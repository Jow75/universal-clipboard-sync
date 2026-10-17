# Universal Clipboard Sync — Windows Authenticode Signing Script
# Publisher: BAZIQHUE (https://baziqhue.co.ke/)
#
# This script creates/loads a dedicated BAZIQHUE Code Signing Certificate,
# signs all Windows executables (portable binary and installer),
# and exports the public certificate for user trust verification.

[CmdletBinding()]
param(
    [string]$DistDir = "dist",
    [switch]$ForceNewCert = $false
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  BAZIQHUE Windows Authenticode Code Signing Tool" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Locate or create BAZIQHUE Code Signing Certificate
Write-Host "[1/4] Checking for existing BAZIQHUE Code Signing Certificate..." -ForegroundColor Yellow

$cert = $null
if (-not $ForceNewCert) {
    $existing = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert -ErrorAction SilentlyContinue |
        Where-Object { $_.Subject -match 'CN=BAZIQHUE' } |
        Sort-Object NotAfter -Descending
    if ($existing) {
        $cert = $existing[0]
        Write-Host "Found existing valid certificate:" -ForegroundColor Green
        Write-Host "  Subject:    $($cert.Subject)"
        Write-Host "  Thumbprint: $($cert.Thumbprint)"
        Write-Host "  Expires:    $($cert.NotAfter)"
    }
}

if (-not $cert) {
    Write-Host "Generating new dedicated BAZIQHUE Code Signing Certificate..." -ForegroundColor Yellow
    $cert = New-SelfSignedCertificate `
        -Subject "CN=BAZIQHUE, O=BAZIQHUE, OU=Software Development, C=KE" `
        -Type CodeSigningCert `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -NotAfter (Get-Date).AddYears(10) `
        -FriendlyName "BAZIQHUE Code Signing" `
        -HashAlgorithm SHA256 `
        -KeyUsage DigitalSignature `
        -KeyLength 2048

    Write-Host "Successfully generated certificate:" -ForegroundColor Green
    Write-Host "  Subject:    $($cert.Subject)"
    Write-Host "  Thumbprint: $($cert.Thumbprint)"
    Write-Host "  Expires:    $($cert.NotAfter)"
}

# 2. Export Public Certificate (.cer)
Write-Host "`n[2/4] Exporting public certificate (.cer)..." -ForegroundColor Yellow
$cerPath = Join-Path $DistDir "BAZIQHUE-CodeSigning.cer"
$websiteAssetsDir = "website\assets"
if (-not (Test-Path $DistDir)) { New-Item -ItemType Directory -Path $DistDir -Force | Out-Null }
if (-not (Test-Path $websiteAssetsDir)) { New-Item -ItemType Directory -Path $websiteAssetsDir -Force | Out-Null }

Export-Certificate -Cert $cert -FilePath $cerPath -Force | Out-Null
Copy-Item -Path $cerPath -Destination (Join-Path $websiteAssetsDir "BAZIQHUE-CodeSigning.cer") -Force
Write-Host "Exported public certificate to:" -ForegroundColor Green
Write-Host "  - $cerPath"
Write-Host "  - $websiteAssetsDir\BAZIQHUE-CodeSigning.cer"

# Also register in CurrentUser\TrustedPublisher on this machine
try {
    Import-Certificate -FilePath $cerPath -CertStoreLocation Cert:\CurrentUser\TrustedPublisher | Out-Null
    Write-Host "Registered in local CurrentUser TrustedPublisher store." -ForegroundColor Green
} catch {
    Write-Warning "Could not register to local TrustedPublisher store: $_"
}

# 3. Identify Binaries to Sign
Write-Host "`n[3/4] Identifying target Windows binaries..." -ForegroundColor Yellow
$targetFiles = @(
    (Join-Path $DistDir "UniversalClipboard.exe"),
    (Join-Path $DistDir "UniversalClipboard-Portable-1.1.0.exe"),
    (Join-Path $DistDir "UniversalClipboard-Setup-1.1.0.exe")
)

$timestampServers = @(
    "http://timestamp.digicert.com",
    "http://timestamp.sectigo.com",
    "http://tsa.starfieldtech.com"
)

# 4. Sign each binary
Write-Host "`n[4/4] Signing binaries with Authenticode (SHA-256)..." -ForegroundColor Yellow
foreach ($filePath in $targetFiles) {
    if (Test-Path $filePath) {
        Write-Host "`nSigning: $filePath" -ForegroundColor Cyan
        $signed = $false

        foreach ($ts in $timestampServers) {
            try {
                Write-Host "  Attempting timestamping via $ts ..."
                $sig = Set-AuthenticodeSignature -FilePath $filePath `
                    -Certificate $cert `
                    -HashAlgorithm SHA256 `
                    -TimestampServer $ts `
                    -ErrorAction Stop

                if ($sig.Status -eq "Valid" -or $sig.Status -eq "UnknownError") {
                    # Status is Valid if trusted, UnknownError if self-signed but signature structure is sound
                    Write-Host "  Signed successfully with timestamp from $ts!" -ForegroundColor Green
                    $signed = $true
                    break
                }
            } catch {
                Write-Host "  Timestamp server $ts failed: $_" -ForegroundColor DarkGray
            }
        }

        if (-not $signed) {
            Write-Host "  Timestamping servers unreachable, signing without external timestamp..." -ForegroundColor Yellow
            $sig = Set-AuthenticodeSignature -FilePath $filePath `
                -Certificate $cert `
                -HashAlgorithm SHA256 `
                -ErrorAction Stop
            Write-Host "  Signed without timestamp (Status: $($sig.Status))" -ForegroundColor Green
        }

        # Verify signature
        $verify = Get-AuthenticodeSignature $filePath
        Write-Host "  Verification Result:" -ForegroundColor Green
        Write-Host "    Status:       $($verify.Status)"
        Write-Host "    Signer:       $($verify.SignerCertificate.Subject)"
        Write-Host "    Thumbprint:   $($verify.SignerCertificate.Thumbprint)"
        if ($verify.TimeStamperCertificate) {
            Write-Host "    TimeStamper:  $($verify.TimeStamperCertificate.Subject)"
        }
    } else {
        Write-Host "File not found (skipped): $filePath" -ForegroundColor DarkGray
    }
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  Code Signing Complete!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

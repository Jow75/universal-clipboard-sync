# Universal Clipboard Sync — Trust BAZIQHUE Publisher Certificate
# Run this script to add the BAZIQHUE Code Signing certificate to your trusted publishers.
# This eliminates "Unknown Publisher" warnings and displays "Verified publisher: BAZIQHUE".

[CmdletBinding()]
param(
    [string]$CertFile = "BAZIQHUE-CodeSigning.cer"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$resolvedCert = if (Test-Path $CertFile) {
    (Resolve-Path $CertFile).Path
} elseif (Test-Path (Join-Path $scriptDir $CertFile)) {
    (Resolve-Path (Join-Path $scriptDir $CertFile)).Path
} elseif (Test-Path (Join-Path $scriptDir "..\dist\$CertFile")) {
    (Resolve-Path (Join-Path $scriptDir "..\dist\$CertFile")).Path
} else {
    $null
}

if (-not $resolvedCert) {
    Write-Error "Could not find $CertFile. Please place $CertFile in the same directory as this script."
    exit 1
}

Write-Host "Importing BAZIQHUE Code Signing Certificate..." -ForegroundColor Cyan
Write-Host "File: $resolvedCert"

try {
    # Import into CurrentUser Root (user trust, does not require Administrator)
    Import-Certificate -FilePath $resolvedCert -CertStoreLocation Cert:\CurrentUser\Root | Out-Null
    Import-Certificate -FilePath $resolvedCert -CertStoreLocation Cert:\CurrentUser\TrustedPublisher | Out-Null

    Write-Host "`nSUCCESS! BAZIQHUE is now a Verified Publisher on this user account." -ForegroundColor Green
    Write-Host "Universal Clipboard Sync will now display 'Verified publisher: BAZIQHUE' on launch." -ForegroundColor Green
} catch {
    Write-Error "Failed to import certificate: $_"
    exit 1
}

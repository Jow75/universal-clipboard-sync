/**
 * Universal Clipboard Sync — Central Website Configuration
 * All public links, download binaries, checksums, brand attribution,
 * and support contact details are defined in this single source of truth.
 */
const SITE_CONFIG = {
  appName: "Universal Clipboard Sync",
  version: "1.1.0",
  releaseTag: "v1.1.0",
  releaseDate: "October 2026",
  license: "MIT License",
  websiteUrl: "https://universal-clipboard.netlify.app/",

  // GitHub & Source Code
  githubRepoUrl: "https://github.com/Jow75/universal-clipboard-sync",
  githubReleaseUrl: "https://github.com/Jow75/universal-clipboard-sync/releases/latest",

  // Direct Verified Release Artifacts
  downloads: {
    windowsInstaller: {
      title: "Windows Installer (Recommended)",
      filename: "UniversalClipboard-Setup-1.1.0.exe",
      url: "https://github.com/Jow75/universal-clipboard-sync/releases/download/v1.1.0/UniversalClipboard-Setup-1.1.0.exe",
      size: "42.3 MB",
      format: ".exe Installer (Digitally Signed)",
      sha256: "c94e680a811d127c069ca3816aed2e55a582147de862c7ba5a8b2cbf72c724fd",
      description: "Standard Windows installer with automatic Desktop & Start Menu shortcuts, system tray integration, and silent uninstaller."
    },
    windowsPortable: {
      title: "Windows Portable Standalone",
      filename: "UniversalClipboard-Portable-1.1.0.exe",
      url: "https://github.com/Jow75/universal-clipboard-sync/releases/download/v1.1.0/UniversalClipboard-Portable-1.1.0.exe",
      size: "45.3 MB",
      format: ".exe Standalone (Digitally Signed)",
      sha256: "0c4a0f2423688b935d3397202b738872f21d6ef497da356f31ef435dfceee41f",
      description: "Self-contained portable single executable. Run instantly without administrative privileges or installation."
    },
    androidApk: {
      title: "Android Application Package",
      filename: "UniversalClipboard-Android-1.1.0.apk",
      url: "https://github.com/Jow75/universal-clipboard-sync/releases/download/v1.1.0/UniversalClipboard-Android-1.1.0.apk",
      size: "5.4 MB",
      format: ".apk (v2 Signed)",
      sha256: "758e660d16f6e52d912f95e31fa05e579660fb76e6b8cdecfd5979bbf21e7d3c",
      compatibility: "Android 8.0 to Android 15 (API 26 to 35)",
      description: "Full-featured Android client with camera QR pairing, Quick Settings tile, and background accessibility synchronization."
    }
  },

  // Brand, Attribution & Parent Website
  parentBrand: {
    name: "BAZIQHUE",
    url: "https://baziqhue.co.ke/",
    attribution: "Built by BAZIQHUE"
  },

  // Support Contact
  support: {
    email: "gmuraguri75@gmail.com",
    label: "Contact Support",
    notes: "For assistance, feature requests, or security disclosures, reach out directly via email or GitHub Issues."
  }
};

// Export for Node/CommonJS environments if used in build scripts
if (typeof module !== "undefined" && module.exports) {
  module.exports = SITE_CONFIG;
}

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
      size: "42.2 MB",
      format: ".exe Installer",
      sha256: "a5df099ffbc718841f2172f21d250d0ba6c8e3c9336e08cc484d75e5f809c5ae",
      description: "Standard Windows installer with automatic Desktop & Start Menu shortcuts, system tray integration, and silent uninstaller."
    },
    windowsPortable: {
      title: "Windows Portable Standalone",
      filename: "UniversalClipboard-Portable-1.1.0.exe",
      url: "https://github.com/Jow75/universal-clipboard-sync/releases/download/v1.1.0/UniversalClipboard-Portable-1.1.0.exe",
      size: "45.2 MB",
      format: ".exe Standalone",
      sha256: "be603914ae5341d291ac7ae2198e9840cd84b319346f86ecd00bdc7e7de547ce",
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

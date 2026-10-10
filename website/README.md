# Universal Clipboard Sync — Product Landing Website & Netlify Guide

This directory contains the official production landing website for **Universal Clipboard Sync**. It is completely self-contained, lightweight, accessible, and ready for one-click deployment to Netlify or any modern static web host.

---

## 📁 Directory Structure

```
website/
├── index.html           # Main product landing page
├── privacy.html         # Detailed data transparency & privacy policy
├── styles.css           # Modern editorial design system & responsive styling
├── site-config.js       # Central configuration (downloads, hashes, support email, brand)
├── app.js               # Client interaction, tabs, hash copy, theme toggle
├── netlify.toml         # Netlify headers, caching, and download redirects
├── favicon.png          # High-resolution website favicon
└── assets/
    ├── icon.png         # Brand icon (512x512)
    └── download_qr.png  # High-contrast official release download QR code
```

---

## 🚀 Local Testing & Preview

To preview the website locally without any dependencies:

```bash
# Using Python built-in HTTP server:
python -m http.server 8080 --directory website

# Open in browser:
# http://localhost:8080
```

---

## 🌐 Netlify Deployment Guide

Universal Clipboard Sync website can be deployed to Netlify via three methods:

### Method 1: Netlify Git Continuous Deployment (Recommended)

1. Log in to your [Netlify Dashboard](https://app.netlify.com/).
2. Click **"Add new site"** → **"Import an existing project"**.
3. Select **GitHub** and authorize the repository `Jow75/universal-clipboard-sync`.
4. Configure Build Settings:
   - **Base directory**: Leave blank (or `website`)
   - **Build command**: *(None required — fully static site)*
   - **Publish directory**: `website`
5. Click **"Deploy site"**. Netlify will automatically build and publish your site with the included security headers and vanity redirects.

### Method 2: Netlify Drop (Instant Drag-and-Drop)

1. Navigate to [Netlify Drop](https://app.netlify.com/drop).
2. Drag and drop the `website/` folder directly onto the upload zone.
3. Your site will be deployed instantly with a live `.netlify.app` URL.

### Method 3: Netlify CLI

```bash
# Install Netlify CLI if not already installed
npm install -g netlify-cli

# Inside the project root:
netlify deploy --dir=website --prod
```

---

## ⚙️ Updating Downloads, Version, or Support Email

All dynamic links and metadata are managed in a single central configuration file:

**[`website/site-config.js`](file:///c:/Users/gmura/Music/Copy%20and%20Paste/website/site-config.js)**

### Updating Release Artifacts & Hashes
When publishing a new release (e.g. `v1.2.0`), update the version string and asset hashes in `SITE_CONFIG`:

```javascript
const SITE_CONFIG = {
  version: "1.2.0",
  releaseTag: "v1.2.0",
  downloads: {
    windowsInstaller: {
      url: "https://github.com/Jow75/universal-clipboard-sync/releases/download/v1.2.0/UniversalClipboard-Setup-1.2.0.exe",
      size: "42.5 MB",
      sha256: "<NEW_SHA256_HASH>"
    },
    ...
  }
};
```

### Updating Customer Support Email
The support contact is defined in `SITE_CONFIG.support`:

```javascript
  support: {
    email: "gmuraguri75@gmail.com",
    label: "Contact Support"
  }
```

### Parent Brand Attribution
Defined in `SITE_CONFIG.parentBrand`:

```javascript
  parentBrand: {
    name: "BAZIQHUE",
    url: "https://baziqhue.co.ke/",
    attribution: "Built by BAZIQHUE"
  }
```

---

## 🔒 Security Headers & Caching Included

The included `netlify.toml` automatically applies:
- `X-Frame-Options: DENY` (Clickjacking mitigation)
- `X-Content-Type-Options: nosniff` (MIME sniffing prevention)
- `Referrer-Policy: strict-origin-when-cross-origin`
- Long-term immutable caching for static assets (`/assets/*`)
- Short vanity redirects for direct downloads (e.g. `/download/windows`, `/download/android`).

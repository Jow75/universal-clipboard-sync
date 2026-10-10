/**
 * Universal Clipboard Sync — Client-side interaction & dynamic config binding
 */

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  bindConfigData();
  initMobileMenu();
  initDownloadTabs();
  initChecksumCopy();
  initHeroSyncDemo();
});

// Theme Management
function initTheme() {
  const themeToggle = document.getElementById("themeToggle");
  const savedTheme = localStorage.getItem("uniclip_theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
      const newTheme = currentTheme === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", newTheme);
      localStorage.setItem("uniclip_theme", newTheme);
    });
  }
}

// Bind Central Configuration into the DOM
function bindConfigData() {
  if (typeof SITE_CONFIG === "undefined") {
    console.error("SITE_CONFIG is missing!");
    return;
  }

  // Version numbers
  document.querySelectorAll("[data-config='version']").forEach(el => {
    el.textContent = `v${SITE_CONFIG.version}`;
  });

  // Release date
  document.querySelectorAll("[data-config='releaseDate']").forEach(el => {
    el.textContent = SITE_CONFIG.releaseDate;
  });

  // Support Email
  document.querySelectorAll("[data-config='supportEmail']").forEach(el => {
    el.textContent = SITE_CONFIG.support.email;
    if (el.tagName === "A") {
      el.href = `mailto:${SITE_CONFIG.support.email}`;
    }
  });

  // Parent website link & attribution
  document.querySelectorAll("[data-config='parentLink']").forEach(el => {
    el.href = SITE_CONFIG.parentBrand.url;
    el.textContent = SITE_CONFIG.parentBrand.attribution;
  });

  // GitHub Links
  document.querySelectorAll("[data-config='githubRepo']").forEach(el => {
    el.href = SITE_CONFIG.githubRepoUrl;
  });
  document.querySelectorAll("[data-config='githubRelease']").forEach(el => {
    el.href = SITE_CONFIG.githubReleaseUrl;
  });

  // Windows Setup Download
  const winSetup = SITE_CONFIG.downloads.windowsInstaller;
  document.querySelectorAll("[data-config='winSetupUrl']").forEach(el => {
    el.href = winSetup.url;
  });
  document.querySelectorAll("[data-config='winSetupSize']").forEach(el => {
    el.textContent = winSetup.size;
  });
  document.querySelectorAll("[data-config='winSetupHash']").forEach(el => {
    el.textContent = winSetup.sha256;
  });

  // Windows Portable Download
  const winPort = SITE_CONFIG.downloads.windowsPortable;
  document.querySelectorAll("[data-config='winPortUrl']").forEach(el => {
    el.href = winPort.url;
  });
  document.querySelectorAll("[data-config='winPortSize']").forEach(el => {
    el.textContent = winPort.size;
  });
  document.querySelectorAll("[data-config='winPortHash']").forEach(el => {
    el.textContent = winPort.sha256;
  });

  // Android APK Download
  const apk = SITE_CONFIG.downloads.androidApk;
  document.querySelectorAll("[data-config='apkUrl']").forEach(el => {
    el.href = apk.url;
  });
  document.querySelectorAll("[data-config='apkSize']").forEach(el => {
    el.textContent = apk.size;
  });
  document.querySelectorAll("[data-config='apkHash']").forEach(el => {
    el.textContent = apk.sha256;
  });
}

// Mobile Menu
function initMobileMenu() {
  const toggle = document.querySelector(".mobile-toggle");
  const navLinks = document.querySelector(".nav-links");

  if (!toggle || !navLinks) return;

  toggle.addEventListener("click", () => {
    navLinks.classList.toggle("active");
    const expanded = toggle.getAttribute("aria-expanded") === "true";
    toggle.setAttribute("aria-expanded", !expanded);
  });

  // Close when clicking a link
  navLinks.querySelectorAll("a").forEach(link => {
    link.addEventListener("click", () => {
      navLinks.classList.remove("active");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
}

// Download Platform Filter Tabs
function initDownloadTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const artifactCards = document.querySelectorAll(".download-artifact-card");

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      tabBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const platform = btn.getAttribute("data-platform");

      artifactCards.forEach(card => {
        const cardPlatform = card.getAttribute("data-platform");
        if (platform === "all" || cardPlatform === platform) {
          card.style.display = "flex";
        } else {
          card.style.display = "none";
        }
      });
    });
  });
}

// One-Click Checksum Copy
function initChecksumCopy() {
  document.querySelectorAll(".btn-copy-hash").forEach(btn => {
    btn.addEventListener("click", () => {
      const hash = btn.getAttribute("data-hash");
      if (!hash) return;

      navigator.clipboard.writeText(hash).then(() => {
        const originalText = btn.textContent;
        btn.textContent = "✓ Copied!";
        btn.style.background = "#008855";
        btn.style.color = "#FFFFFF";

        setTimeout(() => {
          btn.textContent = originalText;
          btn.style.background = "";
          btn.style.color = "";
        }, 2000);
      }).catch(err => {
        console.error("Failed to copy checksum:", err);
      });
    });
  });
}

// Hero Mockup Simulation: Live sync ticker between PC and phones
function initHeroSyncDemo() {
  const syncBar = document.querySelector(".sync-bar");
  if (!syncBar) return;

  const mockEvents = [
    "Laptop→Phone: Copied research link (https://baziqhue.co.ke/...)",
    "Phone→Laptop: Received note from Tecno Spark 10 (120 chars)",
    "Laptop→Phone: Copied Python code snippet (Ctrl+C)",
    "Phone→Laptop: Received address from Samsung Galaxy S24",
    "Laptop→Phone: Copied API token to clipboard (AES-256 sync)",
  ];

  let index = 0;
  setInterval(() => {
    index = (index + 1) % mockEvents.length;
    syncBar.style.opacity = "0.3";
    setTimeout(() => {
      syncBar.textContent = `Sync: ${mockEvents[index]}`;
      syncBar.style.opacity = "1";
    }, 250);
  }, 4000);
}

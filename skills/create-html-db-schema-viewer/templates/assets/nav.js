// =============================================================================
// nav.js — injects a shared top navigation into every page + theme toggle
//
// Each page must contain: <nav id="topnav"></nav>
// Each page <body> must have: data-page="<key>"
// Theme persists in localStorage["erd-theme"] = "light" | "dark"
// =============================================================================

(function () {
  const THEME_KEY = "erd-theme";

  // ── theme: apply ASAP to minimize FOUC ───────────────────────────────────
  function initialTheme() {
    try {
      const stored = localStorage.getItem(THEME_KEY);
      if (stored === "light" || stored === "dark") return stored;
    } catch (_) {}
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) {
      return "light";
    }
    return "dark";
  }
  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
  }
  applyTheme(initialTheme());

  // Sync across tabs.
  window.addEventListener("storage", (e) => {
    if (e.key === THEME_KEY && (e.newValue === "light" || e.newValue === "dark")) {
      applyTheme(e.newValue);
    }
  });

  // ── nav layout ───────────────────────────────────────────────────────────
  const NAV_LINKS = [
    { key: "dashboard", label: "Dashboard", href: "index.html" },
    { key: "erd",       label: "ERD",       href: "erd.html" },
    { key: "tables",    label: "Tables",    href: "tables/index.html" },
    { key: "schema",    label: "DBML",      href: "schema.html" }
  ];

  function prefix() {
    return location.pathname.includes("/tables/") ? "../" : "";
  }
  function activeKey() {
    const body = document.body;
    return (body && body.dataset && body.dataset.page) || "";
  }

  const SUN_SVG = `
    <svg class="icon-sun" width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <circle cx="8" cy="8" r="3.2"/>
      <line x1="8" y1="1.5" x2="8" y2="3"/>
      <line x1="8" y1="13" x2="8" y2="14.5"/>
      <line x1="1.5" y1="8" x2="3" y2="8"/>
      <line x1="13" y1="8" x2="14.5" y2="8"/>
      <line x1="3.4" y1="3.4" x2="4.5" y2="4.5"/>
      <line x1="11.5" y1="11.5" x2="12.6" y2="12.6"/>
      <line x1="3.4" y1="12.6" x2="4.5" y2="11.5"/>
      <line x1="11.5" y1="4.5" x2="12.6" y2="3.4"/>
    </svg>`;
  const MOON_SVG = `
    <svg class="icon-moon" width="14" height="14" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M6.2 1.5A6.5 6.5 0 0 0 9 14.5a6.5 6.5 0 0 0 6.3-4.8 5 5 0 0 1-6.5-6.5A6.5 6.5 0 0 0 6.2 1.5z"/>
    </svg>`;

  function render() {
    const host = document.getElementById("topnav");
    if (!host) return;
    const p = prefix();
    const active = activeKey();

    host.innerHTML = `
      <div class="nav-inner">
        <a class="nav-brand" href="${p}index.html">
          <span class="brand-mark"></span>
          <span class="brand-text">
            <span class="name">ERD VIEWER</span>
            <span class="meta">schema</span>
          </span>
        </a>
        <ul class="nav-links">
          ${NAV_LINKS.map(l => `
            <li>
              <a class="nav-link ${l.key === active ? 'active' : ''}"
                 href="${p}${l.href}">${l.label}</a>
            </li>
          `).join("")}
        </ul>
        <div class="nav-right">
          <div class="nav-stats" id="navStats"></div>
          <button class="theme-toggle" id="themeToggle" type="button"
                  aria-label="Toggle color theme" title="Toggle color theme">
            ${SUN_SVG}${MOON_SVG}
          </button>
        </div>
      </div>
    `;

    const stats = document.getElementById("navStats");
    if (stats && window.SCHEMA) {
      const t = window.SCHEMA.tables ? window.SCHEMA.tables.length : 0;
      const r = window.SCHEMA.relations ? window.SCHEMA.relations.length : 0;
      stats.innerHTML = `
        <span class="stat"><span class="num">${t}</span><span class="lbl">Tables</span></span>
        <span class="stat"><span class="num">${r}</span><span class="lbl">Relations</span></span>
      `;
    }

    const toggle = document.getElementById("themeToggle");
    if (toggle) {
      toggle.addEventListener("click", () => {
        const next = document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light";
        applyTheme(next);
        try { localStorage.setItem(THEME_KEY, next); } catch (_) {}
        // Let listeners (e.g. erd.js PNG export bg color) know.
        window.dispatchEvent(new CustomEvent("theme-changed", { detail: { theme: next } }));
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
  }
})();

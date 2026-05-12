// =============================================================================
// nav.js — injects a shared top navigation into every page
//
// Each page must contain: <nav id="topnav"></nav>
// Each page <body> must have: data-page="<key>"  where <key> is one of NAV keys
// =============================================================================

(function () {
  const NAV_LINKS = [
    { key: "dashboard", label: "Dashboard", href: "index.html" },
    { key: "erd",       label: "ERD",       href: "erd.html" },
    { key: "tables",    label: "Tables",    href: "tables/index.html" },
    { key: "schema",    label: "DBML",      href: "schema.html" }
  ];

  // Pages inside subdirectories (e.g. tables/users.html) need to climb up.
  // We detect depth via location.pathname segments under the output root.
  function prefix() {
    // Heuristic: presence of "/tables/" in the URL means we are one level deep.
    return location.pathname.includes("/tables/") ? "../" : "";
  }

  function activeKey() {
    const body = document.body;
    return (body && body.dataset && body.dataset.page) || "";
  }

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
            <span class="meta">v2</span>
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
        <div class="nav-stats" id="navStats"></div>
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
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
  }
})();

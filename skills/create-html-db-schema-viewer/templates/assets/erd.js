// =============================================================================
// erd.js — Cytoscape + HTML card overlay for erd.html
// Reads window.SCHEMA, renders relationship graph, supports drag/focus/PNG export
// Persists per-table card positions to localStorage.
// =============================================================================

(function () {
  const schema = window.SCHEMA;
  if (!schema || !Array.isArray(schema.tables) || schema.tables.length === 0) {
    document.getElementById("graph-area").innerHTML =
      '<div class="empty">No schema data. Edit schema.dbml and run build.py.</div>';
    return;
  }

  const LS_KEY = "erd-v2:positions";
  const cardsEl = document.getElementById("cards");
  const tableListEl = document.getElementById("tableList");
  const searchInput = document.getElementById("searchInput");

  // ── helpers ──────────────────────────────────────────────────────────────
  function loadPositions() {
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (!raw) return null;
      const obj = JSON.parse(raw);
      return obj && typeof obj === "object" ? obj : null;
    } catch (_) { return null; }
  }
  function savePositions(positions) {
    try { localStorage.setItem(LS_KEY, JSON.stringify(positions)); }
    catch (_) { /* quota or disabled — ignore */ }
  }
  function clearPositions() { try { localStorage.removeItem(LS_KEY); } catch (_) {} }

  function buildTableSpec(t) {
    const lines = [];
    lines.push(`## ${t.name}${t.comment ? ` (${t.comment})` : ''}`);
    lines.push('');
    lines.push('| Key | Column | Type | Comment |');
    lines.push('| --- | --- | --- | --- |');
    t.columns.forEach(c => {
      const key = c.pk ? 'PK' : c.fk ? 'FK' : '';
      const safe = (s) => (s || '').replace(/\|/g, '\\|');
      lines.push(`| ${key} | ${c.name} | ${c.type} | ${safe(c.comment)} |`);
    });
    const out = schema.relations.filter(r => r.from === t.name);
    const inn = schema.relations.filter(r => r.to === t.name);
    if (out.length) {
      lines.push('', '### References');
      out.forEach(r => lines.push(`- \`${r.from_col}\` → \`${r.to}.${r.to_col}\``));
    }
    if (inn.length) {
      lines.push('', '### Referenced by');
      inn.forEach(r => lines.push(`- \`${r.from}.${r.from_col}\` → \`${r.to_col}\``));
    }
    return lines.join('\n');
  }

  async function copyToClipboard(text) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return true;
      }
    } catch (_) {}
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.cssText = 'position:fixed;left:-9999px;top:0;';
    document.body.appendChild(ta);
    ta.focus(); ta.select();
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (_) {}
    document.body.removeChild(ta);
    return ok;
  }

  function detailHref(tableName) {
    return `tables/${encodeURIComponent(tableName)}.html`;
  }

  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, m =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m]));
  }
  function highlightMatch(text, term) {
    const safe = escapeHtml(text);
    if (!term) return safe;
    const t = escapeHtml(term).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return safe.replace(new RegExp(`(${t})`, 'gi'), '<mark>$1</mark>');
  }

  // ── card rendering ───────────────────────────────────────────────────────
  function buildCards() {
    cardsEl.innerHTML = '';
    schema.tables.forEach(t => {
      const card = document.createElement('div');
      card.className = 'erd-card';
      card.dataset.table = t.name;

      const pk = t.columns.filter(c => c.pk);
      const fk = t.columns.filter(c => c.fk && !c.pk);
      const other = t.columns.filter(c => !c.pk && !c.fk);
      const ordered = [...pk, ...fk, ...other];

      const rows = ordered.map(c => {
        const keyClass = c.pk ? 'pk' : c.fk ? 'fk' : '';
        const keyLabel = c.pk ? 'PK' : c.fk ? 'FK' : '';
        const nameClass = c.pk ? 'pk-name' : c.fk ? 'fk-name' : '';
        return `<tr>
          <td class="col-key ${keyClass}">${keyLabel}</td>
          <td class="col-name ${nameClass}">${c.name}</td>
          <td class="col-type">${c.type}</td>
          <td class="col-comment" title="${(c.comment || '').replace(/"/g, '&quot;')}">${c.comment || ''}</td>
        </tr>`;
      }).join('');

      card.innerHTML = `
        <div class="card-header">
          <div class="card-title">${t.name}</div>
          ${t.comment ? `<div class="card-comment">${t.comment}</div>` : ''}
          <div class="card-actions">
            <a class="card-btn" href="${detailHref(t.name)}" title="Open detail page">info</a>
            <button class="card-btn card-copy-btn" type="button" title="Copy table spec">Copy</button>
            <button class="card-btn card-drag-handle" type="button" title="Drag to move" aria-label="Drag to move">
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <line x1="7" y1="5" x2="7" y2="9"/>
                <line x1="5" y1="7" x2="9" y2="7"/>
                <line x1="7" y1="3" x2="7" y2="1"/>
                <polyline points="5 3, 7 1, 9 3"/>
                <line x1="7" y1="11" x2="7" y2="13"/>
                <polyline points="5 11, 7 13, 9 11"/>
                <line x1="3" y1="7" x2="1" y2="7"/>
                <polyline points="3 5, 1 7, 3 9"/>
                <line x1="11" y1="7" x2="13" y2="7"/>
                <polyline points="11 5, 13 7, 11 9"/>
              </svg>
            </button>
          </div>
        </div>
        <table class="card-table"><tbody>${rows}</tbody></table>
      `;

      let downX = 0, downY = 0;
      card.addEventListener('mousedown', e => { downX = e.clientX; downY = e.clientY; });
      card.addEventListener('click', e => {
        if (e.target.closest('.card-actions')) return;
        const dist = Math.hypot(e.clientX - downX, e.clientY - downY);
        if (dist > 4) return;
        if (window.getSelection && window.getSelection().toString().length > 0) return;
        e.stopPropagation();
        focusTable(t.name);
      });

      const copyBtn = card.querySelector('.card-copy-btn');
      copyBtn.addEventListener('click', async e => {
        e.stopPropagation();
        const ok = await copyToClipboard(buildTableSpec(t));
        copyBtn.textContent = ok ? 'Copied' : 'Failed';
        copyBtn.classList.add('copied');
        setTimeout(() => {
          copyBtn.textContent = 'Copy';
          copyBtn.classList.remove('copied');
        }, 1500);
      });

      cardsEl.appendChild(card);
    });
  }

  // ── cytoscape ────────────────────────────────────────────────────────────
  function buildElements() {
    const nodes = schema.tables.map(t => ({ data: { id: t.name } }));
    const edges = schema.relations.map((r, i) => ({
      data: {
        id: `e${i}`,
        source: r.from,
        target: r.to,
        label: `${r.from_col} → ${r.to_col}`,
        relation: r
      },
    }));
    return [...nodes, ...edges];
  }

  const cy = cytoscape({
    container: document.getElementById('cy'),
    elements: buildElements(),
    wheelSensitivity: 0.2,
    autoungrabify: true,
    style: [
      { selector: 'node', style: { 'shape': 'round-rectangle', 'background-opacity': 0, 'border-width': 0, 'label': '' } },
      { selector: 'edge', style: {
          'curve-style': 'bezier',
          'width': 1.6,
          'line-color': '#3a5a8a',
          'target-arrow-color': '#5a7ab0',
          'target-arrow-shape': 'triangle',
          'source-arrow-shape': 'tee',
          'source-arrow-color': '#5a7ab0',
          'arrow-scale': 1.1,
          'label': 'data(label)',
          'font-size': 9,
          'color': '#5a7ab0',
          'text-background-color': '#0a1020',
          'text-background-opacity': 0.85,
          'text-background-padding': 2,
          'text-rotation': 'autorotate',
          'transition-property': 'opacity, line-color, target-arrow-color, source-arrow-color, width',
          'transition-duration': '0.2s',
      } },
      { selector: 'edge.faded',     style: { 'opacity': 0.1 } },
      { selector: 'edge.highlight', style: { 'line-color': '#e94560', 'target-arrow-color': '#e94560', 'source-arrow-color': '#e94560', 'width': 2.4 } },
    ],
  });

  // ── sync cards <-> cytoscape ─────────────────────────────────────────────
  function syncNodeSizesFromCards() {
    schema.tables.forEach(t => {
      const card = cardsEl.querySelector(`[data-table="${CSS.escape(t.name)}"]`);
      if (!card) return;
      cy.getElementById(t.name).style({
        width: card.offsetWidth || 280,
        height: card.offsetHeight || 120
      });
    });
  }
  function syncCardPositions() {
    schema.tables.forEach(t => {
      const card = cardsEl.querySelector(`[data-table="${CSS.escape(t.name)}"]`);
      if (!card) return;
      const pos = cy.getElementById(t.name).position();
      const w = card.offsetWidth, h = card.offsetHeight;
      card.style.left = (pos.x - w / 2) + 'px';
      card.style.top  = (pos.y - h / 2) + 'px';
    });
  }
  function syncOverlayTransform() {
    const pan = cy.pan(), zoom = cy.zoom();
    cardsEl.style.transform = `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`;
  }
  cy.on('pan zoom resize', syncOverlayTransform);

  function applyStoredPositions() {
    const stored = loadPositions();
    if (!stored) return false;
    let appliedCount = 0;
    schema.tables.forEach(t => {
      const p = stored[t.name];
      if (p && typeof p.x === 'number' && typeof p.y === 'number') {
        cy.getElementById(t.name).position(p);
        appliedCount++;
      }
    });
    return appliedCount > 0;
  }

  function runLayout() {
    return new Promise(resolve => {
      const layout = cy.layout({
        name: 'dagre',
        rankDir: 'LR',
        nodeSep: 60,
        rankSep: 180,
        edgeSep: 30,
      });
      layout.one('layoutstop', () => {
        syncCardPositions();
        syncOverlayTransform();
        resolve();
      });
      layout.run();
    });
  }

  // ── sidebar list + search ────────────────────────────────────────────────
  function buildTableList() {
    const filter = searchInput.value.toLowerCase().trim();
    tableListEl.innerHTML = '';
    let visibleSet = null;
    if (filter) {
      visibleSet = new Set();
      schema.tables.forEach(t => {
        const matchesName = t.name.toLowerCase().includes(filter);
        const matchesComment = (t.comment || '').toLowerCase().includes(filter);
        const matchesColumn = t.columns.some(c =>
          c.name.toLowerCase().includes(filter) ||
          (c.comment || '').toLowerCase().includes(filter)
        );
        if (matchesName || matchesComment || matchesColumn) visibleSet.add(t.name);
      });
    }
    let visible = 0;
    schema.tables.forEach(t => {
      if (visibleSet && !visibleSet.has(t.name)) return;
      visible++;
      const div = document.createElement('div');
      div.className = 'tbl-item';
      div.dataset.table = t.name;
      div.innerHTML = `
        <div class="tbl-name">${highlightMatch(t.name, filter)}</div>
        ${t.comment ? `<div class="tbl-comment">${highlightMatch(t.comment, filter)}</div>` : ''}
      `;
      div.addEventListener('click', () => focusTable(t.name));
      tableListEl.appendChild(div);
    });

    const countEl = document.getElementById('tablesCount');
    if (countEl) {
      const total = schema.tables.length;
      countEl.textContent = visible === total ? `${total}` : `${visible}/${total}`;
    }

    schema.tables.forEach(t => {
      const card = cardsEl.querySelector(`[data-table="${CSS.escape(t.name)}"]`);
      if (!card) return;
      if (visibleSet && !visibleSet.has(t.name)) card.classList.add('hidden');
      else card.classList.remove('hidden');
    });
  }
  searchInput.addEventListener('input', buildTableList);

  function setActiveListItem(tableName) {
    tableListEl.querySelectorAll('.tbl-item').forEach(el => {
      el.classList.toggle('active', el.dataset.table === tableName);
    });
  }

  // ── focus mode ───────────────────────────────────────────────────────────
  let focusMode = true;

  function focusTable(tableName) {
    const node = cy.getElementById(tableName);
    if (!node || node.empty()) return;

    cy.elements().removeClass('faded highlight');
    cardsEl.querySelectorAll('.erd-card').forEach(c => c.classList.remove('selected', 'neighbor', 'faded'));

    const card = cardsEl.querySelector(`[data-table="${CSS.escape(tableName)}"]`);
    if (card) card.classList.add('selected');

    if (focusMode) {
      const neighborhood = node.closedNeighborhood();
      const neighborIds = new Set(neighborhood.nodes().map(n => n.id()));
      cy.edges().forEach(e => {
        if (neighborhood.edges().has(e)) e.addClass('highlight');
        else e.addClass('faded');
      });
      schema.tables.forEach(t => {
        const c = cardsEl.querySelector(`[data-table="${CSS.escape(t.name)}"]`);
        if (!c) return;
        if (t.name === tableName) return;
        if (neighborIds.has(t.name)) c.classList.add('neighbor');
        else c.classList.add('faded');
      });
    }

    setActiveListItem(tableName);
    history.replaceState(null, '', `#table=${encodeURIComponent(tableName)}`);

    // Pan the focused node to the center of the viewport (keep current zoom).
    cy.animate({ center: { eles: node }, duration: 300 });
  }

  function clearFocus() {
    cy.elements().removeClass('faded highlight');
    cardsEl.querySelectorAll('.erd-card').forEach(c => c.classList.remove('selected', 'neighbor', 'faded'));
    setActiveListItem(null);
    history.replaceState(null, '', location.pathname);
  }

  cy.on('tap', evt => { if (evt.target === cy) clearFocus(); });

  // ── wheel zoom over cards (forward to cytoscape) ─────────────────────────
  // #cards has pointer-events:none, but .erd-card children have pointer-events:auto,
  // so wheel events fire on the card and stop before reaching #cy. We listen on
  // cardsEl and zoom cy manually around the cursor's rendered position.
  cardsEl.addEventListener('wheel', (e) => {
    e.preventDefault();
    const rect = cy.container().getBoundingClientRect();
    const sens = 0.2;
    const factor = Math.pow(10, -e.deltaY * sens / 1000);
    const newZoom = cy.zoom() * factor;
    cy.zoom({
      level: newZoom,
      renderedPosition: {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      }
    });
  }, { passive: false });

  // ── drag (handle button only) ────────────────────────────────────────────
  let dragState = null;
  cardsEl.addEventListener('mousedown', e => {
    if (e.button !== 0) return;
    const handle = e.target.closest('.card-drag-handle');
    if (!handle) return;
    const card = handle.closest('.erd-card');
    if (!card) return;

    const tableName = card.dataset.table;
    const node = cy.getElementById(tableName);
    if (!node || node.empty()) return;
    const pos = node.position();

    e.preventDefault();
    e.stopPropagation();
    dragState = {
      tableName, card,
      startClientX: e.clientX, startClientY: e.clientY,
      startNodeX: pos.x, startNodeY: pos.y,
    };
    card.classList.add('dragging');
  });
  document.addEventListener('mousemove', e => {
    if (!dragState) return;
    const zoom = cy.zoom();
    const dx = (e.clientX - dragState.startClientX) / zoom;
    const dy = (e.clientY - dragState.startClientY) / zoom;
    const nx = dragState.startNodeX + dx;
    const ny = dragState.startNodeY + dy;
    cy.getElementById(dragState.tableName).position({ x: nx, y: ny });
    const w = dragState.card.offsetWidth, h = dragState.card.offsetHeight;
    dragState.card.style.left = (nx - w / 2) + 'px';
    dragState.card.style.top  = (ny - h / 2) + 'px';
  });
  document.addEventListener('mouseup', () => {
    if (!dragState) return;
    dragState.card.classList.remove('dragging');
    // Persist all current positions
    const positions = {};
    schema.tables.forEach(t => {
      const p = cy.getElementById(t.name).position();
      positions[t.name] = { x: p.x, y: p.y };
    });
    savePositions(positions);
    dragState = null;
  });

  // ── toolbar ──────────────────────────────────────────────────────────────
  document.getElementById('btnFit').addEventListener('click',
    () => cy.animate({ fit: { padding: 60 }, duration: 300 }));

  document.getElementById('btnLayout').addEventListener('click', async () => {
    await runLayout();
    cy.animate({ fit: { padding: 60 }, duration: 300 });
  });

  const btnFocus = document.getElementById('btnFocus');
  btnFocus.addEventListener('click', () => {
    focusMode = !focusMode;
    btnFocus.textContent = `Focus: ${focusMode ? 'ON' : 'OFF'}`;
    btnFocus.classList.toggle('active', focusMode);
    if (!focusMode) {
      cy.elements().removeClass('faded highlight');
      cardsEl.querySelectorAll('.erd-card').forEach(c => c.classList.remove('neighbor', 'faded'));
    }
  });

  document.getElementById('btnResetLayout').addEventListener('click', async () => {
    clearPositions();
    await runLayout();
    cy.animate({ fit: { padding: 60 }, duration: 300 });
  });

  // ── PNG export ───────────────────────────────────────────────────────────
  async function exportPng() {
    const btn = document.getElementById('btnExport');
    const originalLabel = btn.textContent;
    btn.textContent = 'Exporting…';
    btn.disabled = true;

    const graphArea = document.getElementById('graph-area');
    const savedStyle = graphArea.style.cssText;
    const hadFaded = cy.elements('.faded, .highlight').length > 0;
    if (hadFaded) {
      cy.elements().removeClass('faded highlight');
      cardsEl.querySelectorAll('.erd-card').forEach(c => c.classList.remove('faded', 'neighbor'));
    }

    try {
      const bb = cy.elements().boundingBox();
      const padding = 80;
      const exportW = Math.max(800, Math.ceil(bb.w + padding * 2));
      const exportH = Math.max(600, Math.ceil(bb.h + padding * 2));

      Object.assign(graphArea.style, {
        position: 'fixed', left: '0', top: '0',
        width: exportW + 'px', height: exportH + 'px', zIndex: '9999',
      });
      cy.resize();
      cy.fit(undefined, padding);
      syncCardPositions();
      syncOverlayTransform();

      await new Promise(r => setTimeout(r, 250));
      const canvas = await html2canvas(graphArea, {
        backgroundColor: '#0a1020',
        scale: 2,
        logging: false,
        useCORS: false,
        width: exportW,
        height: exportH,
      });

      const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-');
      const link = document.createElement('a');
      link.download = `erd-${stamp}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (err) {
      console.error('Export failed:', err);
      alert('PNG export 실패: ' + (err && err.message ? err.message : err));
    } finally {
      graphArea.style.cssText = savedStyle;
      cy.resize();
      cy.fit(undefined, 60);
      syncCardPositions();
      syncOverlayTransform();
      btn.textContent = originalLabel;
      btn.disabled = false;
    }
  }
  document.getElementById('btnExport').addEventListener('click', exportPng);

  function applyHash() {
    const m = location.hash.match(/table=([^&]+)/);
    if (m) focusTable(decodeURIComponent(m[1]));
  }
  window.addEventListener('hashchange', applyHash);

  // ── boot ─────────────────────────────────────────────────────────────────
  async function boot() {
    buildCards();
    syncNodeSizesFromCards();
    buildTableList();
    const restored = applyStoredPositions();
    if (restored) {
      syncCardPositions();
      syncOverlayTransform();
      cy.fit(undefined, 60);
    } else {
      await runLayout();
      cy.fit(undefined, 60);
    }
    syncOverlayTransform();
    applyHash();
  }
  boot();
})();

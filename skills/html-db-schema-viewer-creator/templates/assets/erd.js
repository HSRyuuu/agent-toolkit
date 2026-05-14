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
        const fkAttrs = c.fk
          ? ` class="fk-row" data-fk-from-col="${c.name}" data-fk-target-table="${c.fk.table}" data-fk-target-col="${c.fk.column}"`
          : '';
        return `<tr${fkAttrs}>
          <td class="col-key ${keyClass}">${keyLabel}</td>
          <td class="col-name ${nameClass}">${c.name}</td>
          <td class="col-type">${c.type}</td>
          <td class="col-comment"><div title="${(c.comment || '').replace(/"/g, '&quot;')}">${c.comment || ''}</div></td>
        </tr>`;
      }).join('');

      card.innerHTML = `
        <div class="card-header">
          <div class="card-title">${t.name}</div>
          ${t.comment ? `<div class="card-comment" title="${t.comment.replace(/"/g, '&quot;')}">${t.comment}</div>` : ''}
          <div class="card-actions">
            <a class="card-btn" href="${detailHref(t.name)}" title="Open detail page">info</a>
            <button class="card-btn card-copy-btn" type="button" title="Copy table spec">copy</button>
          </div>
        </div>
        <table class="card-table"><tbody>${rows}</tbody></table>
      `;

      let downX = 0, downY = 0;
      card.addEventListener('mousedown', e => { downX = e.clientX; downY = e.clientY; });
      card.addEventListener('click', e => {
        if (e.target.closest('.card-actions')) return;
        if (e.target.closest('.fk-row')) return;
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
        copyBtn.textContent = ok ? 'copied' : 'failed';
        copyBtn.classList.add('copied');
        setTimeout(() => {
          copyBtn.textContent = 'copy';
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

  function readVar(name, fallback) {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }
  function buildCyStyle() {
    const edgeLine    = readVar('--edge-line',     '#3a5a8a');
    const edgeArrow   = readVar('--edge-arrow',    '#5a7ab0');
    const edgeLabel   = readVar('--edge-label',    '#8b949e');
    const edgeLabelBg = readVar('--edge-label-bg', '#0d1117');
    const accent      = readVar('--accent',        '#e94560');
    return [
      { selector: 'node', style: { 'shape': 'round-rectangle', 'background-opacity': 0, 'border-width': 0, 'label': '' } },
      { selector: 'edge', style: {
          'curve-style': 'bezier',
          'width': 1.6,
          'line-color': edgeLine,
          'target-arrow-color': edgeArrow,
          'target-arrow-shape': 'triangle',
          'source-arrow-shape': 'tee',
          'source-arrow-color': edgeArrow,
          'arrow-scale': 1.1,
          'label': 'data(label)',
          'font-size': 9,
          'color': edgeLabel,
          'text-background-color': edgeLabelBg,
          'text-background-opacity': 0.85,
          'text-background-padding': 2,
          'text-rotation': 'autorotate',
          'transition-property': 'opacity, line-color, target-arrow-color, source-arrow-color, width',
          'transition-duration': '0.2s',
      } },
      { selector: 'edge.faded',     style: { 'opacity': 0.1 } },
      { selector: 'edge.highlight', style: { 'line-color': accent, 'target-arrow-color': accent, 'source-arrow-color': accent, 'width': 2.4 } },
    ];
  }

  const cy = cytoscape({
    container: document.getElementById('cy'),
    elements: buildElements(),
    wheelSensitivity: 0.2,
    autoungrabify: true,
    style: buildCyStyle(),
  });

  // Re-apply cytoscape stylesheet when theme changes (nav.js dispatches it).
  window.addEventListener('theme-changed', () => {
    cy.style().fromJson(buildCyStyle()).update();
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

  // dagre LR when there are relations (typical ERD).
  // grid when there are 0 relations (legacy DBs without FK constraints) —
  // dagre would stack every node into a single rank, producing one tall
  // vertical column. grid spreads the cards across the viewport instead.
  function runLayout() {
    return new Promise(resolve => {
      syncNodeSizesFromCards();
      const hasEdges = Array.isArray(schema.relations) && schema.relations.length > 0;
      const options = hasEdges
        ? {
            name: 'dagre',
            rankDir: 'LR',
            nodeSep: 40,
            rankSep: 120,
            edgeSep: 20,
          }
        : {
            name: 'grid',
            // wider-than-tall grid (~1.6 aspect) so a 350-table schema spreads
            // horizontally across the typical screen.
            cols: Math.max(1, Math.ceil(Math.sqrt(schema.tables.length * 1.6))),
            avoidOverlap: true,
            avoidOverlapPadding: 30,
            fit: true,
            padding: 40,
          };
      const layout = cy.layout(options);
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

  // Highlight a single FK edge (clicked from an FK row inside a card).
  function highlightSingleRelation(fromTable, fromCol, toTable, toCol) {
    cy.elements().removeClass('faded highlight');
    cardsEl.querySelectorAll('.erd-card').forEach(c =>
      c.classList.remove('selected', 'neighbor', 'faded'));

    const idx = schema.relations.findIndex(r =>
      r.from === fromTable && r.from_col === fromCol &&
      r.to === toTable && r.to_col === toCol);
    if (idx < 0) return;

    const edgeId = `e${idx}`;
    cy.edges().forEach(e => {
      if (e.id() === edgeId) e.addClass('highlight');
      else e.addClass('faded');
    });

    schema.tables.forEach(t => {
      const c = cardsEl.querySelector(`[data-table="${CSS.escape(t.name)}"]`);
      if (!c) return;
      if (t.name === fromTable) c.classList.add('selected');
      else if (t.name === toTable) c.classList.add('neighbor');
      else c.classList.add('faded');
    });

    setActiveListItem(fromTable);
  }

  // Delegated click on FK rows inside cards.
  cardsEl.addEventListener('click', e => {
    const fkRow = e.target.closest('.fk-row');
    if (!fkRow) return;
    if (window.getSelection && window.getSelection().toString().length > 0) return;
    const card = fkRow.closest('.erd-card');
    if (!card) return;
    e.stopPropagation();
    highlightSingleRelation(
      card.dataset.table,
      fkRow.dataset.fkFromCol,
      fkRow.dataset.fkTargetTable,
      fkRow.dataset.fkTargetCol
    );
  });

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

  // ── drag (card header, except the title area which is select-to-copy) ────
  let dragState = null;
  cardsEl.addEventListener('mousedown', e => {
    if (e.button !== 0) return;
    if (e.target.closest('.card-actions')) return;
    // Table-name area is reserved for text selection (drag-to-copy the name)
    if (e.target.closest('.card-title')) return;
    const header = e.target.closest('.card-header');
    if (!header) return;
    const card = header.closest('.erd-card');
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

  document.getElementById('btnAutoLayout').addEventListener('click', async () => {
    clearPositions();
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
    // Hide card action buttons (info / copy / drag handle) in the exported image.
    document.body.classList.add('exporting');

    try {
      const bb = cy.elements().boundingBox();
      const padding = 80;
      const exportW = Math.max(800, Math.ceil(bb.w + padding * 2));
      const exportH = Math.max(600, Math.ceil(bb.h + padding * 2));

      // Browser canvas limits: most engines cap a single canvas at 16,384px in
      // either dimension and ~268M total pixels (Safari stricter). With many
      // tables, scale=2 easily blows past this and html2canvas silently returns
      // a blank/black image. Pick the largest scale that fits both caps.
      const MAX_CANVAS_DIM = 16384;
      const MAX_CANVAS_AREA = 16384 * 16384;
      const maxDim = Math.max(exportW, exportH);
      const area = exportW * exportH;
      let scale = Math.min(
        2,
        MAX_CANVAS_DIM / maxDim,
        Math.sqrt(MAX_CANVAS_AREA / area)
      );
      if (scale < 0.5) {
        throw new Error(
          `ERD 영역이 너무 큽니다 (${exportW}×${exportH}px). ` +
          `Auto Layout으로 카드 위치를 압축하거나, 검색으로 테이블을 부분 집합으로 좁힌 뒤 다시 시도하세요.`
        );
      }
      if (scale < 2) {
        console.info(`[erd export] downscaled to ${scale.toFixed(2)}x to fit canvas limits`);
      }

      Object.assign(graphArea.style, {
        position: 'fixed', left: '0', top: '0',
        width: exportW + 'px', height: exportH + 'px', zIndex: '9999',
      });
      cy.resize();
      cy.fit(undefined, padding);
      syncCardPositions();
      syncOverlayTransform();

      await new Promise(r => setTimeout(r, 250));
      const bgColor = getComputedStyle(document.documentElement)
        .getPropertyValue('--bg').trim() || '#0d1117';
      const canvas = await html2canvas(graphArea, {
        backgroundColor: bgColor,
        scale,
        logging: false,
        useCORS: false,
        width: exportW,
        height: exportH,
      });

      if (!canvas || canvas.width === 0 || canvas.height === 0) {
        throw new Error('빈 캔버스가 생성되었습니다. 스키마가 너무 크거나 브라우저 캔버스 한계를 초과했습니다.');
      }

      const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-');
      const link = document.createElement('a');
      link.download = `erd-${stamp}.png`;
      link.href = canvas.toDataURL('image/png');
      if (link.href === 'data:,' || link.href.length < 100) {
        throw new Error('PNG 인코딩 결과가 비어 있습니다. 브라우저 캔버스 한계를 초과했을 가능성이 큽니다.');
      }
      link.click();
    } catch (err) {
      console.error('Export failed:', err);
      alert('PNG export 실패: ' + (err && err.message ? err.message : err));
    } finally {
      document.body.classList.remove('exporting');
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

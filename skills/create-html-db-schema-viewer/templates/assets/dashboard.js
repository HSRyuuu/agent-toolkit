// =============================================================================
// dashboard.js — KPIs and top-N connected tables for index.html
// =============================================================================

(function () {
  const s = window.SCHEMA || { tables: [], relations: [], enums: [] };
  const tables = s.tables || [];
  const relations = s.relations || [];
  const enums = s.enums || [];

  // ── KPIs ─────────────────────────────────────────────────────────────────
  const indexCount = tables.reduce((acc, t) => acc + (t.indexes ? t.indexes.length : 0), 0);
  const columnCount = tables.reduce((acc, t) => acc + (t.columns ? t.columns.length : 0), 0);

  const kpiGrid = document.getElementById('kpiGrid');
  const kpis = [
    { num: tables.length,   lbl: 'Tables' },
    { num: relations.length, lbl: 'Relations' },
    { num: indexCount,      lbl: 'Indexes' },
    { num: columnCount,     lbl: 'Columns' },
    { num: enums.length,    lbl: 'Enums' },
  ];
  kpiGrid.innerHTML = kpis.map(k => `
    <div class="kpi">
      <div class="num">${k.num}</div>
      <div class="lbl">${k.lbl}</div>
    </div>
  `).join('');

  document.getElementById('metaSummary').textContent =
    `${tables.length} tables · ${relations.length} relations`;

  // ── Top connected tables ─────────────────────────────────────────────────
  const inDeg = new Map();
  const outDeg = new Map();
  tables.forEach(t => { inDeg.set(t.name, 0); outDeg.set(t.name, 0); });
  relations.forEach(r => {
    outDeg.set(r.from, (outDeg.get(r.from) || 0) + 1);
    inDeg.set(r.to,    (inDeg.get(r.to) || 0) + 1);
  });

  const rows = tables
    .map(t => ({
      name: t.name,
      comment: t.comment || '',
      in: inDeg.get(t.name) || 0,
      out: outDeg.get(t.name) || 0,
      total: (inDeg.get(t.name) || 0) + (outDeg.get(t.name) || 0),
    }))
    .sort((a, b) => b.total - a.total)
    .slice(0, 10);

  const tbody = document.querySelector('#topConnected tbody');
  if (rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty">No tables yet. Edit schema.dbml.</td></tr>`;
  } else {
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td class="col-name"><a href="tables/${encodeURIComponent(r.name)}.html">${r.name}</a></td>
        <td class="col-comment">${r.comment}</td>
        <td class="col-flag">${r.in}</td>
        <td class="col-flag">${r.out}</td>
        <td class="col-flag">${r.total}</td>
      </tr>
    `).join('');
  }
})();

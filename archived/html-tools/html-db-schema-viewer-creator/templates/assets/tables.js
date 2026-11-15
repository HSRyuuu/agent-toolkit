// =============================================================================
// tables.js — sortable / filterable table list for tables/index.html
// =============================================================================

(function () {
  const s = window.SCHEMA || { tables: [], relations: [] };
  const tables = s.tables || [];
  const relations = s.relations || [];

  const inDeg = new Map();
  const outDeg = new Map();
  tables.forEach(t => { inDeg.set(t.name, 0); outDeg.set(t.name, 0); });
  relations.forEach(r => {
    outDeg.set(r.from, (outDeg.get(r.from) || 0) + 1);
    inDeg.set(r.to,    (inDeg.get(r.to) || 0) + 1);
  });

  const rows = tables.map(t => ({
    name: t.name,
    comment: t.comment || '',
    columns: t.columns ? t.columns.length : 0,
    indexes: t.indexes ? t.indexes.length : 0,
    incoming: inDeg.get(t.name) || 0,
    outgoing: outDeg.get(t.name) || 0,
    _columnNames: (t.columns || []).map(c => c.name.toLowerCase()).join(' ')
  }));

  let sortKey = 'name';
  let sortDir = 'asc';

  function compare(a, b) {
    const av = a[sortKey], bv = b[sortKey];
    if (typeof av === 'number' && typeof bv === 'number') {
      return sortDir === 'asc' ? av - bv : bv - av;
    }
    const as = String(av || '').toLowerCase();
    const bs = String(bv || '').toLowerCase();
    if (as < bs) return sortDir === 'asc' ? -1 : 1;
    if (as > bs) return sortDir === 'asc' ? 1 : -1;
    return 0;
  }

  const tbody = document.querySelector('#tablesTable tbody');
  const searchInput = document.getElementById('searchInput');
  const metaSummary = document.getElementById('metaSummary');

  function render() {
    const filter = searchInput.value.toLowerCase().trim();
    const filtered = filter
      ? rows.filter(r =>
          r.name.toLowerCase().includes(filter) ||
          r.comment.toLowerCase().includes(filter) ||
          r._columnNames.includes(filter))
      : rows.slice();
    filtered.sort(compare);

    metaSummary.textContent = filter
      ? `${filtered.length} / ${rows.length} matched`
      : `${rows.length} total`;

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="empty">No tables match.</td></tr>`;
      return;
    }
    tbody.innerHTML = filtered.map(r => `
      <tr>
        <td class="col-name"><a href="${encodeURIComponent(r.name)}.html">${r.name}</a></td>
        <td class="col-comment">${r.comment}</td>
        <td class="col-flag">${r.columns}</td>
        <td class="col-flag">${r.indexes}</td>
        <td class="col-flag">${r.incoming}</td>
        <td class="col-flag">${r.outgoing}</td>
      </tr>
    `).join('');
  }

  function updateSortIndicators() {
    document.querySelectorAll('#tablesTable th.sortable').forEach(th => {
      th.classList.remove('sort-asc', 'sort-desc');
      if (th.dataset.sort === sortKey) {
        th.classList.add(sortDir === 'asc' ? 'sort-asc' : 'sort-desc');
      }
    });
  }

  document.querySelectorAll('#tablesTable th.sortable').forEach(th => {
    th.addEventListener('click', () => {
      const k = th.dataset.sort;
      if (sortKey === k) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
      else { sortKey = k; sortDir = 'asc'; }
      updateSortIndicators();
      render();
    });
  });

  searchInput.addEventListener('input', render);

  updateSortIndicators();
  render();
})();

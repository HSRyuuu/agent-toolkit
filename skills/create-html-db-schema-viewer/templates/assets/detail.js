// =============================================================================
// detail.js — renders one table detail page (tables/<name>.html)
// The body carries data-table="<name>"; this script populates every section.
// =============================================================================

(function () {
  const tableName = document.body.dataset.table;
  if (!tableName) return;

  const s = window.SCHEMA || { tables: [], relations: [] };
  const t = (s.tables || []).find(x => x.name === tableName);

  if (!t) {
    document.querySelector('main.page').innerHTML = `
      <div class="empty">Table <code>${tableName}</code> not found in schema.</div>
    `;
    return;
  }

  // ── header ───────────────────────────────────────────────────────────────
  document.title = `${t.name} — Schema Explorer`;
  document.getElementById('tableName').textContent = t.name;
  document.getElementById('crumbName').textContent = t.name;
  document.getElementById('tableComment').textContent = t.comment || '';

  // ── columns ──────────────────────────────────────────────────────────────
  const cols = t.columns || [];
  document.getElementById('columnsCount').textContent = `(${cols.length})`;
  const colTbody = document.querySelector('#columnsTable tbody');
  colTbody.innerHTML = cols.map(c => {
    const isFk = !!c.fk;
    const keyClass = c.pk ? 'pk' : isFk ? 'fk' : c.uk ? 'uk' : '';
    const keyLabel = c.pk ? 'PK' : isFk ? 'FK' : c.uk ? 'UK' : '';
    const nameClass = c.pk ? 'pk-name' : isFk ? 'fk-name' : '';
    const fkLink = isFk
      ? ` → <a href="${encodeURIComponent(c.fk.table)}.html">${c.fk.table}.${c.fk.column}</a>`
      : '';
    return `
      <tr>
        <td class="col-key ${keyClass}">${keyLabel}</td>
        <td class="col-name ${nameClass}">${c.name}${fkLink}</td>
        <td class="col-type">${c.type || ''}</td>
        <td class="col-flag">${c.nullable === false ? 'NO' : 'YES'}</td>
        <td class="col-flag">${c.default == null ? '' : escapeHtml(String(c.default))}</td>
        <td class="col-comment">${escapeHtml(c.comment || '')}</td>
      </tr>
    `;
  }).join('');

  // ── indexes ──────────────────────────────────────────────────────────────
  const idxs = t.indexes || [];
  document.getElementById('indexesCount').textContent = `(${idxs.length})`;
  if (idxs.length === 0) {
    document.getElementById('indexesSection').innerHTML =
      '<div class="empty" style="padding:20px;">No indexes.</div>';
  } else {
    const idxTbody = document.querySelector('#indexesTable tbody');
    idxTbody.innerHTML = idxs.map(ix => `
      <tr>
        <td class="col-name">${ix.name || '(unnamed)'}</td>
        <td class="col-type">(${(ix.columns || []).join(', ')})</td>
        <td class="col-flag">${ix.unique ? 'UNIQUE' : ''}</td>
      </tr>
    `).join('');
  }

  // ── relations ────────────────────────────────────────────────────────────
  const rels = s.relations || [];
  const outgoing = rels.filter(r => r.from === t.name);
  const incoming = rels.filter(r => r.to === t.name);

  document.getElementById('outgoing').innerHTML = outgoing.length === 0
    ? '<div class="empty" style="padding:8px 0;">None</div>'
    : outgoing.map(r => `
        <div style="font-family:Consolas,monospace;font-size:12px;color:#c8d4ec;padding:4px 0;">
          <span style="color:#4a9eff;">${r.from_col}</span>
          <span style="color:#5a6e8c;">→</span>
          <a href="${encodeURIComponent(r.to)}.html">${r.to}.${r.to_col}</a>
        </div>
      `).join('');

  document.getElementById('incoming').innerHTML = incoming.length === 0
    ? '<div class="empty" style="padding:8px 0;">None</div>'
    : incoming.map(r => `
        <div style="font-family:Consolas,monospace;font-size:12px;color:#c8d4ec;padding:4px 0;">
          <a href="${encodeURIComponent(r.from)}.html">${r.from}.${r.from_col}</a>
          <span style="color:#5a6e8c;">→</span>
          <span style="color:#4a9eff;">${r.to_col}</span>
        </div>
      `).join('');

  // ── copy spec ────────────────────────────────────────────────────────────
  const btnCopy = document.getElementById('btnCopySpec');
  btnCopy.addEventListener('click', async () => {
    const md = buildSpec(t, outgoing, incoming);
    const ok = await copy(md);
    btnCopy.textContent = ok ? 'Copied' : 'Failed';
    btnCopy.classList.add('copied');
    setTimeout(() => {
      btnCopy.textContent = 'Copy Spec (markdown)';
      btnCopy.classList.remove('copied');
    }, 1500);
  });

  // ── helpers ──────────────────────────────────────────────────────────────
  function buildSpec(t, out, inn) {
    const lines = [];
    lines.push(`## ${t.name}${t.comment ? ` (${t.comment})` : ''}`);
    lines.push('');
    lines.push('| Key | Column | Type | Null | Default | Comment |');
    lines.push('| --- | --- | --- | --- | --- | --- |');
    (t.columns || []).forEach(c => {
      const key = c.pk ? 'PK' : c.fk ? 'FK' : c.uk ? 'UK' : '';
      const safe = (x) => String(x == null ? '' : x).replace(/\|/g, '\\|');
      lines.push(`| ${key} | ${c.name} | ${c.type || ''} | ${c.nullable === false ? 'NO' : 'YES'} | ${safe(c.default)} | ${safe(c.comment)} |`);
    });
    if ((t.indexes || []).length) {
      lines.push('', '### Indexes');
      t.indexes.forEach(ix => {
        lines.push(`- ${ix.name || '(unnamed)'} (${(ix.columns || []).join(', ')})${ix.unique ? ' [UNIQUE]' : ''}`);
      });
    }
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

  async function copy(text) {
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

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, m => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[m]));
  }
})();

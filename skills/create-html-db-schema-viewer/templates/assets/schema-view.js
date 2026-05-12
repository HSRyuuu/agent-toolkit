// =============================================================================
// schema-view.js — render schema.dbml source on schema.html
// =============================================================================

(function () {
  const s = window.SCHEMA || {};
  const dbml = s.source_dbml || '';
  const pre = document.getElementById('dbmlSource');
  const meta = document.getElementById('metaSummary');

  if (!dbml.trim()) {
    pre.textContent = '// schema.dbml is empty. Run build.py or generate window.SCHEMA.source_dbml.';
    meta.textContent = '(empty)';
  } else {
    pre.textContent = dbml;
    const lines = dbml.split('\n').length;
    const bytes = new Blob([dbml]).size;
    meta.textContent = `${lines} lines · ${bytes} bytes`;
  }

  document.getElementById('btnCopy').addEventListener('click', async (e) => {
    const btn = e.currentTarget;
    const ok = await copy(dbml);
    btn.textContent = ok ? 'Copied' : 'Failed';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = 'Copy DBML';
      btn.classList.remove('copied');
    }, 1500);
  });

  document.getElementById('btnDownload').addEventListener('click', () => {
    const blob = new Blob([dbml], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'schema.dbml';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

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
})();

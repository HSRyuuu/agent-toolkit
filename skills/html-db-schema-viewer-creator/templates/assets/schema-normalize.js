// =============================================================================
// schema-normalize.js — derive window.SCHEMA.relations from column fk fields
// Runs before any page script. Idempotent (skips if relations already present).
// =============================================================================

(function () {
  const s = window.SCHEMA;
  if (!s || !Array.isArray(s.tables)) return;
  if (Array.isArray(s.relations) && s.relations.length > 0) return;

  const rels = [];
  s.tables.forEach(t => {
    (t.columns || []).forEach(c => {
      if (c.fk && c.fk.table && c.fk.column) {
        rels.push({
          from: t.name,
          from_col: c.name,
          to: c.fk.table,
          to_col: c.fk.column
        });
      }
    });
  });
  s.relations = rels;
})();

---
slug: unify-skills-root
status: planned
intent: clear
pending-action: write .omo/plans/unify-skills-root.md
approach: Move every plugin-provided skill to a physical directory under ./skills, remove compatibility symlinks and legacy skill roots from plugin manifests, then update docs/catalog/validation so Claude Code and Codex load the same skill surface.
---

# Draft: unify-skills-root

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
| C1 | Plugin skill topology: all plugin skills exist physically as `skills/<name>/SKILL.md`; no `skills/` symlink aliases remain. | active | `find skills skills-system forks/taste-skill .agents/skills .claude/skills -maxdepth 2 -name SKILL.md` |
| C2 | Claude/Codex manifests both expose the same `./skills/` root. | active | `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json` |
| C3 | Human docs and agent guidance describe one unified `skills/` root, not `skills-system`/`skills-workflow` taxonomy. | active | `README.md`, `docs/catalog.md`, `AGENTS.md`, `.claude/CLAUDE.md` |
| C4 | Validation proves no moved skill was dropped and both plugin loaders can see the same skill set. | active | plugin validation, JSON checks, skill count/list diff |

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
<!-- assumption | adopted default | rationale | reversible? -->
| Repo-local update docs skills | Promote one canonical `update-project-docs` skill into `skills/update-project-docs` and remove duplicated `.agents/skills/update-project-docs` / `.claude/skills/update-project-docs` copies from the plugin repo plan. | The user asked for all plugin skills to be common across Claude and Codex; this skill is repo-specific and currently duplicated across agent-specific local skill roots. | Reversible by re-adding standalone local copies if short `/update-project-docs` invocation is preferred. |
| Empty legacy roots | Remove or leave empty legacy roots only if required by git hygiene; do not keep them as loader paths. | Official docs for both systems support root `skills/` for multi-skill plugins, and keeping old roots would preserve divergent behavior. | Reversible. |
| Taste skill fork location | Move the curated `forks/taste-skill/*` skill directories into `skills/`; keep non-skill fork metadata such as `forks/taste-skill/llms.txt` only if a moved skill references it, otherwise leave it outside loader scope. | The user's requirement is every skill under `skills/`, not every non-skill vendor artifact. | Reversible. |
| Tests | No new unit tests; use characterization/list-diff and real plugin validation instead. | This is a repository topology/config refactor with no app test harness. | Reversible if a validation script is added later. |
| Destination names | Preserve existing `skills/<alias>` directory names when replacing symlinks, even if `SKILL.md` frontmatter `name:` differs. | Existing Codex aliases and README links already use those directory names; renaming to frontmatter names would be a larger invocation/API break. | Reversible with a separate rename migration. |
| Valid skill definition | Promote only directories that contain `SKILL.md`; ignore empty `.agents/skills/architecture-html-dashboard` and `.claude/skills/architecture-html-dashboard` directories. | Empty folders are not loadable skills and should not affect plugin parity. | Reversible if content is later added. |
| Legacy roots after move | Remove legacy skill source roots from active structure after their skill contents move; keep non-skill artifacts only when referenced by a moved skill. | The user asked to merge the split roots into one; leaving old roots as archives creates future confusion. | Reversible from git. |
| Live `skills/git-pull-resolve-conflict` | Treat it as part of the post-change inventory because it already has `skills/git-pull-resolve-conflict/SKILL.md`; do not rewrite its behavior. | It is already under the target root and should remain available to both Claude and Codex. | Reversible by excluding it from staging/catalog if the user says it was accidental. |

## Findings (cited - path:lines)
- Codex official docs: plugin manifests live at `.codex-plugin/plugin.json`; a plugin can include `skills/`, and a full manifest points `skills` to `./skills/`. Source: https://developers.openai.com/codex/plugins/build
- Codex official docs: skills are directories with `SKILL.md`; plugins are the distribution unit for reusable skills; Codex supports symlinked skill folders for local scanning, but plugin packaging still documents `skills/` as the bundled component path. Source: https://developers.openai.com/codex/skills
- Claude official docs: plugin skills live in `skills/<name>/SKILL.md`; plugin skills are namespaced as `/plugin-name:skill-name`; Claude recommends the `skills/` layout for plugins that may grow beyond one skill. Source: https://code.claude.com/docs/en/plugins
- Claude plugin reference: `.claude-plugin/plugin.json` supports a `skills` field, but the manifest is optional for default locations and `skills/` is the documented component directory. Source: https://code.claude.com/docs/en/plugins-reference
- Current Codex manifest already uses a single root: `.codex-plugin/plugin.json:13` has `"skills": "./skills/"`.
- Current Claude manifest diverges: `.claude-plugin/plugin.json:5-10` lists `./skills/`, `./skills-workflow`, `./skills-system/`, and `./forks/taste-skill/`.
- Current README documents the divergence and symlink workaround: `README.md:25`, `README.md:35`, `README.md:41-45`, `README.md:61`.
- Current root guidance documents `skills/` as direct skills plus compatibility symlinks and says non-`skills/` content must be symlinked for Codex: `AGENTS.md:22-25`, `AGENTS.md:68-75`.
- Current direct plugin skills: 26 physical directories under `skills/` and 17 symlink aliases under `skills/`.
- Current legacy plugin skill roots: 4 `skills-system/*/SKILL.md`, 13 `forks/taste-skill/*/SKILL.md`, 0 `skills-workflow/*/SKILL.md`.
- Current agent-specific local skill duplicates: `.agents/skills/update-project-docs/SKILL.md` and `.claude/skills/update-project-docs/SKILL.md`.
- Planning review found no contradiction in the target approach, but required explicit handling for repo-local skill copies, destination naming, legacy root deletion, and current dirty/untracked scope.
- Expected post-change skill count if defaults are approved: 44 physical `skills/*/SKILL.md` entries = 26 current physical under `skills/` + 17 symlink target directories moved in + 1 promoted merged `update-project-docs`.
- Internal skill references that must be updated after movement include `help-agent-toolkit`, `project-setup`, `recommend-project-setting`, and the promoted `update-project-docs`.

## Decisions (with rationale)
- Plan as CLEAR intent: the requested outcome is specific, and unknowns are limited to reversible topology details.
- Use one canonical loader root: `skills/`.
- Replace every `skills/<alias>` symlink that points to a skill with a real directory containing the former target content.
- Preserve current alias directory names for moved taste skills and system skills.
- Merge the Claude/Codex variants of `update-project-docs` into one plugin skill that covers `README.md`, `docs/catalog.md`, `AGENTS.md`, `.claude/CLAUDE.md`, `.codex-plugin/plugin.json`, and `.claude-plugin/plugin.json`.
- Update `.claude-plugin/plugin.json` to point only to `./skills/` (or omit `skills` if validation proves default discovery is preferred); keep `.codex-plugin/plugin.json` at `./skills/`.
- Remove `skills-system/` and `skills-workflow/` from docs as active taxonomy. Preserve conceptual categories in catalog tables as metadata only if helpful, not as directories.
- Treat `.claude-plugin/marketplace.json` existing whitespace-only dirty change as unrelated unless the executor intentionally normalizes it as part of JSON validation.

## Scope IN
- Move or promote all plugin-provided skill directories into `skills/`.
- Resolve symlink aliases by replacing them with physical directories.
- Promote a single `update-project-docs` skill under `skills/` unless user vetoes.
- Update plugin manifests, README, docs catalog, AGENTS.md, and `.claude/CLAUDE.md`.
- Validate JSON, plugin manifests, skill count preservation, no broken symlinks, no references to obsolete loader roots outside historical notes/templates.

## Scope OUT (Must NOT have)
- Do not change individual skill behavior except path references that must change after the move.
- Do not move non-skill templates into `skills/`.
- Do not rewrite `templates/project-setup` semantics unless a reference is now false for this repo.
- Do not delete user-created unrelated untracked content such as `skills/git-pull-resolve-conflict/`.
- Do not commit unless the user explicitly asks after plan approval.
- Do not rename moved skill directories to their frontmatter names in this migration.
- Do not promote empty directories that do not contain `SKILL.md`.

## Open questions
- Approval needed: proceed with the adopted defaults above, especially merging `update-project-docs` into `skills/update-project-docs`, preserving current directory names, and removing legacy skill roots after movement?

## Approval gate
status: approved
pending-action: complete
brief: Plan will unify the plugin on `skills/` as the only skill root for both Claude Code and Codex, physically move the existing system/taste/plugin-local skill directories there, remove `skills/` compatibility symlinks, and update docs plus validation commands accordingly.
result: `.omo/plans/unify-skills-root.md` written after user approval.
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->

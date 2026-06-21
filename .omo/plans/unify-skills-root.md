# unify-skills-root - Work Plan

## TL;DR (For humans)

**What you'll get:** Claude Code와 Codex가 같은 플러그인 스킬 목록을 보도록, 모든 스킬을 하나의 `skills/` 묶음으로 정리한다. 지금 나뉘어 있는 시스템 스킬과 taste 스킬은 별도 루트나 symlink 없이 같은 위치에서 관리된다.

**Why this approach:** 두 제품의 공식 문서가 모두 다중 스킬 플러그인의 표준 위치로 루트 `skills/`를 설명한다. 지금처럼 Claude는 여러 루트, Codex는 symlink를 보는 구조를 유지하면 앞으로 양쪽 동작이 계속 어긋난다.

**What it will NOT do:** 개별 스킬의 목적이나 동작을 리디자인하지 않는다. 템플릿 자료를 스킬로 승격하지 않는다. 기존 디렉토리 이름을 frontmatter 이름에 맞춰 rename하지 않는다.

**Effort:** Medium
**Risk:** Medium - 파일 이동, symlink 제거, 문서/매니페스트/내부 스킬 설명이 동시에 맞아야 한다.
**Decisions to sanity-check:** `update-project-docs`는 공통 스킬로 병합한다. 기존 symlink 이름을 새 실제 디렉토리 이름으로 유지한다. 비어 있는 local skill 디렉토리는 스킬로 보지 않는다.

Your next move: execute this plan with `$omo:start-work` or ask for a high-accuracy plan review first. Full execution detail follows below.

---

> TL;DR (machine): Medium-risk repo topology refactor: replace plugin skill symlinks and split roots with one physical `skills/` root, update manifests/docs/internal references, then prove Claude/Codex parity through manifest validation and inventory checks.

## Scope
### Must have
- All plugin-provided skills must physically live at `skills/<directory>/SKILL.md`.
- `skills/` must contain no top-level symlink skill aliases after the migration.
- `.codex-plugin/plugin.json` must continue to expose `./skills/`.
- `.claude-plugin/plugin.json` must expose only `./skills/` for skills, not `./skills-workflow`, `./skills-system`, or `./forks/taste-skill`.
- The following existing symlink destinations must be moved into the current symlink directory names:

| Source | Destination |
| --- | --- |
| `skills-system/create-claude-plugin/` | `skills/create-claude-plugin/` |
| `skills-system/help-agent-toolkit/` | `skills/help-agent-toolkit/` |
| `skills-system/project-setup/` | `skills/project-setup/` |
| `skills-system/recommend-project-setting/` | `skills/recommend-project-setting/` |
| `forks/taste-skill/brandkit/` | `skills/brandkit/` |
| `forks/taste-skill/brutalist-skill/` | `skills/brutalist-skill/` |
| `forks/taste-skill/gpt-tasteskill/` | `skills/gpt-tasteskill/` |
| `forks/taste-skill/image-to-code-skill/` | `skills/image-to-code-skill/` |
| `forks/taste-skill/imagegen-frontend-mobile/` | `skills/imagegen-frontend-mobile/` |
| `forks/taste-skill/imagegen-frontend-web/` | `skills/imagegen-frontend-web/` |
| `forks/taste-skill/minimalist-skill/` | `skills/minimalist-skill/` |
| `forks/taste-skill/output-skill/` | `skills/output-skill/` |
| `forks/taste-skill/redesign-skill/` | `skills/redesign-skill/` |
| `forks/taste-skill/soft-skill/` | `skills/soft-skill/` |
| `forks/taste-skill/stitch-skill/` | `skills/stitch-skill/` |
| `forks/taste-skill/taste-skill/` | `skills/taste-skill/` |
| `forks/taste-skill/taste-skill-v1/` | `skills/taste-skill-v1/` |

- Merge `.agents/skills/update-project-docs/SKILL.md` and `.claude/skills/update-project-docs/SKILL.md` into one canonical `skills/update-project-docs/SKILL.md` that covers both agent surfaces.
- Preserve the existing untracked `skills/git-pull-resolve-conflict/SKILL.md`; include it in inventory and docs if it still exists when executing.
- Update internal references in moved skills that hard-code old roots, especially `help-agent-toolkit`, `project-setup`, `recommend-project-setting`, and `update-project-docs`.
- Update `README.md`, `docs/catalog.md`, `AGENTS.md`, and `.claude/CLAUDE.md` so they describe the single-root policy.
- Remove or make non-active any legacy skill source roots after their skill contents move. `skills-workflow/` must not remain documented or configured as a loader root.
- Preserve unrelated dirty worktree changes. Current known dirty state before execution: `.claude-plugin/marketplace.json`, `.gitignore`, `AGENTS.md`, `.agents/skills/`, `.omo/`, and `skills/git-pull-resolve-conflict/`.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do not implement the migration by adding more symlinks.
- Do not keep Claude and Codex on different loader topologies.
- Do not rename moved skill directories to their `SKILL.md` frontmatter `name:` values in this migration.
- Do not alter individual skill behavior except where old path references would now be false.
- Do not move `templates/` into `skills/`.
- Do not promote empty directories without `SKILL.md`, including `.agents/skills/architecture-html-dashboard` and `.claude/skills/architecture-html-dashboard`.
- Do not stage or commit unrelated user changes unless they are intentionally included in this migration.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: none; this repo has no app/unit test harness for plugin topology. Use characterization inventory before the move, deterministic file-system assertions after the move, plugin manifest validation, and real plugin listing commands.
- RED proof before production edits: capture the current mismatch and store it at `.omo/evidence/task-1-unify-skills-root.txt`:
  - `find skills -maxdepth 1 -type l -exec basename {} \; | sort`
  - `find skills-system forks/taste-skill .agents/skills .claude/skills -maxdepth 2 -name SKILL.md -print 2>/dev/null | sort`
  - `jq -r '.skills' .claude-plugin/plugin.json`
  - PASS condition for RED: output shows top-level `skills/` symlinks, skill files outside `skills/`, and Claude manifest skills other than only `./skills/`.
- GREEN proof after edits: capture `.omo/evidence/final-unify-skills-root.txt` with:
  - `find skills -maxdepth 1 -type l -print`
  - `find skills-system skills-workflow forks/taste-skill .agents/skills .claude/skills -maxdepth 2 -name SKILL.md -print 2>/dev/null`
  - `find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort`
  - `jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json .agents/plugins/marketplace.json`
  - `python3 /Users/happyhsryu/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py /Users/happyhsryu/dev/personal/agent-toolkit`
  - `codex plugin marketplace add /Users/happyhsryu/dev/personal/agent-toolkit`
  - `codex plugin list --marketplace agent-toolkit-local --available --json`
- Expected GREEN inventory: zero top-level symlinks in `skills/`; zero `SKILL.md` under legacy/plugin-local roots listed above; at least 44 physical `skills/*/SKILL.md` entries if `skills/git-pull-resolve-conflict` still exists.
- Claude real-surface check: run `claude --plugin-dir /Users/happyhsryu/dev/personal/agent-toolkit -p "/help"` if `claude` CLI is installed and non-interactive mode is available; otherwise run `claude plugin validate /Users/happyhsryu/dev/personal/agent-toolkit` and record the absence/presence of Claude CLI as the reason.

## Execution strategy
### Parallel execution waves
- Wave 0: Characterization and inventory. Read-only and must run before any move.
- Wave 1: Physical topology migration. Must be serial enough to avoid symlink-target collisions.
- Wave 2: Manifest and internal skill reference updates. Can run after Wave 1.
- Wave 3: Human docs and catalog regeneration. Can run after Wave 1 and Wave 2 facts are known.
- Wave 4: Validation, review, and commit preparation. Runs after all edits.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1 | none | 2, 8 | none |
| 2 | 1 | 3, 4, 5, 6, 8 | none |
| 3 | 2 | 8 | 4, 5 |
| 4 | 2 | 6, 8 | 3, 5 |
| 5 | 2 | 6, 8 | 3, 4 |
| 6 | 3, 4, 5 | 8 | 7 |
| 7 | 2 | 8 | 6 |
| 8 | 3, 4, 5, 6, 7 | final | none |

## Todos
> Implementation + Test = ONE todo. Never separate.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [x] 1. Capture the current mismatch as RED evidence
  What to do / Must NOT do: Create `.omo/evidence/` if needed. Capture the current topology mismatch before any production edit. Do not edit source files in this todo.
  Parallelization: Wave 0 | Blocked by: none | Blocks: 2, 8
  References (executor has NO interview context - be exhaustive): `.omo/drafts/unify-skills-root.md:31`, `.claude-plugin/plugin.json:5`, `.codex-plugin/plugin.json:13`, `AGENTS.md:68`, `README.md:35`.
  Acceptance criteria (agent-executable): `.omo/evidence/task-1-unify-skills-root.txt` exists and contains output proving all three current failures: `skills/` symlinks exist, `SKILL.md` files exist outside `skills/`, and Claude manifest lists multiple skill roots.
  QA scenarios (name the exact tool + invocation): happy: `find skills -maxdepth 1 -type l -exec basename {} \; | sort; find skills-system forks/taste-skill .agents/skills .claude/skills -maxdepth 2 -name SKILL.md -print 2>/dev/null | sort; jq -r '.skills' .claude-plugin/plugin.json` redirected to `.omo/evidence/task-1-unify-skills-root.txt`, PASS if all mismatch categories appear. failure: `test -s .omo/evidence/task-1-unify-skills-root.txt && grep -q 'skills-system\\|forks/taste-skill\\|brandkit' .omo/evidence/task-1-unify-skills-root.txt`, PASS if grep finds old topology. Evidence `.omo/evidence/task-1-unify-skills-root.txt`.
  Commit: N | evidence only

- [x] 2. Replace skill symlink aliases with physical directories under `skills/`
  What to do / Must NOT do: For each row in the Scope mapping table, remove the `skills/<name>` symlink and move/copy the source directory into that exact destination. Preserve nested files such as `skills/stitch-skill/DESIGN.md`. Do not use shell deletion for anything that is not a symlink or an emptied legacy source after content is confirmed present in `skills/`.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 3, 4, 5, 6, 8
  References (executor has NO interview context - be exhaustive): `skills/brandkit -> ../forks/taste-skill/brandkit`, `skills/create-claude-plugin -> ../skills-system/create-claude-plugin`, `.omo/drafts/unify-skills-root.md:40`, `.omo/drafts/unify-skills-root.md:50`.
  Acceptance criteria (agent-executable): `find skills -maxdepth 1 -type l -print` prints nothing. Every mapped destination has `SKILL.md`. `find skills-system forks/taste-skill -maxdepth 2 -name SKILL.md -print 2>/dev/null` prints nothing after legacy cleanup.
  QA scenarios (name the exact tool + invocation): happy: `for d in create-claude-plugin help-agent-toolkit project-setup recommend-project-setting brandkit brutalist-skill gpt-tasteskill image-to-code-skill imagegen-frontend-mobile imagegen-frontend-web minimalist-skill output-skill redesign-skill soft-skill stitch-skill taste-skill taste-skill-v1; do test -f "skills/$d/SKILL.md" || echo "MISSING: $d"; done`, PASS if no `MISSING`. failure: `find skills -maxdepth 1 -type l -print`, PASS if no output. Evidence `.omo/evidence/task-2-unify-skills-root.txt`.
  Commit: Y | refactor(skills): unify plugin skill directories

- [x] 3. Merge `update-project-docs` into one plugin skill
  What to do / Must NOT do: Create `skills/update-project-docs/SKILL.md` from the two existing variants. It must describe syncing `AGENTS.md`, `.claude/CLAUDE.md`, `README.md`, `docs/catalog.md`, `.codex-plugin/plugin.json`, and `.claude-plugin/plugin.json`; it must scan only `skills/` for plugin skills. Remove plugin-local duplicate skill copies after the merged skill is present. Do not promote empty `architecture-html-dashboard` directories.
  Parallelization: Wave 2 | Blocked by: 2 | Blocks: 6, 8
  References (executor has NO interview context - be exhaustive): `.agents/skills/update-project-docs/SKILL.md:1`, `.claude/skills/update-project-docs/SKILL.md:1`, `.omo/drafts/unify-skills-root.md:22`, `.omo/drafts/unify-skills-root.md:52`.
  Acceptance criteria (agent-executable): `test -f skills/update-project-docs/SKILL.md`; `find .agents/skills .claude/skills -maxdepth 2 -name SKILL.md -print 2>/dev/null` prints nothing; `rg -n 'skills-workflow|skills-system|\\.Codex|\\.Codex-plugin' skills/update-project-docs/SKILL.md` either prints nothing or only mentions them as legacy terms to remove.
  QA scenarios (name the exact tool + invocation): happy: `rg -n 'AGENTS.md|\\.claude/CLAUDE.md|\\.codex-plugin/plugin.json|\\.claude-plugin/plugin.json|docs/catalog.md|README.md' skills/update-project-docs/SKILL.md`, PASS if all six targets are represented. failure: `find .agents/skills .claude/skills -maxdepth 2 -name SKILL.md -print 2>/dev/null`, PASS if no output. Evidence `.omo/evidence/task-3-unify-skills-root.txt`.
  Commit: Y | refactor(skills): merge project docs skill

- [x] 4. Unify Claude and Codex plugin manifests on `./skills/`
  What to do / Must NOT do: Update `.claude-plugin/plugin.json` so the skills field is only `./skills/` or `["./skills/"]`; prefer the single string if Claude validation accepts it because Codex already uses a string. Leave `.codex-plugin/plugin.json` skills as `./skills/`. Keep marketplace source paths unchanged unless validation proves they are invalid. Preserve unrelated `.claude-plugin/marketplace.json` whitespace-only changes unless intentionally normalized.
  Parallelization: Wave 2 | Blocked by: 2 | Blocks: 6, 8
  References (executor has NO interview context - be exhaustive): `.claude-plugin/plugin.json:5`, `.codex-plugin/plugin.json:13`, `https://developers.openai.com/codex/plugins/build`, `https://code.claude.com/docs/en/plugins`.
  Acceptance criteria (agent-executable): `jq -r '.skills' .codex-plugin/plugin.json` prints `./skills/`; `jq -r '.skills | if type=="array" then join(",") else . end' .claude-plugin/plugin.json` prints only `./skills/`; `jq empty .claude-plugin/plugin.json .codex-plugin/plugin.json` exits 0.
  QA scenarios (name the exact tool + invocation): happy: `jq -r '.skills' .codex-plugin/plugin.json && jq -r '.skills | if type=="array" then join(",") else . end' .claude-plugin/plugin.json`, PASS if both outputs equal `./skills/`. failure: `rg -n 'skills-workflow|skills-system|forks/taste-skill' .claude-plugin/plugin.json .codex-plugin/plugin.json`, PASS if no output. Evidence `.omo/evidence/task-4-unify-skills-root.txt`.
  Commit: Y | refactor(plugin): align skill roots

- [x] 5. Update moved skills that hard-code the old topology
  What to do / Must NOT do: Edit moved skills only where instructions mention `skills-system`, `skills-workflow`, `forks/taste-skill`, `.agents/skills`, `.claude/skills`, `.Codex`, or `.Codex-plugin` as active repo topology. The main required files are `skills/help-agent-toolkit/SKILL.md`, `skills/project-setup/SKILL.md`, `skills/recommend-project-setting/SKILL.md`, and `skills/update-project-docs/SKILL.md`. Do not rewrite templates unless they are describing this plugin repo rather than target-project installation behavior. `.claude/skills` remains allowed only when the text explicitly describes installing assets into a target project, not this plugin repo's own loader topology.
  Parallelization: Wave 2 | Blocked by: 2 | Blocks: 6, 8
  References (executor has NO interview context - be exhaustive): `skills-system/help-agent-toolkit/SKILL.md:23`, `skills-system/help-agent-toolkit/SKILL.md:50`, `.omo/drafts/unify-skills-root.md:45`.
  Acceptance criteria (agent-executable): `rg -n 'skills-system|skills-workflow|forks/taste-skill|\\.agents/skills|\\.Codex|\\.Codex-plugin' skills/help-agent-toolkit skills/project-setup skills/recommend-project-setting skills/update-project-docs` prints nothing except explicit legacy warnings that are still accurate and marked as legacy. `rg -n '\\.claude/skills' skills/project-setup skills/recommend-project-setting` may match only lines that explicitly describe target-project installation paths.
  QA scenarios (name the exact tool + invocation): happy: `rg -n 'find .*skills|skills/' skills/help-agent-toolkit/SKILL.md skills/update-project-docs/SKILL.md`, PASS if scanning instructions use `skills/` as the only plugin skill root. failure: `rg -n 'skills-system|skills-workflow|forks/taste-skill' skills/help-agent-toolkit/SKILL.md skills/update-project-docs/SKILL.md`, PASS if no active-root references remain. Evidence `.omo/evidence/task-5-unify-skills-root.txt`.
  Commit: Y | docs(skills): remove old topology references

- [x] 6. Regenerate human docs and agent guidance for one skill root
  What to do / Must NOT do: Update `README.md`, `docs/catalog.md`, `AGENTS.md`, and `.claude/CLAUDE.md` from current `skills/*/SKILL.md` inventory. The catalog must list all physical plugin skills under `skills/`, including moved taste/system skills and `skills/git-pull-resolve-conflict` if present. It may keep category labels as metadata, but not as directories. Do not mention symlink compatibility as the current design.
  Parallelization: Wave 3 | Blocked by: 3, 4, 5 | Blocks: 8
  References (executor has NO interview context - be exhaustive): `README.md:25`, `README.md:35`, `README.md:41`, `README.md:61`, `docs/catalog.md:4`, `docs/catalog.md:12`, `AGENTS.md:22`, `.claude/CLAUDE.md:19`.
  Acceptance criteria (agent-executable): `rg -n 'skills-system|skills-workflow|forks/taste-skill|symlink|\\.Codex|\\.Codex-plugin' README.md docs/catalog.md AGENTS.md .claude/CLAUDE.md` prints nothing except historical notes explicitly labeled as legacy, if any. Every catalog link of the form `../skills/<name>/SKILL.md` resolves.
  QA scenarios (name the exact tool + invocation): happy: `grep -oE '\\(\\.\\./skills/[^)]+/SKILL\\.md\\)' docs/catalog.md | tr -d '()' | sed 's#^../##' | while read p; do test -f "$p" || echo "MISSING: $p"; done`, PASS if no `MISSING`. failure: `rg -n 'skills-system|skills-workflow|forks/taste-skill|compatibility symlink' README.md docs/catalog.md AGENTS.md .claude/CLAUDE.md`, PASS if no active-current references remain. Evidence `.omo/evidence/task-6-unify-skills-root.txt`.
  Commit: Y | docs: document unified skills root

- [x] 7. Clean legacy root leftovers without removing non-skill templates
  What to do / Must NOT do: After all skill directories have moved, remove empty `skills-system/`, `skills-workflow/`, and `forks/taste-skill/` skill-source leftovers from active repo structure. Keep non-skill files only if a moved skill references them; otherwise remove obsolete scoped `AGENTS.md` that contradicts the new topology. Do not touch `templates/`.
  Parallelization: Wave 3 | Blocked by: 2 | Blocks: 8
  References (executor has NO interview context - be exhaustive): `forks/taste-skill/AGENTS.md`, `.gitignore:5`, `.omo/drafts/unify-skills-root.md:28`, `.omo/drafts/unify-skills-root.md:67`.
  Acceptance criteria (agent-executable): `find skills-system skills-workflow forks/taste-skill -maxdepth 2 -name SKILL.md -print 2>/dev/null` prints nothing; `rg -n 'forks/taste-skill/AGENTS.md|skills-system/|skills-workflow/' AGENTS.md README.md docs/catalog.md .claude/CLAUDE.md` prints nothing except explicit legacy notes.
  QA scenarios (name the exact tool + invocation): happy: `find skills-system skills-workflow forks/taste-skill -maxdepth 2 -name SKILL.md -print 2>/dev/null`, PASS if no output. failure: `test ! -e forks/taste-skill/AGENTS.md || ! rg -n 'not move|symlink' forks/taste-skill/AGENTS.md`, PASS if contradictory scoped guidance is absent. Evidence `.omo/evidence/task-7-unify-skills-root.txt`.
  Commit: Y | chore: remove legacy skill roots

- [ ] 8. Run full validation and prepare the structural commit
  What to do / Must NOT do: Run the full GREEN proof commands. Review `git diff --stat` and `git status --short` before staging. Stage only files that belong to this migration, including `.omo/plans/unify-skills-root.md` and evidence files if this repo keeps `.omo/` work artifacts. Do not stage unrelated `.claude-plugin/marketplace.json` whitespace-only change unless it is intentionally normalized and mentioned.
  Parallelization: Wave 4 | Blocked by: 3, 4, 5, 6, 7 | Blocks: final
  References (executor has NO interview context - be exhaustive): `.omo/drafts/unify-skills-root.md:55`, `AGENTS.md:80`, `.agents/plugins/marketplace.json:9`, `plugins/agent-toolkit -> ..`.
  Acceptance criteria (agent-executable): All GREEN proof commands in `## Verification strategy` exit 0 or record a clear, pre-existing missing-tool reason for Claude-only CLI validation. `git diff --stat` shows only migration-owned paths. `git status --short` has no unreviewed new skill-root inconsistencies.
  QA scenarios (name the exact tool + invocation): happy: `{ find skills -maxdepth 1 -type l -print; find skills-system skills-workflow forks/taste-skill .agents/skills .claude/skills -maxdepth 2 -name SKILL.md -print 2>/dev/null; find skills -mindepth 2 -maxdepth 2 -name SKILL.md -print | sort; jq empty .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json .agents/plugins/marketplace.json; python3 /Users/happyhsryu/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py /Users/happyhsryu/dev/personal/agent-toolkit; codex plugin marketplace add /Users/happyhsryu/dev/personal/agent-toolkit; codex plugin list --marketplace agent-toolkit-local --available --json; } | tee .omo/evidence/final-unify-skills-root.txt`, PASS if assertions meet expected GREEN inventory. failure: `rg -n 'skills-system|skills-workflow|forks/taste-skill|\\.agents/skills|\\.Codex|\\.Codex-plugin' README.md docs/catalog.md AGENTS.md .claude/CLAUDE.md skills .claude-plugin/plugin.json .codex-plugin/plugin.json` plus `rg -n '\\.claude/skills' README.md docs/catalog.md AGENTS.md .claude/CLAUDE.md skills .claude-plugin/plugin.json .codex-plugin/plugin.json`, PASS if first command has no active stale references and second command matches only target-project installation behavior. Evidence `.omo/evidence/final-unify-skills-root.txt`.
  Commit: Y | refactor(plugin): unify skills root

## Final verification wave
> Runs in parallel after ALL todos. ALL must APPROVE. Record results and complete automatically when all checks pass; ask the user only on a real blocker or failed verification that cannot be resolved by the executor.
- [ ] F1. Plan compliance audit: compare final diff against this plan. Exact invocation: `git diff --name-status HEAD -- . ':!.omo/evidence/*'` plus manual checklist against Todos 1-8. PASS if every Must have is covered and every Must NOT have is respected.
- [ ] F2. Code quality review: inspect changed `SKILL.md` files and manifests for stale paths, broken markdown links, malformed frontmatter, and overbroad rewrites. Exact invocation: `rg -n '^---$|^name:|^description:' skills/*/SKILL.md` plus targeted review of moved/merged skills.
- [ ] F3. Real manual QA: run Codex plugin listing after marketplace refresh. Exact invocation: `codex plugin marketplace add /Users/happyhsryu/dev/personal/agent-toolkit && codex plugin list --marketplace agent-toolkit-local --available --json`. PASS if `agent-toolkit` is listed and its manifest validates from the unified root. Run Claude plugin validation or `claude --plugin-dir /Users/happyhsryu/dev/personal/agent-toolkit -p "/help"` when available.
- [ ] F4. Scope fidelity: run stale topology search. Exact invocation: `rg -n 'skills-system|skills-workflow|forks/taste-skill|compatibility symlink|\\.agents/skills|\\.Codex|\\.Codex-plugin' README.md docs/catalog.md AGENTS.md .claude/CLAUDE.md skills .claude-plugin/plugin.json .codex-plugin/plugin.json` plus `rg -n '\\.claude/skills' README.md docs/catalog.md AGENTS.md .claude/CLAUDE.md skills .claude-plugin/plugin.json .codex-plugin/plugin.json`. PASS if first command has no active-current matches and second command matches only target-project installation behavior, not this plugin repo's loader topology.

## Commit strategy
- One logical structural commit after validation passes: `refactor(plugin): unify skills root`.
- Include file moves, manifest changes, docs/catalog updates, merged `update-project-docs`, plan/evidence artifacts if `.omo/` is intended to be versioned for this work.
- Do not amend previous commits.
- Do not stage unrelated user work. Known unrelated/needs-review paths before execution: `.claude-plugin/marketplace.json` whitespace-only change and any pre-existing untracked content not claimed by this plan.
- If committing, footer: `Plan: .omo/plans/unify-skills-root.md`.

## Success criteria
- `skills/` is the only active plugin skill root for both Claude Code and Codex.
- Every loadable plugin skill has exactly one physical `skills/<directory>/SKILL.md` location.
- `skills/` has zero top-level symlink aliases.
- `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` both point to the same `./skills/` skill root.
- No `SKILL.md` remains under `skills-system/`, `skills-workflow/`, `forks/taste-skill/`, `.agents/skills`, or `.claude/skills`.
- `README.md`, `docs/catalog.md`, `AGENTS.md`, and `.claude/CLAUDE.md` describe the unified topology and contain no stale active instructions for split roots or symlink compatibility.
- `help-agent-toolkit`, `project-setup`, `recommend-project-setting`, and `update-project-docs` no longer instruct agents to scan or maintain the old split-root structure.
- JSON and plugin validation commands pass, or any missing external CLI is recorded as an environment limitation with all local validation passing.
- The final evidence file proves the RED mismatch was removed and the GREEN unified state exists.

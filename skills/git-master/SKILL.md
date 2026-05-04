---
name: git-master
description: 여러 파일에 걸친 변경을 커밋하거나, 브랜치 이력을 정리·rebase 하거나, 과거 변경이 언제 어떻게 들어왔는지 추적해야 할 때 사용한다. 트리거 - "커밋해줘", "atomic commit", "rebase", "git history", "이 변경 누가 언제 추가했어?", "커밋 분리", "브랜치 정리", "git log 분석".
---

# Git Master Skill

You are a Git expert combining three specializations:
1. **Commit Architect**: Atomic commits, dependency ordering, style detection
2. **Rebase Surgeon**: History rewriting, conflict resolution, branch cleanup
3. **History Archaeologist**: Finding when/where specific changes were introduced

## Core Principle: Multiple Commits by Default

**ONE COMMIT = AUTOMATIC FAILURE**

Hard rules:
- 3+ files changed -> MUST be 2+ commits
- 5+ files changed -> MUST be 3+ commits
- 10+ files changed -> MUST be 5+ commits

## Style Detection (First Step)

Before committing, analyze the last 30 commits:
```bash
git log -30 --oneline
git log -30 --pretty=format:"%s"
```

Detect:
- **Language**: Korean vs English (use majority)
- **Style**: SEMANTIC (feat:, fix:) vs PLAIN vs SHORT

## Commit Splitting Rules

| Criterion | Action |
|-----------|--------|
| Different directories/modules | SPLIT |
| Different component types | SPLIT |
| Can be reverted independently | SPLIT |
| Different concerns (UI/logic/config/test) | SPLIT |
| New file vs modification | SPLIT |

## History Search Commands

| Goal | Command |
|------|---------|
| When was "X" added? | `git log -S "X" --oneline` |
| What commits touched "X"? | `git log -G "X" --oneline` |
| Who wrote line N? | `git blame -L N,N file.py` |
| When did bug start? | `git bisect start && git bisect bad && git bisect good <tag>` |

## Rebase Safety

- **NEVER** rebase main/master
- Use `--force-with-lease` (never `--force`)
- Stash dirty files before rebasing


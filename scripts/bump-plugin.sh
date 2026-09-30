#!/usr/bin/env bash
# Usage: scripts/bump-plugin.sh <plugin> [patch|minor|major]
# Bumps `version` in both plugins/<plugin>/.claude-plugin/plugin.json and .codex-plugin/plugin.json to the same value.
set -euo pipefail
p="${1:?plugin name}"; kind="${2:-patch}"
c="plugins/$p/.claude-plugin/plugin.json"; x="plugins/$p/.codex-plugin/plugin.json"
old=$(jq -r .version "$c"); [ "$old" = "$(jq -r .version "$x")" ] || { echo "version mismatch in $p" >&2; exit 1; }
IFS=. read -r a b d <<<"$old"
case "$kind" in major) a=$((a+1)); b=0; d=0;; minor) b=$((b+1)); d=0;; patch) d=$((d+1));; *) echo "bad kind" >&2; exit 1;; esac
new="$a.$b.$d"
for f in "$c" "$x"; do jq --arg v "$new" '.version=$v' "$f" > "$f.tmp" && mv "$f.tmp" "$f"; done
echo "$p $old -> $new"

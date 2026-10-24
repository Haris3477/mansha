#!/usr/bin/env bash
# Read-only check: is the Graphify code map current? No LLM, changes nothing.
# Exit 0 = fresh, 1 = stale, 2 = no graph.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
G=graphify-out/graph.json
LOG="$HOME/.cache/graphify-rebuild.log"

if [ ! -f "$G" ]; then
  echo "NO GRAPH: run  graphify update ."
  exit 2
fi

BUILT=$(grep -o '"built_at_commit": *"[0-9a-f]*"' "$G" | grep -o '[0-9a-f]\{40\}' | head -1)
HEAD=$(git rev-parse HEAD)
if [ "$BUILT" = "$HEAD" ]; then STATE="FRESH"; CODE=0
else STATE="STALE: run  graphify update ."; CODE=1; fi

echo "graph built at : ${BUILT:0:7}   HEAD: ${HEAD:0:7}   -> $STATE"

CHANGED=$(git status --porcelain | cut -c4-)
if [ -n "$CHANGED" ]; then
  echo "not in graph   : (uncommitted/untracked; read these directly)"
  echo "$CHANGED" | sed 's/^/                 /'
else
  echo "not in graph   : nothing, working tree clean"
fi

if [ -f "$LOG" ]; then
  LAST=$(grep -E 'Rebuilt|failed|exceeded|could not' "$LOG" | tail -1)
  echo "last rebuild   : ${LAST:-no rebuild recorded yet}"
else
  echo "last rebuild   : no hook run yet"
fi
exit $CODE

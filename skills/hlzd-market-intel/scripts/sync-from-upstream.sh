#!/usr/bin/env bash
# sync-from-upstream.sh — pull latest changes from mvanhorn/last30days-skill
# into this HLZD fork. Auto-merges non-conflicting files; lists conflict
# files for manual review.
#
# Usage:
#   bash scripts/sync-from-upstream.sh          # sync from upstream main
#   bash scripts/sync-from-upstream.sh --dry-run   # show what would happen
#
# Exit codes:
#   0 = clean merge (no conflicts)
#   1 = merge conflicts (manual review required)
#   2 = fetch failed (network / remote issue)

set -uo pipefail

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=1
fi

# Sanity: must be run from inside the skill repo
if [[ ! -d .git ]]; then
    echo "ERROR: must run from inside the skill repo (no .git found)" >&2
    exit 2
fi

if ! git remote get-url upstream >/dev/null 2>&1; then
    echo "ERROR: no 'upstream' remote configured. Add with:" >&2
    echo "  git remote add upstream https://github.com/mvanhorn/last30days-skill.git" >&2
    exit 2
fi

echo "==> Fetching upstream main..."
if ! git fetch upstream main; then
    echo "ERROR: fetch failed (network issue or upstream remote not reachable)" >&2
    exit 2
fi

# Show local commits since the last sync point
echo ""
echo "==> Local commits since last sync (origin/main..HEAD):"
git log --oneline origin/main..HEAD 2>/dev/null | head -20 || echo "(none)"

echo ""
echo "==> Upstream commits available to merge (HEAD..upstream/main):"
git log --oneline HEAD..upstream/main 2>/dev/null | head -20 || echo "(none)"

if [[ $DRY_RUN -eq 1 ]]; then
    echo ""
    echo "DRY RUN: stopping before merge attempt. Re-run without --dry-run to proceed."
    exit 0
fi

echo ""
echo "==> Attempting merge of upstream/main into current branch..."
if git merge --no-edit upstream/main -m "sync: mvanhorn/last30days-skill upstream $(date -u +%Y-%m-%d)"; then
    echo ""
    echo "==> Merge succeeded with no conflicts."
    echo ""
    echo "==> Recommended next steps:"
    echo "    python -m pytest tests/ -v   # verify tests still pass"
    echo "    bash scripts/last30days.py '海外安防摄像头 2026' --extract-pain --emit=compact   # smoke test"
    exit 0
else
    echo ""
    echo "==> Merge has conflicts. The following files need manual review:"
    echo ""
    git diff --name-only --diff-filter=U 2>/dev/null
    echo ""
    echo "Resolution rule of thumb for HLZD fork:"
    echo "  - SKILL.md, README.md, assets/* : keep HLZD version (ours)"
    echo "  - scripts/lib/*.py, scripts/last30days.py : take upstream version (theirs) unless"
    echo "    the conflict is in pain_extractor integration (then keep ours)"
    echo "  - tests/*.py : take upstream (theirs)"
    echo ""
    echo "After resolving: git add <resolved files> && git commit"
    exit 1
fi

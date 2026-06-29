#!/usr/bin/env bash
# Deploy the caravan site to GitHub Pages.
# Safe to re-run: it creates the repo on first run, then just pushes updates.
set -euo pipefail

OWNER="snthor-phd"
REPO="polar-bears-2026"
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "→ Caravan site deploy  ($OWNER/$REPO)"

# --- prerequisites ---------------------------------------------------------
command -v git >/dev/null || { echo "✗ git not found."; exit 1; }
if ! command -v gh >/dev/null; then
  echo "✗ GitHub CLI (gh) not found. Install with:  brew install gh"
  echo "  Then run:  gh auth login   and re-run this script."
  exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
  echo "✗ gh is not signed in. Run:  gh auth login"
  echo "  (choose GitHub.com → SSH → your existing key), then re-run this script."
  exit 1
fi

# --- commit ----------------------------------------------------------------
git init -q
git add -A
if git diff --cached --quiet 2>/dev/null; then
  echo "• Nothing new to commit."
else
  git commit -q -m "Update caravan site ($(date +%Y-%m-%d))"
  echo "• Committed changes."
fi
git branch -M main

# --- repo + push -----------------------------------------------------------
if gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "git@github.com:$OWNER/$REPO.git"
  git push -u origin main
else
  gh repo create "$OWNER/$REPO" --public --source=. --remote=origin --push \
    --description "Northern Lights & Polar Bears 2026 RV caravan — itinerary and trip docs"
fi

# --- enable Pages (ignore error if already on) -----------------------------
gh api --method POST "repos/$OWNER/$REPO/pages" \
  -f "source[branch]=main" -f "source[path]=/" >/dev/null 2>&1 \
  && echo "• GitHub Pages enabled." \
  || echo "• GitHub Pages already enabled (or enable it in Settings → Pages)."

echo ""
echo "✓ Done. Live in ~30–60s at:"
echo "    https://$OWNER.github.io/$REPO/"
echo ""
echo "  Update later:  edit files, then re-run ./deploy.sh"

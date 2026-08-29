#!/usr/bin/env bash
# Build the site locally with the SAME Jekyll GitHub Pages uses, to catch
# build-breaking errors before pushing.
#
#   ./preview.sh          build only, reports errors
#   ./preview.sh serve    build and serve at http://localhost:4000
#
# Why this exists: `gem install jekyll` gives you Jekyll 4.x, whose newer Liquid
# accepts syntax that GitHub's Liquid 4.0.4 rejects. A compound `where_exp`
# condition in search.json built fine on Jekyll 4 and failed the Pages build.
# This script pins github-pages 232 / Jekyll 3.10.0 / Liquid 4.0.4 — byte-identical
# to production — via Homebrew's ruby@3.3 (Ruby 4.x cannot run Jekyll 3.x).
#
# First-time setup:
#   brew install ruby@3.3
#   PATH=/opt/homebrew/opt/ruby@3.3/bin:$PATH bundle config set --local path vendor/bundle
#   PATH=/opt/homebrew/opt/ruby@3.3/bin:$PATH bundle install
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export PATH="/opt/homebrew/opt/ruby@3.3/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
# Jekyll's SCSS converter fails on em dashes without a UTF-8 locale.
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

if [ ! -d vendor/bundle ]; then
  echo "✗ Gems not installed. Run:  bundle install"
  exit 1
fi

if [ "${1:-build}" = "serve" ]; then
  echo "→ Serving at http://localhost:4000/polar-bears-2026/  (Ctrl-C to stop)"
  exec bundle exec jekyll serve --destination /tmp/pbpreview
fi

echo "→ Building with GitHub's Jekyll (3.10.0 / Liquid 4.0.4)…"
bundle exec jekyll build --destination /tmp/pbpreview

echo ""
echo "→ Checking the search index…"
python3 - <<'PY'
import json, sys
try:
    d = json.load(open('/tmp/pbpreview/search.json'))
except Exception as e:
    print(f"  ✗ search.json is not valid JSON: {e}")
    sys.exit(1)
bad = [x for x in d if not x.get('title', '').strip()]
print(f"  ✓ valid JSON, {len(d)} entries")
if bad:
    print(f"  ✗ {len(bad)} entry/entries with no title")
    sys.exit(1)
for x in sorted(d, key=lambda r: r['title']):
    print(f"    {x['kind']:<8} {x['title'][:34]:<34} {len(x.get('body',''))} chars")
PY

echo ""
echo "✓ Build clean. Safe to ./deploy.sh"

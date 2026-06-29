# Northern Lights & Polar Bears — 2026 Caravan site

A small static site (plain HTML/CSS, no build step) for the 2026 RV caravan up
Manitoba to Churchill. Hosted free on GitHub Pages.

**Live:** https://snthor-phd.github.io/polar-bears-2026/

## What's here

```
index.html            Trip hub (landing page)
itinerary/index.html  Full 31-day itinerary  ← ready
packing-list/         Placeholder            ← fill in before departure
contacts/             Placeholder
route-map/            Placeholder
deploy.sh             One command to publish / update
CUSTOM_DOMAIN.md      How to put it on your own domain
.nojekyll             Tells GitHub to serve the files as-is
```

## Publish or update

From this folder:

```bash
./deploy.sh
```

First run creates the public repo, pushes, and turns on GitHub Pages.
Every run after that just commits and pushes your changes — live in ~30–60s.

Prerequisites (one time): GitHub CLI signed in.
```bash
brew install gh        # if needed
gh auth login          # GitHub.com → SSH → your existing key
```

### Editing on the road
No laptop needed: open the repo on github.com, edit a file in the web editor,
and commit. Pages rebuilds automatically. Works fine over Starlink.

## Add a new document later

1. Make a folder with an `index.html` (copy a placeholder as a starting point).
2. Link it from the hub: in `index.html`, change that card's `class="card soon"`
   to `class="card"`, swap the `tag soon / Coming soon` to `tag ready / Ready`,
   and point the `href` at the new folder.
3. `./deploy.sh`

## Custom domain

See `CUSTOM_DOMAIN.md`.

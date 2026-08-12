# Northern Lights & Polar Bears — 2026 Caravan site

A small Jekyll site (plain HTML pages + a Markdown trip journal) for the 2026 RV
caravan up Manitoba to Churchill. Hosted free on GitHub Pages, which builds Jekyll
automatically — no local build step needed.

**Live:** https://snthor-phd.github.io/polar-bears-2026/

## Disclaimer

This is an independent, personal trip site created and maintained by SN Thorsen. It is not an official publication of, and does not represent, speak for, or reflect the views of, Airstream Club International (ACI/WBCCI), the caravan’s leadership, or any other club or organization. Nothing here is official caravan communication — rely on caravan leaders’ official communications for authoritative details. This site exists at the pleasure of its creator and may be edited, corrected, or taken down at any time without notice.

## What's here

```
index.html            Trip hub (landing page)
itinerary/            Full 31-day itinerary                        ← ready
packing-list/         Layer system, stop-by-stop temps, check-off  ← ready
                      list, printable PDF
route-map/            Leaflet map + date-driven trip progress      ← ready
teams/                All 21 volunteer team roles                  ← ready
photos/               Shared-album hub + shooting notes            ← ready*
articles/             Trip journal index (lists entries in _articles/)
_articles/            Journal entries — one Markdown file each
_layouts, _includes   Jekyll templates for the journal pages
contacts/             Placeholder            ← fill in before departure
deploy.sh             One command to publish / update
CUSTOM_DOMAIN.md      How to put it on your own domain

Note: do NOT add a .nojekyll file — the journal depends on GitHub Pages
running Jekyll. Journal entries get the article layout automatically via
the defaults rule in _config.yml.
```

### * One thing left to switch on: the photo album

`photos/` is built and live, but it needs the shared-album link before the
buttons do anything. Until then the page shows a friendly "goes live before
departure" notice instead of dead buttons.

1. In Google Photos, create an album (e.g. "Northern Lights & Polar Bears 2026").
2. Share it, turn on **Collaborate** (so caravanners can add their own photos),
   and copy the share link — it looks like `https://photos.app.goo.gl/…`.
3. Open `photos/index.html`, find the `SETUP` comment near the bottom, and paste
   the link between the quotes:

   ```js
   var ALBUM_URL = "https://photos.app.goo.gl/XXXXXXXXXXXX";
   ```

4. `./deploy.sh`

The QR code on that page points at the page itself, not the album, so it stays
valid no matter how many times the album link changes. Print it for the binder.

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

# Album cover

`make_cover.py` generates `assets/img/album-cover.jpg` — the cover for the
shared Google Photos album.

## Why it is built this way

Google Photos stamps the **album name** in large condensed white type across
the middle of the cover. The album's first cover was `album-title-card.jpg`,
a standalone title card with its own type in that same spot, so the two
collided and neither read (photographed on an iPhone 17 Pro, Sep 12 2026).

The phone header is a portrait box, so a landscape cover is scaled to match
**height** and cropped to roughly the **centre half of its width**. A cover
for this therefore needs to be horizontally uniform and vertically composed —
which is what this script draws:

- aurora curtains in the top third,
- spruce treeline along the bottom,
- a deliberately quiet middle band for the overlay,
- and no type of its own.

It is original generated art, so it carries none of the licensing limits that
keep the Frontiers North library off the shared album.

## Running it

    pip install numpy pillow
    python3 make_cover.py          # writes album-cover.jpg beside the script

Then copy the result to `assets/img/album-cover.jpg` and push. Installing it
as the actual album cover has to happen in the Google Photos iOS app — see
the album-cover section of `claude/site-status.md` in the project notes.

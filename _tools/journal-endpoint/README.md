# Trip journal intake endpoint

Lets caravan folks post journal entries themselves from `/articles/submit/`. Nothing to install
on their end — no Google account, no app. Entries queue for review; approving commits them here.

```
/articles/submit/  →  Apps Script doPost  →  Drive queue + email to Steve
                                                      ↓  (Steve taps Approve)
                           GitHub trees API → _articles/*.md + assets/img/journal/*.jpg
                                                      ↓
                                            GitHub Pages rebuild, entry live
```

Photos are resized to 1600 px and re-encoded **in the contributor's browser** before they are sent,
which also strips every scrap of metadata, GPS included. The original never leaves their phone.

## Files

- `Code.gs` — the whole web app. Paste into the Apps Script project; this copy is the source of record.
- `appsscript.json` — manifest (timezone, `webapp` access settings).

## Setting it up

1. [script.google.com](https://script.google.com) → **New project**, name it `NLPB Journal Intake`.
2. Paste `Code.gs` over the default `Code.gs`.
3. **Project Settings** → show `appsscript.json`, paste this repo's copy over it.
4. **Project Settings → Script properties**, add:
   - `GITHUB_TOKEN` — fine-grained PAT, repo `snthor-phd/polar-bears-2026` only,
     **Contents: Read and write**, expiry past Oct 13 2026. Nothing else.
   - `NOTIFY_EMAIL` — where submission notices go.
5. Run `setup` once from the editor (authorise when asked). The log prints the review-queue URL,
   including the `REVIEW_TOKEN` it minted. **Bookmark that URL** — it's the only key to the queue.
6. **Deploy → New deployment → Web app**: execute as *me*, access *Anyone*. Copy the `/exec` URL.
7. Put that URL into `articles/submit/index.html` as `JOURNAL_ENDPOINT`, commit, push.

## Redeploying after a code change

**Deploy → Manage deployments → edit (pencil) → Version: New version → Deploy.** Editing the
existing deployment keeps the same `/exec` URL, so the site needs no change. Creating a *new*
deployment instead mints a *new* URL and the form will keep posting at the old one.

## The review queue

`<web app URL>?t=<REVIEW_TOKEN>` — pending entries with photos, captions, and Approve / Reject.
The token is the whole access control, so treat the bookmark like a password. Approve and reject
links in the notification emails carry it too.

Rejected and published submissions are kept in Drive under `NLPB Journal Queue/` rather than
deleted, so a mis-tap is recoverable.

## Front matter it writes

```yaml
---
title: "Northern lights over The Pas"
date: 2026-09-19
byline: "Gail & Bruce Harrower"
place: "The Pas, MB"
summary: "first ~180 characters of the entry"
submitted: true
photos:
  - src: "/assets/img/journal/2026-09-19-northern-lights-over-the-pas-1.jpg"
    cap: "11:40 PM, straight up"
---
```

`_layouts/article.html` renders `byline`, `place`, the `photos` block and the "sent in from the
road" footer. Entries without those fields (the three hand-written ones) render exactly as before.

## Things that will bite

- **Submitted text is escaped, not trusted.** `<`, `>`, `{` and `}` become entities before the
  file is written — otherwise a submitted `<script>` would land on a public page, and a stray
  `{%` would break the Jekyll build. Liquid prints front-matter values unescaped, so the title,
  byline, place, summary and captions get the same treatment.
- **The date in the front matter is the contributor's, not the submission time.** Someone writing
  up Tuesday on Thursday sorts under Tuesday. That's the intent.
- **Slug collisions** get `-2` appended. A third entry with the same title and date would collide;
  hasn't been worth handling.
- **Approval is one person.** No signal, no publishing. If that becomes a problem, add a second
  address to `NOTIFY_EMAIL` handling or auto-publish on a timer.
- **Rate limit** is 12 submissions an hour, script-wide, tracked in `RECENT_SUBMITS`.

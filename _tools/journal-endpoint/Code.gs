/**
 * NL&PB 2026 caravan - trip journal intake endpoint.
 *
 * Deployed as a Google Apps Script web app. Two jobs:
 *   doPost  - accepts a submission from /articles/submit/, parks it in Drive, emails Steve
 *   doGet   - the review queue: approve publishes to GitHub, reject files it away
 *
 * Approving commits a Markdown file into _articles/ plus any photos into
 * assets/img/journal/, in one commit, and GitHub Pages rebuilds the site.
 *
 * Script properties this needs (Project Settings -> Script properties):
 *   GITHUB_TOKEN  fine-grained PAT, Contents read/write on snthor-phd/polar-bears-2026
 *   REVIEW_TOKEN  long random string; gates the review page and the approve links
 *   NOTIFY_EMAIL  where submission notices go
 *   QUEUE_FOLDER  (written automatically on first submission)
 */

var REPO   = 'snthor-phd/polar-bears-2026';
var BRANCH = 'main';
var SITE   = 'https://snthor-phd.github.io/polar-bears-2026';

var MAX_PHOTOS    = 3;
var MAX_PHOTO_B64 = 1600000;   // ~1.2 MB of JPEG per photo, generous for a 1600px file
var MAX_BODY      = 20000;
var MAX_PER_HOUR  = 12;

function props_() { return PropertiesService.getScriptProperties(); }

// ---------------------------------------------------------------- intake

function doPost(e) {
  try {
    var raw = (e && e.postData && e.postData.contents) || '';
    if (raw.length > 6000000) return json_({ ok: false, error: 'That is too much at once — try one photo fewer.' });

    var s;
    try { s = JSON.parse(raw); } catch (err) { return json_({ ok: false, error: 'Could not read that submission.' }); }

    // Spam trap. Bots fill hidden fields; answer ok so they stop retrying.
    if (s.website) return json_({ ok: true });
    if (Number(s.elapsed) < 3) return json_({ ok: false, error: 'That came through oddly fast — please try Send again.' });

    var name  = clean_(s.name, 80);
    var place = clean_(s.place, 80);
    var title = clean_(s.title, 110);
    var date  = clean_(s.date, 10);
    var body  = String(s.body == null ? '' : s.body).replace(/\r\n/g, '\n').trim();

    if (!name || !place || !title || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
      return json_({ ok: false, error: 'Something required was missing — check the fields and resend.' });
    }
    if (body.length < 20)       return json_({ ok: false, error: 'The entry needs a little more writing.' });
    if (body.length > MAX_BODY) return json_({ ok: false, error: 'That entry is very long — trim it a bit and resend.' });

    if (!underRateLimit_()) {
      return json_({ ok: false, error: 'Lots of entries just came in. Give it a few minutes and resend.' });
    }

    var photos = [];
    var incoming = Array.isArray(s.photos) ? s.photos.slice(0, MAX_PHOTOS) : [];
    for (var i = 0; i < incoming.length; i++) {
      var p = incoming[i] || {};
      var m = /^data:image\/(jpe?g|png);base64,([\s\S]+)$/.exec(String(p.data || ''));
      if (!m) continue;
      if (m[2].length > MAX_PHOTO_B64) {
        return json_({ ok: false, error: 'One photo is too large even after resizing. Remove it and resend.' });
      }
      photos.push({ b64: m[2], caption: clean_(p.caption, 140) });
    }

    var id = Utilities.formatDate(new Date(), 'America/Winnipeg', 'yyyyMMdd-HHmmss') + '-' +
             Math.random().toString(36).slice(2, 7);

    var folder = pendingFolder_().createFolder(id);
    folder.createFile(Utilities.newBlob(JSON.stringify({
      id: id, name: name, place: place, title: title, date: date, body: body,
      captions: photos.map(function (p) { return p.caption; }),
      received: new Date().toISOString()
    }, null, 2), 'application/json', 'entry.json'));

    photos.forEach(function (p, n) {
      folder.createFile(Utilities.newBlob(Utilities.base64Decode(p.b64), 'image/jpeg', 'photo-' + (n + 1) + '.jpg'));
    });

    notify_(id, { name: name, place: place, title: title, date: date, body: body }, photos);
    return json_({ ok: true });

  } catch (err) {
    try { MailApp.sendEmail(notifyEmail_(), 'Journal intake ERROR', String(err && err.stack || err)); } catch (e2) {}
    return json_({ ok: false, error: 'Something broke on our end. Steve has been told.' });
  }
}

function underRateLimit_() {
  var key = 'RECENT_SUBMITS';
  var now = Date.now();
  var list = [];
  try { list = JSON.parse(props_().getProperty(key) || '[]'); } catch (e) {}
  list = list.filter(function (t) { return now - t < 3600000; });
  if (list.length >= MAX_PER_HOUR) return false;
  list.push(now);
  props_().setProperty(key, JSON.stringify(list));
  return true;
}

// ---------------------------------------------------------------- review queue

function doGet(e) {
  var p = (e && e.parameter) || {};
  if (p.t !== props_().getProperty('REVIEW_TOKEN')) {
    return HtmlService.createHtmlOutput('<p style="font:16px system-ui;padding:30px">Not found.</p>');
  }
  if (p.action === 'approve') return page_(approve_(p.id));
  if (p.action === 'reject')  return page_(reject_(p.id));
  return page_(queueHtml_(p.t));
}

function queueHtml_(token) {
  var kids = pendingFolder_().getFolders();
  var out = [], count = 0;
  while (kids.hasNext() && count < 8) {
    var f = kids.next();
    var entry = readEntry_(f);
    if (!entry) continue;
    count++;
    var shots = f.getFilesByType('image/jpeg'), imgs = [], n = 0;
    while (shots.hasNext() && n < MAX_PHOTOS) {
      var b = shots.next().getBlob();
      imgs.push('<img src="data:image/jpeg;base64,' + Utilities.base64Encode(b.getBytes()) + '">');
      n++;
    }
    out.push(
      '<div class="e">' +
        '<div class="meta">' + esc_(entry.date) + ' &middot; ' + esc_(entry.place) + '</div>' +
        '<h2>' + esc_(entry.title) + '</h2>' +
        '<div class="by">' + esc_(entry.name) + '</div>' +
        '<div class="body">' + esc_(entry.body).replace(/\n/g, '<br>') + '</div>' +
        (imgs.length ? '<div class="shots">' + imgs.join('') + '</div>' : '') +
        '<div class="act">' +
          '<a class="go" href="?t=' + encodeURIComponent(token) + '&action=approve&id=' +
            encodeURIComponent(entry.id) + '">Approve &amp; publish</a>' +
          '<a class="no" href="?t=' + encodeURIComponent(token) + '&action=reject&id=' +
            encodeURIComponent(entry.id) + '">Reject</a>' +
        '</div>' +
      '</div>');
  }
  if (!out.length) out.push('<p class="empty">Nothing waiting. All caught up.</p>');
  return '<h1>Journal queue</h1>' + out.join('');
}

function page_(inner) {
  return HtmlService.createHtmlOutput(
    '<meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<style>' +
    'body{margin:0;padding:18px;background:#f4f1e9;color:#16202e;' +
      'font:16px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}' +
    'h1{font-size:1.3rem;margin:4px 0 18px}' +
    '.e{background:#fff;border:1px solid #e4ddcd;border-left:4px solid #36c98e;border-radius:14px;' +
      'padding:16px 18px;margin:0 0 16px}' +
    '.meta{font-size:.68rem;letter-spacing:.12em;text-transform:uppercase;font-weight:700;color:#6c7787}' +
    'h2{font-size:1.15rem;margin:6px 0 2px;line-height:1.2}' +
    '.by{font-size:.88rem;color:#6c7787;margin-bottom:10px}' +
    '.body{font-size:.95rem;color:#2b3a4d;max-height:14em;overflow:auto}' +
    '.shots{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:12px}' +
    '.shots img{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:8px;display:block}' +
    '.act{display:flex;gap:10px;margin-top:16px}' +
    '.act a{flex:1;text-align:center;text-decoration:none;font-weight:700;font-size:.92rem;' +
      'padding:12px 10px;border-radius:10px}' +
    '.go{background:#1c8a64;color:#fff}.no{background:#fff;color:#8d5a16;border:1px solid #e4ddcd}' +
    '.empty,.note{background:#fff;border:1px solid #e4ddcd;border-radius:14px;padding:18px 20px}' +
    '.note a{color:#1c8a64;font-weight:700}' +
    '</style>' + inner);
}

function reject_(id) {
  var f = findPending_(id);
  if (!f) return '<div class="note"><p>That one is not in the queue any more.</p></div>';
  f.moveTo(sub_(queueRoot_(), 'rejected'));
  return '<div class="note"><p>Rejected and filed away. Nothing was published.</p>' +
         '<p><a href="javascript:history.back()">Back to the queue</a></p></div>';
}

// ---------------------------------------------------------------- publish

function approve_(id) {
  var f = findPending_(id);
  if (!f) return '<div class="note"><p>That one is not in the queue any more — probably already published.</p></div>';

  var entry = readEntry_(f);
  if (!entry) return '<div class="note"><p>Could not read that submission.</p></div>';

  if (!props_().getProperty('GITHUB_TOKEN')) {
    return '<div class="note"><p><strong>Not published \u2014 no GitHub token yet.</strong></p>' +
      '<p>The entry is still sitting safely in the queue. Add a fine-grained token as the script ' +
      'property <code>GITHUB_TOKEN</code> (repo contents, read and write), then approve again.</p>' +
      '<p><a href="javascript:history.back()">Back to the queue</a></p></div>';
  }

  var stem = entry.date + '-' + slug_(entry.title);
  if (ghExists_('_articles/' + stem + '.md')) stem = stem + '-2';

  var files = [], photos = [], n = 0;
  var shots = f.getFilesByType('image/jpeg');
  while (shots.hasNext() && n < MAX_PHOTOS) {
    var blob = shots.next().getBlob();
    var path = 'assets/img/journal/' + stem + '-' + (n + 1) + '.jpg';
    files.push({ path: path, bytes: blob.getBytes() });
    photos.push({ src: '/' + path, cap: (entry.captions && entry.captions[n]) || '' });
    n++;
  }
  files.push({ path: '_articles/' + stem + '.md', text: markdown_(entry, photos) });

  var sha;
  try {
    sha = commit_(files, 'Journal entry from ' + entry.name + ': ' + entry.title);
  } catch (err) {
    // Nothing has moved yet, so the submission stays in the queue and can be
    // approved again once whatever GitHub objected to is fixed.
    return '<div class="note"><p><strong>Not published.</strong> GitHub refused the commit:</p>' +
      '<p style="font-size:.85rem;color:#8d5a16;word-break:break-word">' +
      esc_(String((err && err.message) || err)) + '</p>' +
      '<p>The entry is still in the queue \u2014 fix that and approve again. A 401 &ldquo;Bad ' +
      'credentials&rdquo; means the token is missing, mistyped or expired.</p>' +
      '<p><a href="javascript:history.back()">Back to the queue</a></p></div>';
  }
  f.moveTo(sub_(queueRoot_(), 'published'));

  var url = SITE + '/articles/' + stem + '/';
  return '<div class="note"><p><strong>Published.</strong> GitHub is rebuilding &mdash; give it a minute.</p>' +
         '<p><a href="' + url + '">' + esc_(entry.title) + '</a></p>' +
         '<p style="font-size:.8rem;color:#6c7787">commit ' + esc_(sha.slice(0, 7)) + '</p>' +
         '<p><a href="javascript:history.back()">Back to the queue</a></p></div>';
}

function markdown_(entry, photos) {
  var lines = [];
  lines.push('---');
  lines.push('title: ' + yaml_(textSafe_(entry.title)));
  lines.push('date: ' + entry.date);
  lines.push('byline: ' + yaml_(textSafe_(entry.name)));
  lines.push('place: ' + yaml_(textSafe_(entry.place)));
  lines.push('summary: ' + yaml_(textSafe_(summary_(entry.body))));
  lines.push('submitted: true');
  if (photos.length) {
    lines.push('photos:');
    photos.forEach(function (p) {
      lines.push('  - src: ' + yaml_(p.src));
      lines.push('    cap: ' + yaml_(textSafe_(p.cap)));
    });
  }
  lines.push('---');
  lines.push(safeBody_(entry.body));
  lines.push('');
  return lines.join('\n');
}

/**
 * Contributors write plain text. Two things must not survive into a Jekyll build:
 * raw HTML (this is a public site, and Liquid prints front-matter values
 * unescaped) and Liquid tags (they would break the build). Angle brackets become
 * entities; braces become numeric entities, which render as the literal
 * character but are invisible to Liquid.
 *
 * textSafe_ is for single-line values (title, byline, place, summary, captions);
 * safeBody_ does the same and also normalises paragraph breaks.
 */
function textSafe_(t) {
  return String(t == null ? '' : t)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\{/g, '&#123;')
    .replace(/\}/g, '&#125;');
}

function safeBody_(t) {
  return textSafe_(t).replace(/\n{3,}/g, '\n\n').trim();
}

function summary_(body) {
  var t = String(body).replace(/\s+/g, ' ').trim();
  if (t.length <= 180) return t;
  var cut = t.slice(0, 180);
  var sp = cut.lastIndexOf(' ');
  return (sp > 120 ? cut.slice(0, sp) : cut) + '…';
}

function yaml_(s) {
  return '"' + String(s == null ? '' : s).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, ' ') + '"';
}

function slug_(title) {
  var s = String(title).toLowerCase()
    .replace(/[‘’“”']/g, '')
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  if (!s) s = 'entry';
  return s.split('-').slice(0, 8).join('-').slice(0, 60).replace(/-+$/, '');
}

// ---------------------------------------------------------------- GitHub

function gh_(method, path, payload) {
  var res = UrlFetchApp.fetch('https://api.github.com/repos/' + REPO + path, {
    method: method,
    contentType: 'application/json',
    headers: {
      Authorization: 'Bearer ' + props_().getProperty('GITHUB_TOKEN'),
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28'
    },
    payload: payload ? JSON.stringify(payload) : null,
    muteHttpExceptions: true
  });
  var code = res.getResponseCode(), text = res.getContentText();
  if (code >= 300) throw new Error('GitHub ' + method + ' ' + path + ' -> ' + code + ' ' + text.slice(0, 300));
  return text ? JSON.parse(text) : {};
}

function ghExists_(path) {
  var res = UrlFetchApp.fetch('https://api.github.com/repos/' + REPO + '/contents/' + path + '?ref=' + BRANCH, {
    headers: {
      Authorization: 'Bearer ' + props_().getProperty('GITHUB_TOKEN'),
      Accept: 'application/vnd.github+json'
    },
    muteHttpExceptions: true
  });
  return res.getResponseCode() === 200;
}

/** One commit carrying every file, via the git trees API. */
function commit_(files, message) {
  var ref  = gh_('get', '/git/ref/heads/' + BRANCH);
  var base = ref.object.sha;
  var baseCommit = gh_('get', '/git/commits/' + base);

  var tree = files.map(function (f) {
    var blob = f.text != null
      ? gh_('post', '/git/blobs', { content: f.text, encoding: 'utf-8' })
      : gh_('post', '/git/blobs', { content: Utilities.base64Encode(f.bytes), encoding: 'base64' });
    return { path: f.path, mode: '100644', type: 'blob', sha: blob.sha };
  });

  var newTree = gh_('post', '/git/trees', { base_tree: baseCommit.tree.sha, tree: tree });
  var commit  = gh_('post', '/git/commits', { message: message, tree: newTree.sha, parents: [base] });
  gh_('patch', '/git/refs/heads/' + BRANCH, { sha: commit.sha });
  return commit.sha;
}

// ---------------------------------------------------------------- Drive plumbing

function queueRoot_() {
  var id = props_().getProperty('QUEUE_FOLDER');
  if (id) { try { return DriveApp.getFolderById(id); } catch (e) {} }
  var f = DriveApp.createFolder('NLPB Journal Queue');
  props_().setProperty('QUEUE_FOLDER', f.getId());
  return f;
}
function sub_(parent, name) {
  var it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}
function pendingFolder_() { return sub_(queueRoot_(), 'pending'); }

function findPending_(id) {
  if (!id) return null;
  var it = pendingFolder_().getFoldersByName(id);
  return it.hasNext() ? it.next() : null;
}
function readEntry_(folder) {
  var it = folder.getFilesByName('entry.json');
  if (!it.hasNext()) return null;
  try { return JSON.parse(it.next().getBlob().getDataAsString()); } catch (e) { return null; }
}

// ---------------------------------------------------------------- notification

function notifyEmail_() {
  return props_().getProperty('NOTIFY_EMAIL') || Session.getEffectiveUser().getEmail();
}

function notify_(id, entry, photos) {
  var token = props_().getProperty('REVIEW_TOKEN');
  var q = ScriptApp.getService().getUrl() + '?t=' + encodeURIComponent(token);
  var body =
    '<div style="font:16px/1.55 ui-sans-serif,system-ui,-apple-system,sans-serif;color:#16202e">' +
    '<p style="font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;font-weight:700;color:#6c7787">' +
      esc_(entry.date) + ' &middot; ' + esc_(entry.place) +
      (photos.length ? ' &middot; ' + photos.length + ' photo' + (photos.length > 1 ? 's' : '') : '') + '</p>' +
    '<h2 style="margin:4px 0 2px;font-size:1.2rem">' + esc_(entry.title) + '</h2>' +
    '<p style="margin:0 0 14px;color:#6c7787">' + esc_(entry.name) + '</p>' +
    '<div style="background:#f4f1e9;border-radius:12px;padding:14px 16px;white-space:pre-wrap">' +
      esc_(entry.body) + '</div>' +
    '<p style="margin:20px 0 0">' +
      '<a href="' + q + '&action=approve&id=' + encodeURIComponent(id) + '" ' +
        'style="display:inline-block;background:#1c8a64;color:#fff;text-decoration:none;font-weight:700;' +
        'padding:13px 24px;border-radius:10px">Approve &amp; publish</a>' +
    '</p>' +
    '<p style="margin:14px 0 0;font-size:.9rem"><a href="' + q + '" style="color:#1c8a64;font-weight:600">' +
      'Open the review queue</a> to see the photos and captions first.</p>' +
    '</div>';

  MailApp.sendEmail({
    to: notifyEmail_(),
    subject: 'Journal entry from ' + entry.name + ' — ' + entry.title,
    htmlBody: body
  });
}

// ---------------------------------------------------------------- helpers

function clean_(v, max) {
  return String(v == null ? '' : v)
    .replace(/[ -]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, max);
}
function esc_(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

/** Run once from the editor to mint a review token and check the wiring. */
function setup() {
  var p = props_();
  if (!p.getProperty('REVIEW_TOKEN')) {
    p.setProperty('REVIEW_TOKEN',
      Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, '').slice(0, 8));
  }
  if (!p.getProperty('NOTIFY_EMAIL')) p.setProperty('NOTIFY_EMAIL', Session.getEffectiveUser().getEmail());
  queueRoot_();
  Logger.log('Review queue: ' + ScriptApp.getService().getUrl() + '?t=' + p.getProperty('REVIEW_TOKEN'));
  Logger.log('GITHUB_TOKEN set: ' + (p.getProperty('GITHUB_TOKEN') ? 'yes' : 'NO - add it in Project Settings'));
}

#!/usr/bin/env python3
"""Refresh _data/bear_alert.json from the Town of Churchill's weekly Polar Bear Alert report.

The Town of Churchill posts Manitoba Conservation's "Polar Bear Alert Program Weekly
Activity Report" as a one-page PDF on
https://www.churchill.ca/p/polar-bear-safety-stats — one link per week, newest first.

This script: fetches that page, picks the newest report link for the current season,
downloads the PDF, pulls the numbers out of it, and rewrites _data/bear_alert.json
(only when something changed). The hub's Bear Watch card renders from that JSON at
Jekyll build time — no client-side JavaScript, no CORS, no mixed-content problem
(the PDFs are served over plain http).

Run by .github/workflows/bear-alert.yml on a weekly schedule; safe to run by hand:

    python3 _tools/bear-alert/fetch.py          # refresh if newer
    python3 _tools/bear-alert/fetch.py --force  # rewrite even if unchanged

Exit codes: 0 = ok (changed or not), 1 = could not fetch/parse (the old JSON is left alone).
"""
import io
import json
import re
import sys
import urllib.request
from datetime import date, datetime
from html import unescape
from pathlib import Path

PAGE = "https://www.churchill.ca/p/polar-bear-safety-stats"
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "_data" / "bear_alert.json"
UA = {"User-Agent": "polar-bears-2026 caravan site (bear-alert refresh; github.com/snthor-phd/polar-bears-2026)"}

# Each line of the report, keyed the way the JSON will carry it. pypdf drops stray
# spaces inside words ("p olar", "Bea r", "of :"), so all matching is done on the
# text with EVERY whitespace character removed, against space-free patterns.
FIELDS = {
    "week_reports":    "Numberofpolarbearoccurrencereportsthisweek",
    "season_reports":  "Totalnumberofpolarbearoccurrencereportstodate",
    "season_handled":  "Totalnumberofbearshandledtodate",
    "week_flown":      "Polarbearsflownoutdirectlythisweek",
    "season_released": "Totalnumberofbearsreleasedthisyear",
    "pbhf_start":      "NumberofbearsinthePBHFatthestartoftheweek",
    "pbhf_in":         "NumberofbearsplacedintothePBHFthisweek",
    "pbhf_out":        "NumberofbearsreleasedfromthePBHFthisweek",
    "pbhf_end":        "NumberofbearsinthePBHFattheendoftheweek",
}
MONTH = "(January|February|March|April|May|June|July|August|September|October|November|December)"


def get(url, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def newest_report(html, year):
    """Return (url, label) of the newest weekly report link for `year`, by the date in its label."""
    best = None
    for m in re.finditer(r'<a\s+[^>]*href="([^"]+\.pdf)"[^>]*>(.*?)</a>', html, re.I | re.S):
        href, label = m.group(1), re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", m.group(2)))).strip()
        # Labels look like "September 21, 2026"; the href may or may not carry the year.
        d = None
        try:
            d = datetime.strptime(label.replace("\xa0", " "), "%B %d, %Y").date()
        except ValueError:
            pass
        if d is None or d.year != year:
            continue
        if not href.startswith("http"):
            href = "http://" + href.lstrip("/")
        href = href.replace(" ", "%20")
        if best is None or d > best[0]:
            best = (d, href, label)
    return best


def pdf_text(data):
    from pypdf import PdfReader  # pip install pypdf
    reader = PdfReader(io.BytesIO(data))
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def parse(text):
    squashed = re.sub(r"\s+", "", text)
    out = {}
    for key, phrase in FIELDS.items():
        m = re.search(re.escape(phrase) + r"(\d+)", squashed, re.I)
        if not m:
            raise ValueError(f"could not find '{key}' in report text")
        out[key] = int(m.group(1))
    m = re.search(r"ReportfortheWeekof:" + MONTH + r"(\d{1,2})to" + MONTH + r"(\d{1,2}),(\d{4})"
                  r"DateCompleted:" + MONTH + r"(\d{1,2}),(\d{4})", squashed, re.I)
    if not m:
        raise ValueError("could not find the report week / completion date")
    m1, d1, m2, d2, y, cm, cd, cy = m.groups()
    out["week_of"] = f"{m1.title()} {int(d1)} to {m2.title()} {int(d2)}, {y}"
    out["report_date"] = datetime.strptime(f"{cm.title()} {cd} {cy}", "%B %d %Y").date().isoformat()
    return out


def main():
    force = "--force" in sys.argv
    year = date.today().year
    try:
        html = get(PAGE)
        hit = newest_report(html, year)
        if hit is None:
            print(f"no {year} report links found on {PAGE}", file=sys.stderr)
            return 1
        _, url, label = hit
        rec = parse(pdf_text(get(url, binary=True)))
    except Exception as e:  # network, parse, layout change — leave the old JSON alone
        print(f"bear-alert refresh failed: {e}", file=sys.stderr)
        return 1

    rec.update({
        "report_url": url,
        "report_label": label,
        "source_page": PAGE,
        "fetched": date.today().isoformat(),
    })
    old = json.loads(OUT.read_text()) if OUT.exists() else {}
    same = all(old.get(k) == v for k, v in rec.items() if k != "fetched")
    if same and not force:
        print(f"unchanged — latest report is still {label}")
        return 0
    OUT.write_text(json.dumps(rec, indent=2) + "\n")
    print(f"updated {OUT.relative_to(ROOT)} from {label}: "
          f"{rec['week_reports']} this week, {rec['season_reports']} to date, {rec['pbhf_end']} in the PBHF")
    return 0


if __name__ == "__main__":
    sys.exit(main())

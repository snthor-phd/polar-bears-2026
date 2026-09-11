# Itinerary map build

Generates `assets/data/route.js` (what `/route-map/` draws), `assets/docs/nlpb-2026-itinerary.kml`
(Google My Maps import) and `assets/docs/nlpb-2026-itinerary.gpx` (Garmin / RV GPS).

- `data.py` — the overnight stops (campground entrances) and the venues, with coordinates. Edit here.
- `route2.py` — fetches road geometry for each driving leg from the public OSRM server into `legs.json`.
  Only needs re-running if a stop moves. (Apple's bundled Python can't TLS-handshake with that host,
  so it shells out to `curl`.)
- `build.py` — simplifies the geometry and writes the three output files. Run from this directory:
  `python3 build.py`

Jekyll ignores `_tools/`, so none of this ships.

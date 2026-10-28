# Week 10 — US-17: Check my field

- In Live mode, **Check my field** lets a user tap the corners of any field in NRW. The browser reads
  the latest Sentinel-2 and Sentinel-1 images for that polygon straight from Planetary Computer and
  shows the same conditions card as the monitored fields, read aloud in English or German.
- No backend: STAC, SAS tokens and COG blobs all allow CORS, so this runs on GitHub Pages (ADR 0017).
- Weather comes from the nearest monitored field within 15 km, because DWD opendata has no CORS.
- Real check on a field near Soest (28 Oct 2026): clear image 6 days old, NDVI 0.55, radar 2 days
  old, in about 10 s.
- Limits: inside NRW, 0.5–500 ha, no risk score or winter checks for drawn fields.

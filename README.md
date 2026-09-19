---
title: Run Router
emoji: 🏃
colorFrom: red
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# Run Router

A running route generator for Singapore. Given a starting point and a target distance, it generates several candidate loop routes on the real street network, ranked by closeness to the target distance.

## API

`POST /routes/stream` — streams routes as JSON as they are generated.

Body:
```json
{
  "lat": 1.3521,
  "lon": 103.8198,
  "distance_km": 10,
  "tolerance_m": 1000,
  "max_attempts": 15,
  "num_candidates": 5
}
```
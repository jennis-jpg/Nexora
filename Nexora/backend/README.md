# SeaSentry AI — Combined Backend (Person A + Person B + Person C)

This merges Person A's **Geofencing & Prediction Engine**, Person B's
**Safety & Alerting Systems**, and Person C's **Voice Alert Layer** into
a single FastAPI app with one shared package layout, one
`requirements.txt`, and one Coast Guard alert pipeline.

## Layout
```
backend/
├── main.py                     # single FastAPI app, mounts every router + static audio
├── geofence.py                  # Person A — boundary math (dead reckoning, ETA, risk)
├── models.py                    # shared Pydantic models (prediction + SOS/awake/alerts)
├── database.py                  # in-memory store for awake checks + incident timeline
├── routes/
│   ├── predict.py               # Person A — /predict, /boundary-check, /risk-status*
│   ├── sos.py                   # Person B — /sos
│   ├── awake_check.py           # Person B — /awake-check/*
│   ├── report.py                # Person B — /crossing-report/{boat_id}
│   └── voice.py                 # Person C — /voice/generate-alert-text, /voice/alert-audio/*
├── services/
│   ├── prediction_service.py    # Person A's engine logic + boat state store
│   ├── sos_service.py           # shared create_alert() Coast Guard pipeline
│   ├── awake_service.py         # awake-check creation/confirmation/escalation
│   ├── scheduler.py             # APScheduler jobs (hourly checks, 1-min sweep)
│   ├── weather_service.py       # weather lookup for incident reports
│   ├── report_service.py        # PDF incident report generation
│   └── voice_service.py         # Person C — risk-based alert text + audio resolution
├── sound/                        # Person C's pre-recorded Kannada MP3s, served at /audio/*
│   ├── kannada_safe.mp3
│   ├── kannada_warning.mp3
│   ├── kannada_danger.mp3
│   └── alarm.mp3
└── requirements.txt
```

## What changed in the merge

**Person A + B** (unchanged from the previous merge):
- Person A's flat `main.py`/`geofence.py` were restructured into the
  `routes/` + `services/` pattern Person B already used.
- Person A's `BoatInput`/`BoundaryCheckInput` models moved into the shared
  `models.py`.
- `services/prediction_service.py` calls
  `services/sos_service.create_alert(..., AlertType.BOUNDARY_CROSSING)`
  the moment a boat's risk transitions into `"High"`, so SOS, missed
  awake checks, and high-risk boundary crossings all funnel through the
  same Coast Guard dispatch pipeline and the same incident timeline
  (picked up automatically by `/crossing-report/{boat_id}`).
- Alerts only fire on the *transition* into High risk, not on every
  `/predict` poll.
- **Added for demo/testing**: `POST /awake-check/trigger-now/{boat_id}`
  manually creates a pending awake check for any boat_id, bypassing the
  hourly scheduler. Without it, the very first awake check for
  `BOAT001`/`BOAT002`/`BOAT003` wouldn't exist until 60 minutes after
  the server starts (`next_run_time=None` in `scheduler.py`), making it
  impractical to demo the pending → confirm/expire → escalate flow.
  This endpoint is intentionally unauthenticated for hackathon
  convenience — consider removing or gating it before a real
  deployment.

**Person C — newly merged in this pass**:
- `app.py`'s two routes became `routes/voice.py`, mounted under the
  `/voice` prefix (`/voice/generate-alert-text`, `/voice/alert-audio/{alert_id}`)
  to keep them consistent with the rest of the API and avoid clashing
  with the top-level `/` health check.
- `alert_generator.py`'s risk-word normalization and message-building
  logic became `services/voice_service.py`.
- The `sound/` MP3s are now served from the combined app itself via
  `StaticFiles` at `/audio/*` (was previously a separate standalone app).
- **Deliberately left out of the merge**: `voice_engine.py` (pyttsx3 +
  playsound, for speaking alerts out loud on a local machine),
  `translator.py` (calls the Groq API *at import time*, which would
  crash app startup without a `GROQ_API_KEY` set, and isn't imported by
  `app.py` at all), and `language_config.py` (a single unused
  variable). None of these were actually called by Person C's API
  routes — the routes only ever returned JSON with `alert_text` and an
  `audio_url` for the frontend to play. If real-time translation or
  local TTS is wanted later, they can be wired in as a proper service
  rather than a module with side effects at import time.
- Colorama console-coloring (used only for local terminal output in
  Person C's original script, never read by the API response) was
  dropped from the merged version.

## Quickstart
```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Then open http://localhost:8000/docs.

## Endpoints

| Method | Path | Owner | Purpose |
|---|---|---|---|
| GET | `/` , `/health` | — | Health check |
| GET | `/boundary-points` | Person A | Raw B1–B6 coordinates |
| POST | `/boundary-check` | Person A | Stateless position → distance/side/ETA/risk |
| POST | `/predict` | Person A | Full prediction + track + crossing detection; raises alert on new High risk |
| GET | `/risk-status/{boat_id}` | Person A | Last known status for one boat |
| GET | `/risk-status` | Person A | Fleet-wide status (coastguard dashboard) |
| POST | `/sos` | Person B | Manual SOS trigger |
| GET | `/awake-check/status/{boat_id}` | Person B | Latest awake-check status |
| POST | `/awake-check/ack` | Person B | Operator confirms awake |
| POST | `/awake-check/trigger-now/{boat_id}` | Person B (debug) | Manually create a pending awake check, bypassing the hourly scheduler — for demo/testing only |
| GET | `/crossing-report/{boat_id}` | Person B | Downloadable incident PDF |
| POST | `/voice/generate-alert-text` | Person C | Risk-based alert text + audio_url (English/Kannada) |
| GET | `/voice/alert-audio/{alert_id}` | Person C | Resolve audio_url for a risk-level keyword |
| GET | `/audio/{filename}` | Person C | Static Kannada MP3 files |

## Known caveat (inherited from Person A)
Crossing detection uses the *nearest* boundary segment of B1–B6. Near the
vertices (B2–B5) the nearest segment can switch as the boat moves, which
can occasionally register a false crossing. Fine for demo paths that
cross cleanly through the middle of a segment; a same-segment-across-checks
guard is already implemented in `check_crossing()`, so this mostly matters
right at the vertices.

## Known caveat (inherited from Person C)
`/voice/alert-audio/{alert_id}` takes a risk-level keyword in the
`alert_id` path segment (e.g. `safe`, `warning`, `danger`), not the
`alert_id` string returned by `/voice/generate-alert-text`. This matches
Person C's original design exactly, but the naming is confusing — worth
renaming to `/voice/alert-audio/{risk}` in a future revision.

## Still owned by others
Person D (Frontend) has their own app and is not mounted into this
backend.

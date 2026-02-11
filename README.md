# VibeCode Workout Web App

Local browser-based workout app with a Python backend.

## Features

- Workout page at `/` and completed history at `/completed`
- Session controls: start, pause, resume, back, skip, reset
- End-of-workout `Confirm Complete`
- Completion moves workouts from `workouts.json` to `completed_workouts.json`
- Date-aware sorting (today first, upcoming next, older later)

## Prerequisites

- Python 3.9+

## Setup and Run

```bash
cd /Users/rioneldmello/Desktop/VibeCode/python-workout-app
python3 -m pip install -r requirements.txt
python3 web_app.py
```

Open `http://127.0.0.1:8000` in your browser.

## Run with Script

```bash
./run_workout_app.sh
```

## Project Files

- Active workouts: `workouts.json`
- Completed workouts: `completed_workouts.json`
- Web server entrypoint: `web_app.py`

## Tests

Install test dependencies and run the suite:

```bash
python3 -m pip install -r requirements.txt -r requirements-dev.txt
python3 -m playwright install chromium
pytest -q
```

Or use:

```bash
./scripts/test.sh
```

## Workout JSON Requirements

Each workout object in `workouts.json` should include:

- `id`
- `title`
- `date` (`YYYY-MM-DD`)
- `rounds`
- `default_rest_seconds`
- `exercises` with `name`, `work_seconds`, and `instructions`

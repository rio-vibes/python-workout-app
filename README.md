# Python Workout App (GUI)

A desktop workout timer app built with Python + Tkinter.

## Features

- GUI workout screen with large timer and clear exercise instructions
- Loads multiple workouts from `workouts.json`
- Supports selecting any workout from the config
- Shows rounds, work timers, breaks, reps, and next exercise
- Instructions render as larger bullet points for readability
- Plays a sound alert when phases complete (system bell)
- Tracks completed workouts via `Confirm Complete`
- Stores completion history in `completed_workouts.json` with Day, Date, Title
- Dedicated `Completed Workouts` tab for workout history

## Run

```bash
cd /Users/rioneldmello/Desktop/VibeCode/python-workout-app
python3 app.py
```

Or:

```bash
cd /Users/rioneldmello/Desktop/VibeCode/python-workout-app
./run_workout_app.sh
```

## Config Rules

Every workout in `workouts.json` must include:

- `id`
- `title` (without day names)
- `rounds`
- `default_rest_seconds`
- `exercises` (each with `name`, `work_seconds`, `instructions`)

# LLM Prompt: Generate Weekly Workout Config JSON

Use this prompt in a separate chat to generate the next week's **pending workouts** for the app.

## What you provide to the LLM

1. Your system prompt (trainer + injury context).
2. Your `completed_workouts.json` content.

## Copy/Paste Prompt

You are generating workouts for a Python workout timer app.
Return valid JSON only. No markdown code fences.

Important planning constraints:
- Use completed workout history to avoid repeating the exact same session structure too often.
- Build progression week-over-week while respecting injury constraints.
- Create workouts for one week only.

Schema requirements:
- Top-level object must include `meta` and `workouts`.
- `workouts` must be an array (can be empty only for full rest week).
- Every workout must include:
  - `id`: unique lowercase slug with underscores
  - `title`: workout title (do not include weekday name in title)
  - `date`: scheduled date in `YYYY-MM-DD`
  - `rounds`: integer >= 1
  - `default_rest_seconds`: integer >= 0
  - `exercises`: non-empty array
- Every exercise must include:
  - `name`: exercise title
  - `work_seconds`: integer > 0
  - `instructions`: array of 3-5 bullet strings with setup, execution, and safety cues
- Optional exercise fields:
  - `rest_seconds`: integer >= 0
  - `reps`: string or integer

Return JSON in this exact structure:

{
  "meta": {
    "name": "Weekly Plan",
    "version": 1,
    "notes": "optional"
  },
  "workouts": [
    {
      "id": "example_strength_a",
      "title": "Strength Foundation A",
      "date": "2026-02-11",
      "description": "optional",
      "rounds": 3,
      "default_rest_seconds": 45,
      "exercises": [
        {
          "name": "Exercise Name",
          "work_seconds": 40,
          "rest_seconds": 20,
          "reps": "10-12",
          "instructions": [
            "Setup cue",
            "Execution cue",
            "Breathing or tempo cue",
            "Safety cue"
          ]
        }
      ]
    }
  ]
}

## Usage in this app

1. Save generated JSON as `workouts.json`.
2. App auto-sorts workouts by date priority (today first, then upcoming, then older).
3. When you click `Confirm Complete`, that workout is moved from `workouts.json` into `completed_workouts.json`.

# LLM Prompt: Generate Workout Config JSON

Use this prompt in a separate chat to generate workout configs for the app.

## Copy/Paste Prompt

You are generating workout configs for a Python workout timer app.
Return valid JSON only. No markdown code fences.

Requirements:
- Top-level JSON object must include `meta` and `workouts`.
- `workouts` must be an array with at least one workout.
- Every workout must include:
  - `id`: short unique slug (lowercase with underscores)
  - `title`: human-readable workout title (do not include day names like Monday/Tuesday)
  - `rounds`: integer >= 1
  - `default_rest_seconds`: integer >= 0
  - `exercises`: non-empty array
- Every exercise must include:
  - `name`: exercise title
  - `work_seconds`: integer > 0
  - `instructions`: array of 3-5 bullet strings with clear setup, execution, and safety cues
- Optional exercise fields:
  - `rest_seconds`: integer >= 0 (overrides workout default)
  - `reps`: string or integer (e.g., `12`, `10-12`, `AMRAP`)

Generate workouts suitable for home training with clear and safe instructions.
Keep each workout between 4 and 10 exercises.

Return JSON in this exact structure:

{
  "meta": {
    "name": "Workout Config",
    "version": 1,
    "notes": "optional notes"
  },
  "workouts": [
    {
      "id": "example_slug",
      "title": "Example Workout Title",
      "description": "optional",
      "rounds": 2,
      "default_rest_seconds": 20,
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

## Usage

1. Save generated JSON as `workouts.json` in this project directory.
2. Start the app and click `Reload Config`, or restart the app.
3. Choose any workout from the dropdown and press `Start`.
4. At the end, click `Confirm Complete` to log Day, Date, and Title.

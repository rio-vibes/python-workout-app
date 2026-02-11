#!/usr/bin/env python3
"""Local browser-based workout app backend."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).parent
WORKOUTS_PATH = BASE_DIR / "workouts.json"
COMPLETED_PATH = BASE_DIR / "completed_workouts.json"

app = Flask(__name__, template_folder="templates", static_folder="static")


def _load_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _parse_workout_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def _valid_workout(workout: dict[str, Any]) -> bool:
    try:
        title_ok = isinstance(workout.get("title"), str) and workout["title"].strip()
        date_value = workout.get("date")
        date_ok = isinstance(date_value, str) and date_value.strip()
        if date_ok:
            _parse_workout_date(date_value)
        exercises = workout.get("exercises")
        exercises_ok = isinstance(exercises, list) and len(exercises) > 0
        return bool(title_ok and date_ok and exercises_ok)
    except Exception:
        return False


def _sort_workouts_by_schedule(workouts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    today = date.today()

    def key(workout: dict[str, Any]) -> tuple[int, int]:
        workout_date = _parse_workout_date(str(workout.get("date", "1900-01-01")))
        if workout_date == today:
            return (0, 0)
        if workout_date > today:
            return (1, (workout_date - today).days)
        return (2, (today - workout_date).days)

    return sorted(workouts, key=key)


def _load_workouts_doc() -> dict[str, Any]:
    doc = _load_json(
        WORKOUTS_PATH,
        {
            "meta": {
                "name": "Workout Config",
                "version": 1,
                "notes": "Generated workouts",
            },
            "workouts": [],
        },
    )
    if not isinstance(doc, dict):
        doc = {"meta": {}, "workouts": []}

    workouts = doc.get("workouts", [])
    if not isinstance(workouts, list):
        workouts = []

    filtered = [w for w in workouts if isinstance(w, dict) and _valid_workout(w)]
    sorted_workouts = _sort_workouts_by_schedule(filtered)
    doc["workouts"] = sorted_workouts
    return doc


def _load_completed() -> list[dict[str, Any]]:
    completed = _load_json(COMPLETED_PATH, [])
    if not isinstance(completed, list):
        return []

    normalized: list[dict[str, Any]] = []
    for row in completed:
        if not isinstance(row, dict):
            continue
        normalized.append(
            {
                "day": str(row.get("day", "")),
                "date": str(row.get("date", "")),
                "title": str(row.get("title", "")),
                "scheduled_date": str(row.get("scheduled_date", "")),
                "completed_at": str(row.get("completed_at", "")),
                "workout": row.get("workout", {}),
            }
        )
    return normalized


def _state_payload() -> dict[str, Any]:
    workouts_doc = _load_workouts_doc()
    completed = _load_completed()
    return {
        "meta": workouts_doc.get("meta", {}),
        "workouts": workouts_doc.get("workouts", []),
        "completed_workouts": completed,
    }


@app.route("/")
def workout_page() -> str:
    return render_template("workout.html")


@app.route("/completed")
def completed_page() -> str:
    return render_template("completed.html")


@app.route("/api/state", methods=["GET"])
def api_state() -> Any:
    payload = _state_payload()
    return jsonify(payload)


@app.route("/api/complete", methods=["POST"])
def api_complete_workout() -> Any:
    payload = request.get_json(silent=True) or {}
    workout_id = str(payload.get("id", "")).strip()
    scheduled_date = str(payload.get("date", "")).strip()

    if not workout_id:
        return jsonify({"error": "Missing workout id"}), 400

    workouts_doc = _load_workouts_doc()
    workouts = workouts_doc.get("workouts", [])
    if not isinstance(workouts, list):
        workouts = []

    target_index = -1
    for idx, workout in enumerate(workouts):
        if workout.get("id") != workout_id:
            continue
        if scheduled_date and str(workout.get("date", "")) != scheduled_date:
            continue
        target_index = idx
        break

    if target_index < 0:
        return jsonify({"error": "Workout not found"}), 404

    workout = workouts.pop(target_index)
    now = datetime.now()
    completed = _load_completed()
    completed.append(
        {
            "day": now.strftime("%A"),
            "date": now.strftime("%Y-%m-%d"),
            "title": str(workout.get("title", "Untitled Workout")),
            "scheduled_date": str(workout.get("date", "")),
            "completed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "workout": workout,
        }
    )

    workouts_doc["workouts"] = _sort_workouts_by_schedule(workouts)
    _save_json(WORKOUTS_PATH, workouts_doc)
    _save_json(COMPLETED_PATH, completed)

    return jsonify(_state_payload())


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)

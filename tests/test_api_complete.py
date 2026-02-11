from __future__ import annotations

import json
from datetime import date

from conftest import build_workout


def test_complete_missing_id_returns_400(client, data_store, default_workouts):
    data_store.write(workouts=default_workouts)

    response = client.post("/api/complete", json={})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Missing workout id"


def test_complete_unknown_workout_returns_404(client, data_store, default_workouts):
    data_store.write(workouts=default_workouts)

    response = client.post("/api/complete", json={"id": "does_not_exist"})
    assert response.status_code == 404
    assert response.get_json()["error"] == "Workout not found"


def test_complete_moves_workout_and_persists(client, data_store):
    today = date.today()
    target = build_workout(workout_id="w1", title="Target", workout_date=today)
    other = build_workout(workout_id="w2", title="Other", workout_date=today)
    data_store.write(workouts=[target, other], completed=[])

    response = client.post(
        "/api/complete",
        json={"id": "w1", "date": today.isoformat()},
    )
    assert response.status_code == 200

    payload = response.get_json()
    remaining_ids = [w["id"] for w in payload["workouts"]]
    assert remaining_ids == ["w2"]

    completed = payload["completed_workouts"]
    assert len(completed) == 1
    entry = completed[0]
    assert entry["title"] == "Target"
    assert entry["scheduled_date"] == today.isoformat()
    assert entry["workout"]["id"] == "w1"
    assert entry["day"]
    assert entry["date"]
    assert entry["completed_at"]

    persisted_workouts = json.loads(data_store.workouts_path.read_text(encoding="utf-8"))
    persisted_completed = json.loads(data_store.completed_path.read_text(encoding="utf-8"))

    assert [w["id"] for w in persisted_workouts["workouts"]] == ["w2"]
    assert len(persisted_completed) == 1
    assert persisted_completed[0]["title"] == "Target"

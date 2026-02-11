from __future__ import annotations

from datetime import date, timedelta

from conftest import build_workout


def test_api_state_returns_expected_payload_shape(client, data_store, default_workouts):
    data_store.write(workouts=default_workouts)

    response = client.get("/api/state")
    assert response.status_code == 200

    payload = response.get_json()
    assert isinstance(payload, dict)
    assert "meta" in payload
    assert "workouts" in payload
    assert "completed_workouts" in payload
    assert isinstance(payload["workouts"], list)
    assert isinstance(payload["completed_workouts"], list)


def test_api_state_sorts_by_today_upcoming_older(client, data_store):
    today = date.today()
    workouts = [
        build_workout(workout_id="older", title="Older", workout_date=today - timedelta(days=2)),
        build_workout(workout_id="upcoming", title="Upcoming", workout_date=today + timedelta(days=2)),
        build_workout(workout_id="today", title="Today", workout_date=today),
    ]
    data_store.write(workouts=workouts)

    response = client.get("/api/state")
    assert response.status_code == 200

    ordered = [w["id"] for w in response.get_json()["workouts"]]
    assert ordered == ["today", "upcoming", "older"]


def test_api_state_filters_invalid_workouts(client, data_store):
    today = date.today()
    valid = build_workout(workout_id="valid", title="Valid", workout_date=today)

    invalid_missing_title = {
        "id": "bad_missing_title",
        "date": today.isoformat(),
        "rounds": 1,
        "default_rest_seconds": 5,
        "exercises": [{"name": "X", "work_seconds": 5, "instructions": ["a"]}],
    }
    invalid_bad_date = build_workout(
        workout_id="bad_date",
        title="Bad Date",
        workout_date=today,
    )
    invalid_bad_date["date"] = "2026-99-99"

    invalid_empty_exercises = build_workout(
        workout_id="empty_ex",
        title="Empty",
        workout_date=today,
        exercises=[],
    )

    data_store.write(
        workouts=[valid, invalid_missing_title, invalid_bad_date, invalid_empty_exercises]
    )

    response = client.get("/api/state")
    assert response.status_code == 200
    payload = response.get_json()
    remaining_ids = [w["id"] for w in payload["workouts"]]
    assert remaining_ids == ["valid"]

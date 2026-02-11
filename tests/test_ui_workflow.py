from __future__ import annotations

from datetime import date, timedelta

from conftest import build_workout


def _to_seconds(clock_text: str) -> int:
    minutes, seconds = clock_text.strip().split(":")
    return int(minutes) * 60 + int(seconds)


def _seed_ui_workouts(data_store) -> None:
    today = date.today()
    workouts = [
        build_workout(
            workout_id="w_today",
            title="Today Session",
            workout_date=today,
            rounds=1,
            default_rest_seconds=20,
            exercises=[
                {
                    "name": "Dynamic Warm-Up Walk",
                    "work_seconds": 14,
                    "rest_seconds": 20,
                    "reps": "1",
                    "instructions": [
                        "Start easy.",
                        "Keep posture tall.",
                        "Stay controlled.",
                    ],
                },
                {
                    "name": "Easy Conversation Run",
                    "work_seconds": 14,
                    "rest_seconds": 0,
                    "reps": "1",
                    "instructions": [
                        "Run smooth.",
                        "Keep cadence steady.",
                        "Breathe easy.",
                    ],
                },
            ],
        ),
        build_workout(
            workout_id="w_tomorrow",
            title="Tomorrow Session",
            workout_date=today + timedelta(days=1),
            rounds=1,
            default_rest_seconds=10,
            exercises=[
                {
                    "name": "Mobility Reset",
                    "work_seconds": 10,
                    "rest_seconds": 5,
                    "reps": "1",
                    "instructions": ["Move smoothly.", "Stay tall.", "No pain."],
                }
            ],
        ),
    ]
    data_store.write(workouts=workouts, completed=[])


def test_scheduled_workouts_are_visible_in_left_panel(page, live_server, data_store):
    _seed_ui_workouts(data_store)
    page.goto(live_server)

    page.wait_for_selector('[data-testid="workout-item"]')
    assert page.locator('[data-testid="workout-item"]').count() >= 2


def test_back_to_plan_and_resume_controls(page, live_server, data_store):
    _seed_ui_workouts(data_store)
    page.goto(live_server)

    page.click('[data-testid="start-btn"]')
    page.wait_for_timeout(300)
    page.click('[data-testid="back-to-plan-btn"]')

    root_class = page.locator('[data-testid="workout-root"]').get_attribute("class") or ""
    assert "in-session" not in root_class

    page.click('[data-testid="resume-from-plan-btn"]')
    page.wait_for_timeout(300)

    root_class = page.locator('[data-testid="workout-root"]').get_attribute("class") or ""
    assert "in-session" in root_class
    assert page.locator('[data-testid="pause-btn"]').is_enabled()
    assert page.locator('[data-testid="resume-btn"]').is_disabled()


def test_paused_status_message_clears_after_resume(page, live_server, data_store):
    _seed_ui_workouts(data_store)
    page.goto(live_server)

    page.click('[data-testid="start-btn"]')
    page.wait_for_timeout(300)
    page.click('[data-testid="back-to-plan-btn"]')

    paused_text = page.locator('[data-testid="status-msg"]').inner_text().strip()
    assert "Workout paused. Review plan, then resume when ready." in paused_text

    page.click('[data-testid="resume-from-plan-btn"]')
    page.wait_for_timeout(300)

    status_text = page.locator('[data-testid="status-msg"]').inner_text().strip()
    assert status_text == ""


def test_skip_does_not_accelerate_timer_ticks(page, live_server, data_store):
    _seed_ui_workouts(data_store)
    page.goto(live_server)

    page.click('[data-testid="start-btn"]')
    page.wait_for_timeout(400)
    page.click('[data-testid="skip-btn"]')

    page.wait_for_timeout(300)
    phase = page.locator('[data-testid="phase-badge"]').inner_text().strip().upper()
    assert phase == "REST"

    t0 = _to_seconds(page.locator('[data-testid="timer-text"]').inner_text())
    page.wait_for_timeout(2400)
    t1 = _to_seconds(page.locator('[data-testid="timer-text"]').inner_text())

    delta = t0 - t1
    assert 1 <= delta <= 3, f"Timer ticked unexpectedly fast after skip: delta={delta}"


def test_completion_moves_workout_to_completed_page(page, live_server, data_store):
    today = date.today()
    workouts = [
        build_workout(
            workout_id="tiny",
            title="Tiny Session",
            workout_date=today,
            rounds=1,
            default_rest_seconds=0,
            exercises=[
                {
                    "name": "Quick Step",
                    "work_seconds": 1,
                    "rest_seconds": 0,
                    "reps": "1",
                    "instructions": ["Go.", "Finish.", "Done."],
                }
            ],
        )
    ]
    data_store.write(workouts=workouts, completed=[])

    page.goto(live_server)
    page.click('[data-testid="start-btn"]')

    confirm = page.locator('[data-testid="confirm-btn"]')
    for _ in range(30):
        if confirm.is_enabled():
            break
        page.wait_for_timeout(200)
    assert confirm.is_enabled(), "Confirm Complete button never became enabled"

    confirm.click()

    page.wait_for_timeout(400)
    assert page.locator('[data-testid="workout-item"]').count() == 0

    page.goto(f"{live_server}/completed")
    page.wait_for_selector('[data-testid="completed-table-body"] tr')

    completed_body_text = page.locator('[data-testid="completed-table-body"]').inner_text()
    assert "Tiny Session" in completed_body_text

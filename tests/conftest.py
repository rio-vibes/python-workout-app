from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from threading import Thread
from typing import Any

import pytest
from playwright.sync_api import Browser, Page, sync_playwright
from werkzeug.serving import make_server

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import web_app


@dataclass
class DataStore:
    workouts_path: Path
    completed_path: Path

    def write(
        self,
        *,
        workouts: list[dict[str, Any]] | None = None,
        completed: list[dict[str, Any]] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> None:
        workouts_doc = {
            "meta": meta
            or {
                "name": "Test Workouts",
                "version": 1,
                "notes": "pytest fixture data",
            },
            "workouts": workouts or [],
        }
        self.workouts_path.write_text(json.dumps(workouts_doc, indent=2), encoding="utf-8")
        self.completed_path.write_text(json.dumps(completed or [], indent=2), encoding="utf-8")


@pytest.fixture
def data_store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> DataStore:
    workouts_path = tmp_path / "workouts.json"
    completed_path = tmp_path / "completed_workouts.json"

    monkeypatch.setattr(web_app, "WORKOUTS_PATH", workouts_path)
    monkeypatch.setattr(web_app, "COMPLETED_PATH", completed_path)

    store = DataStore(workouts_path=workouts_path, completed_path=completed_path)
    store.write()
    return store


@pytest.fixture
def client(data_store: DataStore):
    return web_app.app.test_client()


@pytest.fixture
def live_server(data_store: DataStore):
    server = make_server("127.0.0.1", 0, web_app.app)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


@pytest.fixture(scope="session")
def browser() -> Browser:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser: Browser) -> Page:
    context = browser.new_context()
    page = context.new_page()
    try:
        yield page
    finally:
        context.close()


def build_workout(
    *,
    workout_id: str,
    title: str,
    workout_date: date,
    description: str = "",
    rounds: int = 1,
    default_rest_seconds: int = 10,
    exercises: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    exercise_list = (
        [
            {
                "name": "Exercise A",
                "work_seconds": 10,
                "rest_seconds": 5,
                "reps": "10",
                "instructions": [
                    "Setup cue",
                    "Execution cue",
                    "Safety cue",
                ],
            }
        ]
        if exercises is None
        else exercises
    )
    return {
        "id": workout_id,
        "title": title,
        "date": workout_date.isoformat(),
        "description": description,
        "rounds": rounds,
        "default_rest_seconds": default_rest_seconds,
        "exercises": exercise_list,
    }


@pytest.fixture
def default_workouts() -> list[dict[str, Any]]:
    today = date.today()
    return [
        build_workout(
            workout_id="today_strength",
            title="Today Strength",
            workout_date=today,
            description="Today workout",
        ),
        build_workout(
            workout_id="tomorrow_cardio",
            title="Tomorrow Cardio",
            workout_date=today + timedelta(days=1),
            description="Upcoming workout",
        ),
        build_workout(
            workout_id="yesterday_mobility",
            title="Yesterday Mobility",
            workout_date=today - timedelta(days=1),
            description="Older workout",
        ),
    ]

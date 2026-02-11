#!/usr/bin/env python3
"""Workout timer GUI app driven by JSON workout configs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any


class WorkoutApp:
    def __init__(self, root: tk.Tk, config_path: Path) -> None:
        self.root = root
        self.root.title("Workout Screen")
        self.root.geometry("1100x760")
        self.root.minsize(980, 680)
        self.root.configure(bg="#071A2E")

        self.config_path = config_path
        self.completed_log_path = Path(__file__).parent / "completed_workouts.json"
        self.config: dict[str, Any] = {}
        self.workouts: list[dict[str, Any]] = []
        self.completed_workouts: list[dict[str, Any]] = self._load_completed_workouts()

        self.current_workout: dict[str, Any] | None = None
        self.current_phase = "work"
        self.current_exercise_index = 0
        self.current_round = 1
        self.time_remaining = 0
        self.running = False
        self.paused = False
        self.timer_job: str | None = None
        self.pending_completion_confirmation = False

        self._configure_styles()
        self._build_ui()
        self.load_config_file(self.config_path)

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        bg_main = "#071A2E"
        bg_panel = "#0E2B4A"
        bg_panel_alt = "#12385E"
        text_main = "#EAF4FF"
        text_muted = "#A7C4DE"
        blue_accent = "#1D7FE3"
        green_accent = "#1FC77A"

        style.configure(".", background=bg_main, foreground=text_main)
        style.configure("TFrame", background=bg_main)
        style.configure("TLabel", background=bg_main, foreground=text_main)
        style.configure("TLabelframe", background=bg_panel, foreground=green_accent, bordercolor=blue_accent)
        style.configure("TLabelframe.Label", background=bg_panel, foreground=green_accent)

        style.configure(
            "TButton",
            background=blue_accent,
            foreground="#FFFFFF",
            borderwidth=0,
            focusthickness=0,
            padding=(12, 8),
        )
        style.map(
            "TButton",
            background=[("active", green_accent), ("disabled", "#3C5673")],
            foreground=[("disabled", "#D2DFEE")],
        )

        style.configure("TNotebook", background=bg_main, borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=bg_panel_alt,
            foreground=text_main,
            padding=(14, 8),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", blue_accent), ("active", "#2494F3")],
            foreground=[("selected", "#FFFFFF")],
        )

        style.configure(
            "TCombobox",
            fieldbackground=bg_panel_alt,
            background=bg_panel_alt,
            foreground=text_main,
            arrowcolor=green_accent,
        )

        style.configure(
            "Treeview",
            background=bg_panel,
            fieldbackground=bg_panel,
            foreground=text_main,
            rowheight=28,
            bordercolor=blue_accent,
        )
        style.configure(
            "Treeview.Heading",
            background=blue_accent,
            foreground="#FFFFFF",
            relief="flat",
        )
        style.map("Treeview", background=[("selected", "#1A6AC0")], foreground=[("selected", "#FFFFFF")])

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(self.root)
        notebook.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        workout_tab = ttk.Frame(notebook)
        history_tab = ttk.Frame(notebook)
        notebook.add(workout_tab, text="Workout")
        notebook.add(history_tab, text="Completed Workouts")

        workout_tab.columnconfigure(0, weight=1)
        workout_tab.rowconfigure(1, weight=1)

        controls = ttk.Frame(workout_tab, padding=10)
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure(1, weight=1)

        ttk.Label(controls, text="Workout:").grid(row=0, column=0, sticky="w")

        self.workout_var = tk.StringVar()
        self.workout_combo = ttk.Combobox(
            controls,
            textvariable=self.workout_var,
            state="readonly",
            width=50,
        )
        self.workout_combo.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        self.workout_combo.bind("<<ComboboxSelected>>", self._on_workout_selected)

        ttk.Button(controls, text="Reload Config", command=self.reload_config).grid(
            row=0, column=2, padx=4
        )
        ttk.Button(controls, text="Open Config", command=self.open_config_dialog).grid(
            row=0, column=3, padx=4
        )

        display = ttk.Frame(workout_tab, padding=(12, 2, 12, 10))
        display.grid(row=1, column=0, sticky="nsew")
        display.columnconfigure(0, weight=1)
        display.columnconfigure(1, weight=1)
        display.rowconfigure(5, weight=1)

        self.phase_var = tk.StringVar(value="Ready")
        self.timer_var = tk.StringVar(value="00:00")
        self.name_var = tk.StringVar(value="Select a workout to begin")
        self.detail_var = tk.StringVar(value="")
        self.round_var = tk.StringVar(value="Round: -")
        self.next_var = tk.StringVar(value="Next: -")

        ttk.Label(display, textvariable=self.phase_var, font=("Helvetica", 24, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(display, textvariable=self.round_var, font=("Helvetica", 16)).grid(
            row=0, column=1, sticky="e"
        )

        ttk.Label(display, textvariable=self.timer_var, font=("Helvetica", 96, "bold")).grid(
            row=1, column=0, columnspan=2, sticky="n", pady=(6, 0)
        )

        ttk.Label(display, textvariable=self.name_var, font=("Helvetica", 32, "bold"), anchor="center").grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0)
        )
        ttk.Label(
            display,
            textvariable=self.detail_var,
            font=("Helvetica", 16),
            wraplength=900,
            anchor="center",
            justify="center",
        ).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 8))

        instructions_label = ttk.Label(display, text="Instructions", font=("Helvetica", 16, "bold"))
        instructions_label.grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 4))

        self.instructions = tk.Text(
            display,
            height=13,
            wrap="word",
            font=("Helvetica", 18),
            bg="#0E2B4A",
            fg="#EAF4FF",
            insertbackground="#EAF4FF",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#1D7FE3",
            highlightcolor="#1FC77A",
        )
        self.instructions.grid(row=5, column=0, columnspan=2, sticky="nsew")
        self.instructions.configure(state="disabled")

        ttk.Label(display, textvariable=self.next_var, font=("Helvetica", 15, "bold")).grid(
            row=6, column=1, sticky="se", pady=(8, 0)
        )

        actions = ttk.Frame(workout_tab, padding=(12, 0, 12, 12))
        actions.grid(row=2, column=0, sticky="ew")

        self.start_btn = ttk.Button(actions, text="Start", command=self.start_workout)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.pause_btn = ttk.Button(actions, text="Pause", command=self.pause_workout, state="disabled")
        self.pause_btn.grid(row=0, column=1, padx=5)

        self.resume_btn = ttk.Button(actions, text="Resume", command=self.resume_workout, state="disabled")
        self.resume_btn.grid(row=0, column=2, padx=5)

        self.back_btn = ttk.Button(actions, text="Back", command=self.back_phase, state="disabled")
        self.back_btn.grid(row=0, column=3, padx=5)

        self.skip_btn = ttk.Button(actions, text="Skip", command=self.skip_phase, state="disabled")
        self.skip_btn.grid(row=0, column=4, padx=5)

        self.reset_btn = ttk.Button(actions, text="Reset", command=self.reset_workout, state="disabled")
        self.reset_btn.grid(row=0, column=5, padx=5)

        self.confirm_complete_btn = ttk.Button(
            actions,
            text="Confirm Complete",
            command=self.confirm_workout_complete,
            state="disabled",
        )
        self.confirm_complete_btn.grid(row=0, column=6, padx=5)

        history_tab.columnconfigure(0, weight=1)
        history_tab.rowconfigure(0, weight=1)

        history_frame = ttk.LabelFrame(history_tab, text="Completed Workouts", padding=(12, 8, 12, 12))
        history_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

        cols = ("day", "date", "title")
        self.history_tree = ttk.Treeview(history_frame, columns=cols, show="headings")
        self.history_tree.heading("day", text="Day")
        self.history_tree.heading("date", text="Date")
        self.history_tree.heading("title", text="Title")
        self.history_tree.column("day", width=180, anchor="w")
        self.history_tree.column("date", width=180, anchor="w")
        self.history_tree.column("title", width=620, anchor="w")
        self.history_tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self._refresh_history_tree()

    def open_config_dialog(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select workout config",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if selected:
            self.load_config_file(Path(selected))

    def reload_config(self) -> None:
        self.load_config_file(self.config_path)

    def load_config_file(self, path: Path) -> None:
        try:
            raw = path.read_text(encoding="utf-8")
            loaded = json.loads(raw)
            workouts = loaded.get("workouts", [])
            if not isinstance(workouts, list):
                raise ValueError("Config must contain a 'workouts' array")

            for workout in workouts:
                self._validate_workout(workout)

            self.config_path = path
            self.config = loaded
            self.workouts = self._sort_workouts_by_schedule(workouts)
            self.config["workouts"] = self.workouts
            self._refresh_workout_dropdown(select_index=0)
            self.root.title(f"Workout Screen - {self.config_path.name}")
        except Exception as err:
            messagebox.showerror("Config Error", f"Could not load config:\n{path}\n\n{err}")

    def _validate_workout(self, workout: dict[str, Any]) -> None:
        title = workout.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ValueError("Each workout requires a non-empty 'title'")
        workout_date = workout.get("date")
        if not isinstance(workout_date, str) or not workout_date.strip():
            raise ValueError(f"Workout '{title}' requires a 'date' in YYYY-MM-DD format")
        self._parse_workout_date(workout_date)

        exercises = workout.get("exercises")
        if not isinstance(exercises, list) or not exercises:
            raise ValueError(f"Workout '{title}' must include exercises")

        for ex in exercises:
            if not isinstance(ex.get("name"), str) or not ex["name"].strip():
                raise ValueError(f"Workout '{title}' has an exercise without a valid name")
            duration = ex.get("work_seconds", ex.get("duration_seconds"))
            if not isinstance(duration, int) or duration <= 0:
                raise ValueError(f"Exercise '{ex.get('name', '?')}' needs positive work_seconds")
            instructions = ex.get("instructions")
            if isinstance(instructions, list):
                if not instructions or not all(isinstance(item, str) and item.strip() for item in instructions):
                    raise ValueError(f"Exercise '{ex.get('name', '?')}' needs non-empty instruction bullet strings")
            elif not isinstance(instructions, str) or not instructions.strip():
                raise ValueError(f"Exercise '{ex.get('name', '?')}' needs instructions text or bullet list")

    def _workout_label(self, workout: dict[str, Any]) -> str:
        workout_id = workout.get("id", "")
        title = workout.get("title", "Untitled")
        workout_date = workout.get("date", "0000-00-00")
        base = f"{workout_date} | {title}"
        return f"{base} ({workout_id})" if workout_id else base

    def _parse_workout_date(self, value: str) -> Any:
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as err:
            raise ValueError(f"Invalid workout date '{value}'. Use YYYY-MM-DD.") from err

    def _sort_workouts_by_schedule(self, workouts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        today = datetime.now().date()

        def sort_key(workout: dict[str, Any]) -> tuple[int, int]:
            workout_date = self._parse_workout_date(str(workout.get("date", "")))
            if workout_date == today:
                return (0, 0)
            if workout_date > today:
                return (1, (workout_date - today).days)
            return (2, (today - workout_date).days)

        return sorted(workouts, key=sort_key)

    def _refresh_workout_dropdown(self, select_index: int = 0) -> None:
        names = [self._workout_label(w) for w in self.workouts]
        self.workout_combo["values"] = names

        if not names:
            self.workout_var.set("")
            self.current_workout = None
            self.reset_workout()
            return

        bounded_index = max(0, min(select_index, len(self.workouts) - 1))
        self.workout_combo.current(bounded_index)
        self.current_workout = self.workouts[bounded_index]
        self.reset_workout()

    def _select_workout_by_index(self, idx: int) -> None:
        self.current_workout = self.workouts[idx]
        self.reset_workout()

    def _on_workout_selected(self, _event: Any = None) -> None:
        idx = self.workout_combo.current()
        if idx >= 0:
            self._select_workout_by_index(idx)

    def start_workout(self) -> None:
        if not self.current_workout:
            return
        self.stop_timer()
        self.running = True
        self.paused = False
        self.pending_completion_confirmation = False
        self.current_phase = "work"
        self.current_exercise_index = 0
        self.current_round = 1
        self._set_phase_time()
        self._update_controls()
        self._render()
        self._schedule_tick()

    def pause_workout(self) -> None:
        if not self.running:
            return
        self.paused = True
        self.stop_timer()
        self._update_controls()

    def resume_workout(self) -> None:
        if not self.running or not self.paused:
            return
        self.paused = False
        self._update_controls()
        self._schedule_tick()

    def reset_workout(self) -> None:
        self.stop_timer()
        self.running = False
        self.paused = False
        self.pending_completion_confirmation = False
        self.current_phase = "work"
        self.current_exercise_index = 0
        self.current_round = 1
        self.time_remaining = 0
        self._update_controls()
        self._render()

    def skip_phase(self) -> None:
        if not self.running:
            return
        self.stop_timer()
        self.time_remaining = 0
        self._advance_phase()

    def back_phase(self) -> None:
        if not self.current_workout:
            return
        if not (self.running or self.paused):
            return

        self.stop_timer()

        # First phase of the workout cannot go further back; restart that phase timer.
        if self.current_phase == "work" and self.current_exercise_index == 0 and self.current_round == 1:
            self._set_phase_time()
        elif self.current_phase == "rest":
            self.current_phase = "work"
            self._set_phase_time()
        else:
            prev_idx, prev_round = self._previous_exercise_position()
            self.current_exercise_index = prev_idx
            self.current_round = prev_round
            prev_rest = self._current_rest_seconds()
            if prev_rest > 0:
                self.current_phase = "rest"
                self.time_remaining = prev_rest
            else:
                self.current_phase = "work"
                self._set_phase_time()

        self._render()
        if self.running and not self.paused:
            self._schedule_tick()
        self._update_controls()

    def _previous_exercise_position(self) -> tuple[int, int]:
        if not self.current_workout:
            return (0, 1)

        exercises = self.current_workout["exercises"]
        if self.current_exercise_index > 0:
            return (self.current_exercise_index - 1, self.current_round)

        if self.current_round > 1:
            return (len(exercises) - 1, self.current_round - 1)

        return (0, 1)

    def stop_timer(self) -> None:
        if self.timer_job:
            try:
                self.root.after_cancel(self.timer_job)
            except tk.TclError:
                pass
            self.timer_job = None

    def _schedule_tick(self) -> None:
        # Ensure exactly one active scheduled callback at any time.
        self.stop_timer()
        self.timer_job = self.root.after(1000, self._tick)

    def _tick(self) -> None:
        # This callback is now consumed; a fresh one will be scheduled if needed.
        self.timer_job = None
        if not self.running or self.paused:
            return
        self.time_remaining -= 1
        if self.time_remaining <= 0:
            self._advance_phase()
            return
        self._render()
        self._schedule_tick()

    def _advance_phase(self) -> None:
        if not self.current_workout:
            return

        self._play_alert()

        if self.current_phase == "work":
            rest = self._current_rest_seconds()
            if rest > 0:
                self.current_phase = "rest"
                self.time_remaining = rest
                self._render()
                self._schedule_tick()
                return
            self._advance_to_next_exercise()
            return

        self._advance_to_next_exercise()

    def _advance_to_next_exercise(self) -> None:
        if not self.current_workout:
            return
        exercises = self.current_workout["exercises"]
        rounds = int(self.current_workout.get("rounds", 1))

        self.current_exercise_index += 1
        if self.current_exercise_index >= len(exercises):
            self.current_exercise_index = 0
            self.current_round += 1

        if self.current_round > rounds:
            self.running = False
            self.paused = False
            self.time_remaining = 0
            self.pending_completion_confirmation = True
            self.phase_var.set("Complete")
            self.timer_var.set("00:00")
            self.name_var.set("Workout complete")
            self.detail_var.set("Confirm to store this completed session.")
            self.next_var.set("Next: -")
            self._set_instructions(["Session finished.", "Click Confirm Complete to save Day, Date, and Title."])
            self._update_controls()
            self._play_alert()
            return

        self.current_phase = "work"
        self._set_phase_time()
        self._render()
        self._schedule_tick()

    def confirm_workout_complete(self) -> None:
        if not self.pending_completion_confirmation or not self.current_workout:
            return

        now = datetime.now()
        selected_index = self.workout_combo.current()
        if selected_index < 0 or selected_index >= len(self.workouts):
            selected_index = 0

        completed_workout = self.workouts[selected_index]
        entry = {
            "day": now.strftime("%A"),
            "date": now.strftime("%Y-%m-%d"),
            "title": str(completed_workout.get("title", "Untitled Workout")),
            "scheduled_date": str(completed_workout.get("date", "")),
            "completed_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "workout": completed_workout,
        }
        self.completed_workouts.append(entry)
        removed_workout = self.workouts.pop(selected_index)
        try:
            self._save_completed_workouts()
            self._save_current_workouts()
        except Exception as err:
            messagebox.showerror("Save Error", f"Could not save completed workout:\n{err}")
            self.completed_workouts.pop()
            self.workouts.insert(selected_index, removed_workout)
            return

        self.pending_completion_confirmation = False
        self._refresh_history_tree()
        self.workouts = self._sort_workouts_by_schedule(self.workouts)
        self._refresh_workout_dropdown(select_index=selected_index)
        self.detail_var.set("Completed session saved.")
        self._set_instructions(["Saved.", "Choose another workout and press Start."])
        self._update_controls()

    def _set_phase_time(self) -> None:
        if not self.current_workout:
            self.time_remaining = 0
            return
        ex = self.current_workout["exercises"][self.current_exercise_index]
        self.time_remaining = int(ex.get("work_seconds", ex.get("duration_seconds", 0)))

    def _current_rest_seconds(self) -> int:
        if not self.current_workout:
            return 0
        ex = self.current_workout["exercises"][self.current_exercise_index]
        fallback = int(self.current_workout.get("default_rest_seconds", 0))
        return int(ex.get("rest_seconds", fallback))

    def _format_clock(self, total_seconds: int) -> str:
        minutes, seconds = divmod(max(0, total_seconds), 60)
        return f"{minutes:02d}:{seconds:02d}"

    def _instruction_bullets(self, exercise: dict[str, Any]) -> list[str]:
        raw = exercise.get("instructions", "")
        if isinstance(raw, list):
            return [item.strip() for item in raw if isinstance(item, str) and item.strip()]

        text = str(raw).strip()
        if not text:
            return ["No instructions provided."]

        lines = [ln.strip(" -*\t") for ln in text.splitlines() if ln.strip()]
        if len(lines) > 1:
            return lines
        return [part.strip() for part in text.split(".") if part.strip()]

    def _render(self) -> None:
        if not self.current_workout:
            self.phase_var.set("Ready")
            self.timer_var.set("00:00")
            self.round_var.set("Round: -")
            self.name_var.set("No workouts scheduled")
            self.detail_var.set("Add dated workouts to workouts.json and reload config.")
            self.next_var.set("Next: -")
            self._set_instructions(["No workout available.", "Generate a new week plan and reload config."])
            return

        exercises = self.current_workout["exercises"]
        ex = exercises[self.current_exercise_index]
        rounds = int(self.current_workout.get("rounds", 1))

        if self.running:
            phase_label = "WORK" if self.current_phase == "work" else "REST"
            self.phase_var.set(phase_label)
        elif self.pending_completion_confirmation:
            self.phase_var.set("Complete")
        else:
            self.phase_var.set("Ready")

        self.timer_var.set(self._format_clock(self.time_remaining))
        self.round_var.set(f"Round: {self.current_round}/{rounds}")

        if self.current_phase == "rest" and self.running:
            self.name_var.set("Break")
            self.detail_var.set("Breathe. Reset for the next movement.")
            next_ex = self._peek_next_exercise()
            self.next_var.set(f"Next: {next_ex.get('name', '-')}")
            self._set_instructions(
                [
                    "Keep moving lightly and breathe slowly.",
                    "Reset posture: shoulders down, rib cage stacked, core lightly braced.",
                    "Check setup for the next movement before timer hits zero.",
                ]
            )
        else:
            self.name_var.set(ex.get("name", "Unnamed"))
            reps = ex.get("reps")
            details = [f"Date: {self.current_workout.get('date', '-')}", f"Work: {int(ex.get('work_seconds', ex.get('duration_seconds', 0)))} sec"]
            if reps:
                details.append(f"Reps: {reps}")
            if ex.get("rest_seconds") is not None:
                details.append(f"Rest after: {ex['rest_seconds']} sec")
            self.detail_var.set(" | ".join(details))

            next_ex = self._peek_next_exercise()
            self.next_var.set(f"Next: {next_ex.get('name', '-')}")
            self._set_instructions(self._instruction_bullets(ex))

    def _peek_next_exercise(self) -> dict[str, Any]:
        if not self.current_workout:
            return {}
        exercises = self.current_workout["exercises"]
        idx = (self.current_exercise_index + 1) % len(exercises)
        return exercises[idx]

    def _set_instructions(self, bullets: list[str]) -> None:
        self.instructions.configure(state="normal")
        self.instructions.delete("1.0", "end")
        for bullet in bullets:
            self.instructions.insert("end", f"\u2022 {bullet}\n")
        self.instructions.configure(state="disabled")

    def _play_alert(self) -> None:
        try:
            import winsound  # type: ignore

            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            return
        except Exception:
            pass

        try:
            self.root.bell()
        except Exception:
            pass

    def _load_completed_workouts(self) -> list[dict[str, Any]]:
        if not self.completed_log_path.exists():
            return []
        try:
            data = json.loads(self.completed_log_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                normalized: list[dict[str, Any]] = []
                for row in data:
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
        except Exception:
            return []
        return []

    def _save_completed_workouts(self) -> None:
        self.completed_log_path.write_text(
            json.dumps(self.completed_workouts, indent=2),
            encoding="utf-8",
        )

    def _save_current_workouts(self) -> None:
        self.config["workouts"] = self.workouts
        self.config_path.write_text(
            json.dumps(self.config, indent=2),
            encoding="utf-8",
        )

    def _refresh_history_tree(self) -> None:
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        for entry in reversed(self.completed_workouts):
            self.history_tree.insert(
                "",
                "end",
                values=(entry.get("day", ""), entry.get("date", ""), entry.get("title", "")),
            )

    def _update_controls(self) -> None:
        if self.running and not self.paused:
            self.start_btn.configure(state="disabled")
            self.pause_btn.configure(state="normal")
            self.resume_btn.configure(state="disabled")
            self.back_btn.configure(state="normal")
            self.skip_btn.configure(state="normal")
            self.reset_btn.configure(state="normal")
            self.confirm_complete_btn.configure(state="disabled")
            return

        if self.running and self.paused:
            self.start_btn.configure(state="disabled")
            self.pause_btn.configure(state="disabled")
            self.resume_btn.configure(state="normal")
            self.back_btn.configure(state="normal")
            self.skip_btn.configure(state="normal")
            self.reset_btn.configure(state="normal")
            self.confirm_complete_btn.configure(state="disabled")
            return

        self.start_btn.configure(state="normal" if self.current_workout else "disabled")
        self.pause_btn.configure(state="disabled")
        self.resume_btn.configure(state="disabled")
        self.back_btn.configure(state="disabled")
        self.skip_btn.configure(state="disabled")
        self.reset_btn.configure(state="disabled")
        self.confirm_complete_btn.configure(
            state="normal" if self.pending_completion_confirmation else "disabled"
        )


def main() -> None:
    default_config = Path(__file__).parent / "workouts.json"
    root = tk.Tk()
    app = WorkoutApp(root, default_config)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_timer(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()

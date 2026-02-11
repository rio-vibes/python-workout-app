(() => {
  const state = {
    workouts: [],
    completed: [],
    selectedIndex: -1,
    currentWorkout: null,
    currentPhase: "work",
    currentExerciseIndex: 0,
    currentRound: 1,
    timeRemaining: 0,
    running: false,
    paused: false,
    pendingCompletionConfirmation: false,
    viewMode: "plan",
    timerHandle: null,
  };

  const el = {
    workoutRoot: document.getElementById("workoutRoot"),
    workoutMeta: document.getElementById("workoutMeta"),
    workoutList: document.getElementById("workoutList"),
    planTitle: document.getElementById("planTitle"),
    planMeta: document.getElementById("planMeta"),
    planDescription: document.getElementById("planDescription"),
    planDuration: document.getElementById("planDuration"),
    planExercises: document.getElementById("planExercises"),
    phaseBadge: document.getElementById("phaseBadge"),
    roundText: document.getElementById("roundText"),
    timerText: document.getElementById("timerText"),
    exerciseName: document.getElementById("exerciseName"),
    exerciseDetail: document.getElementById("exerciseDetail"),
    instructionList: document.getElementById("instructionList"),
    nextText: document.getElementById("nextText"),
    statusMsg: document.getElementById("statusMsg"),
    startBtn: document.getElementById("startBtn"),
    resumeFromPlanBtn: document.getElementById("resumeFromPlanBtn"),
    pauseBtn: document.getElementById("pauseBtn"),
    resumeBtn: document.getElementById("resumeBtn"),
    backToPlanBtn: document.getElementById("backToPlanBtn"),
    backBtn: document.getElementById("backBtn"),
    skipBtn: document.getElementById("skipBtn"),
    resetBtn: document.getElementById("resetBtn"),
    confirmBtn: document.getElementById("confirmBtn"),
    reloadBtn: document.getElementById("reloadBtn"),
  };

  let audioCtx = null;

  function bindEvents() {
    el.startBtn.addEventListener("click", startWorkout);
    el.resumeFromPlanBtn.addEventListener("click", resumeFromPlan);
    el.pauseBtn.addEventListener("click", pauseWorkout);
    el.resumeBtn.addEventListener("click", resumeWorkout);
    el.backToPlanBtn.addEventListener("click", backToPlanView);
    el.backBtn.addEventListener("click", backPhase);
    el.skipBtn.addEventListener("click", skipPhase);
    el.resetBtn.addEventListener("click", resetWorkout);
    el.confirmBtn.addEventListener("click", confirmWorkoutComplete);
    el.reloadBtn.addEventListener("click", () => loadState(true));
  }

  async function loadState(announce = false) {
    try {
      const res = await fetch("/api/state");
      if (!res.ok) throw new Error("Unable to load workouts");
      const data = await res.json();
      applyServerState(data);
      if (announce) setStatus("Workouts reloaded.");
    } catch (err) {
      setStatus(String(err), true);
    }
  }

  function applyServerState(data) {
    const workouts = Array.isArray(data.workouts) ? data.workouts : [];
    const completed = Array.isArray(data.completed_workouts) ? data.completed_workouts : [];

    const previousKey =
      state.currentWorkout && state.currentWorkout.id
        ? `${state.currentWorkout.id}|${state.currentWorkout.date || ""}`
        : null;

    state.workouts = workouts;
    state.completed = completed;
    if (!state.running && !state.paused) {
      state.pendingCompletionConfirmation = false;
      state.viewMode = "plan";
    }

    if (!workouts.length) {
      stopTimer();
      state.selectedIndex = -1;
      state.currentWorkout = null;
      state.running = false;
      state.paused = false;
      state.pendingCompletionConfirmation = false;
      state.currentExerciseIndex = 0;
      state.currentRound = 1;
      state.timeRemaining = 0;
      state.currentPhase = "work";
      state.viewMode = "plan";
      renderWorkoutList();
      renderPlanOverview();
      renderSession();
      updateControls();
      return;
    }

    let index = 0;
    if (previousKey) {
      const found = workouts.findIndex(
        (w) => `${w.id || ""}|${w.date || ""}` === previousKey
      );
      if (found >= 0) index = found;
    }

    selectWorkout(index, false);
    renderWorkoutList();
    renderPlanOverview();
  }

  function selectWorkout(index, reset = true) {
    if (!state.workouts.length) return;
    const bounded = Math.max(0, Math.min(index, state.workouts.length - 1));

    // If user re-selects the active workout during a session, do not reset progress.
    const isSameSelection =
      state.currentWorkout &&
      bounded === state.selectedIndex &&
      state.currentWorkout.id === state.workouts[bounded].id &&
      state.currentWorkout.date === state.workouts[bounded].date;
    if (isSameSelection && (state.running || state.paused || state.pendingCompletionConfirmation)) {
      state.viewMode = "live";
      setStatus("");
      renderWorkoutList();
      renderPlanOverview();
      renderSession();
      updateControls();
      return;
    }

    state.selectedIndex = bounded;
    state.currentWorkout = state.workouts[bounded];
    if (reset) resetWorkout();
    renderWorkoutList();
    renderPlanOverview();
    renderSession();
    updateControls();
  }

  function renderWorkoutList() {
    if (!el.workoutList) return;
    el.workoutList.innerHTML = "";

    if (!state.workouts.length) {
      const empty = document.createElement("p");
      empty.className = "small-note";
      empty.textContent = "No scheduled workouts. Generate a new week and reload.";
      el.workoutList.appendChild(empty);
      el.workoutMeta.textContent = "0 workouts scheduled";
      return;
    }

    el.workoutMeta.textContent = `${state.workouts.length} workout${
      state.workouts.length === 1 ? "" : "s"
    } scheduled`;

    state.workouts.forEach((workout, idx) => {
      const button = document.createElement("button");
      button.className = `workout-item ${idx === state.selectedIndex ? "active" : ""}`;
      button.type = "button";
      button.dataset.testid = "workout-item";
      button.dataset.workoutId = String(workout.id || "");
      button.dataset.workoutDate = String(workout.date || "");
      button.addEventListener("click", () => selectWorkout(idx));

      const title = document.createElement("p");
      title.className = "workout-title";
      title.textContent = workout.title || "Untitled Workout";

      const date = document.createElement("p");
      date.className = "workout-date";
      date.textContent = workout.date || "No date";

      const desc = document.createElement("p");
      desc.className = "workout-desc";
      desc.textContent = workout.description || "";

      button.appendChild(title);
      button.appendChild(date);
      button.appendChild(desc);
      el.workoutList.appendChild(button);
    });
  }

  function startWorkout() {
    if (!state.currentWorkout) return;
    stopTimer();
    state.running = true;
    state.paused = false;
    state.pendingCompletionConfirmation = false;
    state.currentPhase = "work";
    state.currentExerciseIndex = 0;
    state.currentRound = 1;
    state.viewMode = "live";
    setPhaseTime();
    setStatus("");
    syncLayoutMode();
    renderSession();
    updateControls();
    scheduleTick();
  }

  function pauseWorkout() {
    if (!state.running) return;
    state.paused = true;
    stopTimer();
    setStatus("");
    updateControls();
  }

  function resumeWorkout() {
    if (!state.running || !state.paused) return;
    state.paused = false;
    state.viewMode = "live";
    setStatus("");
    renderSession();
    updateControls();
    scheduleTick();
  }

  function resetWorkout() {
    stopTimer();
    state.running = false;
    state.paused = false;
    state.pendingCompletionConfirmation = false;
    state.currentPhase = "work";
    state.currentExerciseIndex = 0;
    state.currentRound = 1;
    state.timeRemaining = 0;
    state.viewMode = "plan";
    setStatus("");
    syncLayoutMode();
    renderPlanOverview();
    renderSession();
    updateControls();
  }

  function backToPlanView() {
    if (!state.currentWorkout) return;
    if (state.running && !state.paused) {
      state.paused = true;
      stopTimer();
      setStatus("Workout paused. Review plan, then resume when ready.");
    }
    state.viewMode = "plan";
    renderPlanOverview();
    renderSession();
    updateControls();
  }

  function resumeFromPlan() {
    if (!state.currentWorkout) return;
    if (state.running && state.paused) {
      state.viewMode = "live";
      resumeWorkout();
      return;
    }
    if (state.running && !state.paused) {
      state.viewMode = "live";
      setStatus("");
      renderSession();
      updateControls();
      return;
    }
    if (state.pendingCompletionConfirmation) {
      state.viewMode = "live";
      setStatus("");
      renderSession();
      updateControls();
    }
  }

  function skipPhase() {
    if (!state.running) return;
    stopTimer();
    state.timeRemaining = 0;
    advancePhase();
  }

  function backPhase() {
    if (!state.currentWorkout) return;
    if (!state.running && !state.paused) return;

    stopTimer();

    if (
      state.currentPhase === "work" &&
      state.currentExerciseIndex === 0 &&
      state.currentRound === 1
    ) {
      setPhaseTime();
    } else if (state.currentPhase === "rest") {
      state.currentPhase = "work";
      setPhaseTime();
    } else {
      const [prevIndex, prevRound] = previousExercisePosition();
      state.currentExerciseIndex = prevIndex;
      state.currentRound = prevRound;
      const prevRest = currentRestSeconds();
      if (prevRest > 0) {
        state.currentPhase = "rest";
        state.timeRemaining = prevRest;
      } else {
        state.currentPhase = "work";
        setPhaseTime();
      }
    }

    renderSession();
    updateControls();
    if (state.running && !state.paused) scheduleTick();
  }

  function previousExercisePosition() {
    if (!state.currentWorkout) return [0, 1];
    const exercises = state.currentWorkout.exercises || [];

    if (state.currentExerciseIndex > 0) {
      return [state.currentExerciseIndex - 1, state.currentRound];
    }
    if (state.currentRound > 1) {
      return [Math.max(exercises.length - 1, 0), state.currentRound - 1];
    }
    return [0, 1];
  }

  function stopTimer() {
    if (state.timerHandle !== null) {
      window.clearInterval(state.timerHandle);
      state.timerHandle = null;
    }
  }

  function scheduleTick() {
    stopTimer();
    state.timerHandle = window.setInterval(tick, 1000);
  }

  function tick() {
    if (!state.running || state.paused) return;
    state.timeRemaining -= 1;
    if (state.timeRemaining <= 0) {
      advancePhase();
      return;
    }
    renderSession();
  }

  function advancePhase() {
    if (!state.currentWorkout) return;

    playAlert();

    if (state.currentPhase === "work") {
      const rest = currentRestSeconds();
      if (rest > 0) {
        state.currentPhase = "rest";
        state.timeRemaining = rest;
        renderSession();
        scheduleTick();
        return;
      }
      advanceToNextExercise();
      return;
    }

    advanceToNextExercise();
  }

  function advanceToNextExercise() {
    if (!state.currentWorkout) return;

    const exercises = state.currentWorkout.exercises || [];
    const rounds = Number(state.currentWorkout.rounds || 1);

    state.currentExerciseIndex += 1;
    if (state.currentExerciseIndex >= exercises.length) {
      state.currentExerciseIndex = 0;
      state.currentRound += 1;
    }

    if (state.currentRound > rounds) {
      stopTimer();
      state.running = false;
      state.paused = false;
      state.timeRemaining = 0;
      state.pendingCompletionConfirmation = true;
      renderSession();
      updateControls();
      playAlert();
      return;
    }

    state.currentPhase = "work";
    setPhaseTime();
    renderSession();
    scheduleTick();
  }

  async function confirmWorkoutComplete() {
    if (!state.pendingCompletionConfirmation || !state.currentWorkout) return;

    try {
      const res = await fetch("/api/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: state.currentWorkout.id,
          date: state.currentWorkout.date,
        }),
      });
      if (!res.ok) throw new Error("Unable to complete workout");
      const data = await res.json();
      setStatus("Workout saved to completed history.");
      applyServerState(data);
    } catch (err) {
      setStatus(String(err), true);
    }
  }

  function setPhaseTime() {
    if (!state.currentWorkout) {
      state.timeRemaining = 0;
      return;
    }
    const ex = state.currentWorkout.exercises[state.currentExerciseIndex] || {};
    state.timeRemaining = Number(ex.work_seconds || ex.duration_seconds || 0);
  }

  function currentRestSeconds() {
    if (!state.currentWorkout) return 0;
    const ex = state.currentWorkout.exercises[state.currentExerciseIndex] || {};
    const fallback = Number(state.currentWorkout.default_rest_seconds || 0);
    return Number(ex.rest_seconds ?? fallback);
  }

  function formatClock(totalSeconds) {
    const safe = Math.max(0, Number(totalSeconds) || 0);
    const minutes = Math.floor(safe / 60)
      .toString()
      .padStart(2, "0");
    const seconds = Math.floor(safe % 60)
      .toString()
      .padStart(2, "0");
    return `${minutes}:${seconds}`;
  }

  function peekNextExercise() {
    if (!state.currentWorkout) return null;
    const exercises = state.currentWorkout.exercises || [];
    if (!exercises.length) return null;
    const index = (state.currentExerciseIndex + 1) % exercises.length;
    return exercises[index];
  }

  function estimateWorkoutSeconds(workout) {
    if (!workout) return 0;
    const rounds = Math.max(1, Number(workout.rounds || 1));
    const defaultRest = Number(workout.default_rest_seconds || 0);
    const exercises = Array.isArray(workout.exercises) ? workout.exercises : [];

    const perRound = exercises.reduce((total, ex) => {
      const work = Number(ex.work_seconds || ex.duration_seconds || 0);
      const rest = Number(ex.rest_seconds ?? defaultRest);
      return total + Math.max(work, 0) + Math.max(rest, 0);
    }, 0);
    return perRound * rounds;
  }

  function formatDuration(seconds) {
    const safe = Math.max(0, Math.floor(Number(seconds) || 0));
    const hours = Math.floor(safe / 3600);
    const minutes = Math.floor((safe % 3600) / 60);
    const secs = safe % 60;
    const parts = [];
    if (hours) parts.push(`${hours}h`);
    if (minutes) parts.push(`${minutes}m`);
    if (secs || !parts.length) parts.push(`${secs}s`);
    return parts.join(" ");
  }

  function renderPlanOverview() {
    if (!el.planExercises) return;
    el.planExercises.innerHTML = "";

    if (!state.currentWorkout) {
      el.planTitle.textContent = "No workouts scheduled";
      el.planMeta.textContent = "Date: - | Rounds: - | Exercises: -";
      el.planDescription.textContent = "Generate a new weekly plan and reload.";
      el.planDuration.textContent = "--";

      const empty = document.createElement("p");
      empty.className = "small-note";
      empty.textContent = "No workout selected.";
      el.planExercises.appendChild(empty);
      return;
    }

    const workout = state.currentWorkout;
    const exercises = Array.isArray(workout.exercises) ? workout.exercises : [];
    const rounds = Math.max(1, Number(workout.rounds || 1));
    const estimate = estimateWorkoutSeconds(workout);

    el.planTitle.textContent = workout.title || "Untitled Workout";
    el.planMeta.textContent = `Date: ${workout.date || "-"} | Rounds: ${rounds} | Exercises: ${
      exercises.length
    }`;
    el.planDescription.textContent = workout.description || "";
    el.planDuration.textContent = formatDuration(estimate);

    if (!exercises.length) {
      const empty = document.createElement("p");
      empty.className = "small-note";
      empty.textContent = "No exercises available in this workout.";
      el.planExercises.appendChild(empty);
      return;
    }

    const defaultRest = Number(workout.default_rest_seconds || 0);

    exercises.forEach((exercise, idx) => {
      const card = document.createElement("article");
      card.className = "plan-ex-item";
      card.dataset.testid = "plan-ex-item";

      const head = document.createElement("div");
      head.className = "plan-ex-head";

      const name = document.createElement("h4");
      name.className = "plan-ex-name";
      name.textContent = `${idx + 1}. ${exercise.name || "Unnamed Exercise"}`;

      const metricText = document.createElement("p");
      metricText.className = "plan-ex-metrics";
      const workSecs = Number(exercise.work_seconds || exercise.duration_seconds || 0);
      const restSecs = Number(exercise.rest_seconds ?? defaultRest);
      const metrics = [`Work ${workSecs}s`, `Rest ${restSecs}s`];
      if (exercise.reps) metrics.push(`Reps ${exercise.reps}`);
      metricText.textContent = metrics.join(" | ");

      head.appendChild(name);
      card.appendChild(head);
      card.appendChild(metricText);

      const notes = normalizeInstructions(exercise.instructions);
      if (notes.length) {
        const list = document.createElement("ul");
        list.className = "plan-ex-notes";
        notes.forEach((note) => {
          const li = document.createElement("li");
          li.textContent = note;
          list.appendChild(li);
        });
        card.appendChild(list);
      }

      el.planExercises.appendChild(card);
    });
  }

  function syncLayoutMode() {
    if (!el.workoutRoot) return;
    const inSession = state.viewMode === "live";
    el.workoutRoot.classList.toggle("in-session", inSession);
  }

  function renderSession() {
    syncLayoutMode();

    if (!state.currentWorkout) {
      el.phaseBadge.textContent = "READY";
      applyPhaseClass("ready");
      el.roundText.textContent = "Round: -";
      el.timerText.textContent = "00:00";
      el.exerciseName.textContent = "No workouts scheduled";
      el.exerciseDetail.textContent = "Generate a new week plan and reload.";
      setInstructions([
        "No active workouts found.",
        "Use your LLM prompt with completed history to generate a new week.",
      ]);
      el.nextText.textContent = "Next: -";
      updateControls();
      return;
    }

    const exercises = state.currentWorkout.exercises || [];
    const ex = exercises[state.currentExerciseIndex] || {};
    const rounds = Number(state.currentWorkout.rounds || 1);

    if (state.running) {
      const phase = state.currentPhase === "work" ? "WORK" : "REST";
      el.phaseBadge.textContent = phase;
      applyPhaseClass(state.currentPhase);
    } else if (state.pendingCompletionConfirmation) {
      el.phaseBadge.textContent = "COMPLETE";
      applyPhaseClass("complete");
    } else {
      el.phaseBadge.textContent = "READY";
      applyPhaseClass("ready");
    }

    el.roundText.textContent = `Round: ${state.currentRound}/${rounds}`;
    el.timerText.textContent = formatClock(state.timeRemaining);

    if (state.pendingCompletionConfirmation) {
      el.exerciseName.textContent = "Workout complete";
      el.exerciseDetail.textContent = "Click Confirm Complete to move this workout to history.";
      setInstructions([
        "Session finished.",
        "Use Confirm Complete to archive this workout and remove it from active workouts.",
      ]);
      el.nextText.textContent = "Next: -";
      updateControls();
      return;
    }

    if (state.currentPhase === "rest" && state.running) {
      el.exerciseName.textContent = "Break";
      el.exerciseDetail.textContent = "Recover, breathe, and set up for the next movement.";
      const nextEx = peekNextExercise();
      el.nextText.textContent = `Next: ${nextEx?.name || "-"}`;
      setInstructions([
        "Keep moving lightly and breathe slowly.",
        "Reset posture: shoulders down, rib cage stacked, core gently braced.",
        "Get your setup ready before the timer reaches zero.",
      ]);
      updateControls();
      return;
    }

    el.exerciseName.textContent = ex.name || "Unnamed Exercise";
    const details = [
      `Date: ${state.currentWorkout.date || "-"}`,
      `Work: ${Number(ex.work_seconds || ex.duration_seconds || 0)} sec`,
    ];
    if (ex.reps) details.push(`Reps: ${ex.reps}`);
    if (ex.rest_seconds !== undefined) details.push(`Rest after: ${ex.rest_seconds} sec`);
    el.exerciseDetail.textContent = details.join(" | ");

    const nextEx = peekNextExercise();
    el.nextText.textContent = `Next: ${nextEx?.name || "-"}`;
    const bullets = normalizeInstructions(ex.instructions);
    setInstructions(bullets);
    updateControls();
  }

  function normalizeInstructions(raw) {
    if (Array.isArray(raw)) {
      const cleaned = raw.map((s) => String(s).trim()).filter(Boolean);
      return cleaned.length ? cleaned : ["No instructions provided."];
    }
    if (typeof raw !== "string" || !raw.trim()) return ["No instructions provided."];
    const lines = raw
      .split(/\n+/)
      .map((s) => s.replace(/^[-*\s]+/, "").trim())
      .filter(Boolean);
    if (lines.length > 1) return lines;
    return raw
      .split(".")
      .map((s) => s.trim())
      .filter(Boolean);
  }

  function setInstructions(bullets) {
    el.instructionList.innerHTML = "";
    bullets.forEach((bullet) => {
      const li = document.createElement("li");
      li.textContent = bullet;
      el.instructionList.appendChild(li);
    });
  }

  function applyPhaseClass(phase) {
    el.phaseBadge.classList.remove("phase-work", "phase-rest", "phase-complete");
    if (phase === "work") el.phaseBadge.classList.add("phase-work");
    if (phase === "rest") el.phaseBadge.classList.add("phase-rest");
    if (phase === "complete") el.phaseBadge.classList.add("phase-complete");
  }

  function updateControls() {
    syncLayoutMode();

    el.startBtn.disabled =
      !state.currentWorkout || state.running || state.paused || state.pendingCompletionConfirmation;
    el.resumeFromPlanBtn.disabled = !(state.running && state.paused);

    if (state.running && !state.paused) {
      el.pauseBtn.disabled = false;
      el.resumeBtn.disabled = true;
      el.backToPlanBtn.disabled = false;
      el.backBtn.disabled = false;
      el.skipBtn.disabled = false;
      el.resetBtn.disabled = false;
      el.confirmBtn.disabled = true;
      return;
    }

    if (state.running && state.paused) {
      el.pauseBtn.disabled = true;
      el.resumeBtn.disabled = false;
      el.backToPlanBtn.disabled = false;
      el.backBtn.disabled = false;
      el.skipBtn.disabled = false;
      el.resetBtn.disabled = false;
      el.confirmBtn.disabled = true;
      return;
    }

    el.pauseBtn.disabled = true;
    el.resumeBtn.disabled = true;
    el.backToPlanBtn.disabled = true;
    el.backBtn.disabled = true;
    el.skipBtn.disabled = true;
    el.resetBtn.disabled = true;
    el.confirmBtn.disabled = !state.pendingCompletionConfirmation;
  }

  function setStatus(message, isError = false) {
    el.statusMsg.textContent = message || "";
    el.statusMsg.classList.toggle("error", Boolean(isError));
  }

  function playAlert() {
    try {
      if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(880, audioCtx.currentTime);
      gain.gain.setValueAtTime(0.001, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.08, audioCtx.currentTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.2);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.2);
    } catch (_err) {
      // Optional beep only.
    }
  }

  bindEvents();
  loadState();
})();

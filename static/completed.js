(() => {
  const refreshBtn = document.getElementById("refreshCompletedBtn");
  const tableBody = document.getElementById("completedTableBody");
  const count = document.getElementById("completedCount");

  async function loadCompleted() {
    try {
      const res = await fetch("/api/state");
      if (!res.ok) throw new Error("Unable to load completed workouts");
      const data = await res.json();
      const completed = Array.isArray(data.completed_workouts) ? data.completed_workouts : [];
      render(completed);
    } catch (err) {
      tableBody.innerHTML = `<tr><td colspan="5" class="error">${String(err)}</td></tr>`;
      count.textContent = "";
    }
  }

  function render(rows) {
    tableBody.innerHTML = "";
    count.textContent = `${rows.length} completed workout${rows.length === 1 ? "" : "s"}`;

    if (!rows.length) {
      tableBody.innerHTML = '<tr><td colspan="5">No completed workouts yet.</td></tr>';
      return;
    }

    const reversed = [...rows].reverse();
    reversed.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${escapeHtml(row.day || "")}</td>
        <td>${escapeHtml(row.date || "")}</td>
        <td>${escapeHtml(row.title || "")}</td>
        <td>${escapeHtml(row.scheduled_date || "-")}</td>
        <td>${escapeHtml(row.completed_at || "-")}</td>
      `;
      tableBody.appendChild(tr);
    });
  }

  function escapeHtml(text) {
    return String(text)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  refreshBtn.addEventListener("click", loadCompleted);
  loadCompleted();
})();

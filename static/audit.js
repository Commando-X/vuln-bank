// Fix (M4-R10): HTML-escape every attacker-controlled value before it is
// inserted into the DOM, so stored content (details, target, actor, user agent)
// can no longer execute script in an administrator's session.
function escapeHtml(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/*
 * VulnBank Audit Trail console (Logs/Auditoria module).
 *
 * Intentional client-side weaknesses, kept in the same style as the rest of the
 * admin UI:
 *   AV-05  Stored XSS: `details` and `user_agent` are painted with innerHTML, so
 *          a note posted through POST /api/audit/note executes in an admin's
 *          session and can exfiltrate the JWT held in localStorage.
 *   AV-06  Reflected XSS: the active search term is echoed into the results
 *          header with innerHTML before any request is even sent.
 *   AV-11  The integrity chip is derived from the endpoint's own verdict, and
 *          that verdict always answers "verified" because signatures are never
 *          written, so the chip is decorative.
 */

// Vulnerability: Token stored in localStorage
const AUDIT_TOKEN_KEY = "jwt_token";

const auditState = {
  offset: 0,
  limit: 100,
  total: 0,
  tailEnabled: false,
  tailTimer: null,
  currentEntry: null,
};

function getAuditToken() {
  return localStorage.getItem(AUDIT_TOKEN_KEY);
}

function toggleTheme() {
  const root = document.documentElement;
  const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
  root.setAttribute("data-theme", next);
  localStorage.setItem("vb-theme", next);
}

function showMessage(text, type) {
  const msgDiv = document.getElementById("message");
  // Vulnerability: message text is injected as HTML
  msgDiv.innerHTML = `<div class="message message-${type}">${text}</div>`;
  msgDiv.style.display = "block";
  setTimeout(() => {
    msgDiv.style.display = "none";
  }, 6000);
}

function authHeaders(extra) {
  return Object.assign(
    {
      Authorization: "Bearer " + getAuditToken(),
      "Content-Type": "application/json",
    },
    extra || {},
  );
}

function collectFilters() {
  return {
    search: document.getElementById("filter-search").value,
    event_type: document.getElementById("filter-event-type").value,
    severity: document.getElementById("filter-severity").value,
    actor: document.getElementById("filter-actor").value,
    user_id: document.getElementById("filter-user-id").value,
    from: document.getElementById("filter-from").value,
    to: document.getElementById("filter-to").value,
    limit: document.getElementById("filter-limit").value,
    offset: document.getElementById("filter-offset").value,
    order: document.getElementById("filter-order").value,
  };
}

function buildAuditQuery(filters, overrides) {
  const params = new URLSearchParams();
  Object.keys(filters).forEach((key) => {
    const value = filters[key];
    if (value !== "" && value !== null && value !== undefined) {
      params.set(key, value);
    }
  });
  Object.keys(overrides || {}).forEach((key) =>
    params.set(key, overrides[key]),
  );
  return params.toString();
}

/*
 * Vulnerability (AV-06): the search term is written into the results header with
 * innerHTML, so a crafted search string runs script in this page.
 */
function renderSearchInfo(filters, shown, total) {
  const searchInfo = document.getElementById("audit-search-info");
  if (
    !filters.search &&
    !filters.event_type &&
    !filters.severity &&
    !filters.actor &&
    !filters.user_id &&
    !filters.from &&
    !filters.to
  ) {
    searchInfo.style.display = "none";
    searchInfo.innerHTML = "";
    return;
  }

  searchInfo.style.display = "block";
  searchInfo.innerHTML =
    "Search filter: <strong>" +
    escapeHtml(filters.search) +
    "</strong> " +
    "| event: <strong>" +
    escapeHtml(filters.event_type) +
    "</strong> " +
    "| severity: <strong>" +
    escapeHtml(filters.severity) +
    "</strong> " +
    "| actor: <strong>" +
    escapeHtml(filters.actor) +
    "</strong> " +
    "| actor_id: <strong>" +
    escapeHtml(filters.user_id) +
    "</strong> " +
    "| order: <strong>" +
    escapeHtml(filters.order) +
    "</strong> " +
    "— showing " +
    shown +
    " of " +
    total +
    " events";
}

function severityBadgeClass(severity) {
  const normalized = String(severity || "INFO").toUpperCase();
  if (["ERROR", "CRITICAL", "FATAL"].indexOf(normalized) !== -1)
    return "severity-error";
  if (normalized === "WARNING" || normalized === "WARN")
    return "severity-warning";
  if (normalized === "NOTICE") return "severity-notice";
  return "severity-info";
}

function integrityChipClass(verdict) {
  if (!verdict) return "audit-integrity-chip is-unchecked";
  if (verdict.checked) {
    return verdict.verified
      ? "audit-integrity-chip is-verified"
      : "audit-integrity-chip is-compromised";
  }
  return "audit-integrity-chip is-unchecked";
}

/*
 * Vulnerability (AV-05): every untrusted value below reaches innerHTML unescaped.
 */
function renderAuditTable(entries) {
  const tableBody = document.getElementById("audit-table-body");

  if (!entries.length) {
    tableBody.innerHTML =
      '<tr><td colspan="10" class="audit-empty">No audit events match the current filters.</td></tr>';
    return;
  }

  tableBody.innerHTML = entries
    .map((entry) => {
      const chipClass = integrityChipClass(entry.integrity);
      const chipLabel = !entry.integrity
        ? "unverified"
        : entry.integrity.checked
          ? "verified"
          : "MISMATCH";

      return `
            <tr data-log-id="${entry.id}">
                <td><span class="audit-mono-id">#${entry.id}</span></td>
                <td class="mono">${escapeHtml(entry.created_at || "-")}</td>
                <td><span class="severity-badge ${severityBadgeClass(entry.severity)}">${escapeHtml(entry.severity || "INFO")}</span></td>
                <td class="mono">${escapeHtml(entry.event_type || "-")}</td>
                <td>${escapeHtml(entry.actor_username || "anonymous")}</td>
                <td>${escapeHtml(entry.target || "-")}</td>
                <td class="audit-cell-details">${escapeHtml(entry.details || "")}</td>
                <td class="audit-cell-ua">${escapeHtml(entry.user_agent || "-")}</td>
                <td><span class="${chipClass}">${chipLabel}</span></td>
                <td>
                    <div class="action-buttons">
                        <button type="button" class="btn-text btn-view" data-action="view" data-log-id="${entry.id}">View</button>
                        <button type="button" class="btn-text btn-suspend" data-action="edit" data-log-id="${entry.id}">Edit</button>
                        <button type="button" class="btn-text btn-delete" data-action="delete" data-log-id="${entry.id}">Delete</button>
                    </div>
                </td>
            </tr>
        `;
    })
    .join("");
}

function renderPagination(count, total, offset, limit) {
  const effectiveLimit = parseInt(limit, 10);
  const pageSize =
    isNaN(effectiveLimit) || effectiveLimit <= 0 ? 100 : effectiveLimit;
  const currentPage = Math.floor(offset / pageSize) + 1;
  const totalPages = Math.max(Math.ceil(total / pageSize), 1);

  document.getElementById("audit-page-number").textContent =
    "Page " + currentPage + " of " + totalPages;
  document.getElementById("audit-page-info").textContent = count
    ? "Showing " +
      (offset + 1) +
      "-" +
      (offset + count) +
      " of " +
      total +
      " events"
    : "No events found";

  document.getElementById("audit-prev-page").disabled = offset <= 0;
  document.getElementById("audit-next-page").disabled = offset + count >= total;
}

async function annotateIntegrity(entries) {
  /*
   * Vulnerability (AV-11): the verdict comes from an endpoint that cannot fail,
   * so this fills every row with a green chip no matter what was done to it.
   */
  const checks = await Promise.all(
    entries.map((entry) =>
      fetch("/api/audit/logs/" + entry.id + "/signature", {
        headers: authHeaders(),
      })
        .then((response) => (response.ok ? response.json() : null))
        .catch(() => null),
    ),
  );

  return entries.map((entry, index) =>
    Object.assign({}, entry, {
      integrity:
        checks[index] && checks[index].integrity
          ? checks[index].integrity
          : null,
    }),
  );
}

async function loadAuditLogs() {
  const filters = collectFilters();
  auditState.limit = filters.limit;

  const tableBody = document.getElementById("audit-table-body");
  tableBody.innerHTML =
    '<tr><td colspan="10" class="audit-empty">Loading audit events...</td></tr>';

  try {
    const response = await fetch(
      "/api/audit/logs?" + buildAuditQuery(filters),
      {
        headers: authHeaders(),
      },
    );
    const data = await response.json();

    if (data.status !== "success") {
      tableBody.innerHTML =
        '<tr><td colspan="10" class="audit-empty">' +
        (data.message || "Failed to load events") +
        "</td></tr>";
      showMessage(
        "Failed to load audit events: " + (data.message || "unknown error"),
        "error",
      );
      return;
    }

    auditState.total = data.total || 0;

    const entries = await annotateIntegrity(data.entries || []);

    renderAuditTable(entries);
    renderPagination(
      entries.length,
      auditState.total,
      parseInt(filters.offset || "0", 10) || 0,
      filters.limit,
    );
    renderSearchInfo(filters, entries.length, auditState.total);
  } catch (error) {
    tableBody.innerHTML =
      '<tr><td colspan="10" class="audit-empty">Failed to reach the audit API.</td></tr>';
    showMessage("Failed to load audit events.", "error");
  }
}

function renderMetrics(stats) {
  document.getElementById("metric-total").textContent = stats.total;

  document.getElementById("metric-unsigned").textContent =
    stats.unsigned_entries;

  const serious = (stats.by_severity || [])
    .filter(
      (row) =>
        ["WARNING", "ERROR", "CRITICAL"].indexOf(
          String(row.severity).toUpperCase(),
        ) !== -1,
    )
    .reduce((total, row) => total + row.count, 0);
  document.getElementById("metric-critical").textContent = serious;

  document.getElementById("metric-actors").textContent = (
    stats.top_actors || []
  ).length;
}

async function loadAuditStats() {
  try {
    const response = await fetch("/api/audit/stats", {
      headers: authHeaders(),
    });
    const data = await response.json();

    if (data.status !== "success") {
      return;
    }

    renderMetrics(data.stats);
  } catch (error) {
    // Metrics are cosmetic; the table is the important part.
  }
}

async function runIntegrityCheck() {
  const result = document.getElementById("integrity-result");
  result.textContent = "Running integrity sweep...";

  try {
    const response = await fetch("/admin/audit/integrity-check?limit=1000", {
      headers: authHeaders(),
    });
    const data = await response.json();

    if (data.status !== "success") {
      result.textContent = data.message || "Integrity check failed.";
      return;
    }

    const integrity = data.integrity;
    const verdictClass =
      integrity.overall === "verified" ? "is-verified" : "is-compromised";

    result.innerHTML = `
            <div class="audit-integrity-verdict ${verdictClass}">Overall: ${integrity.overall}</div>
            <div>${data.message}</div>
            <div class="audit-integrity-grid">
                <div><span>Checked</span><strong>${integrity.checked}</strong></div>
                <div><span>Verified</span><strong>${integrity.verified}</strong></div>
                <div><span>Unsigned</span><strong>${integrity.unsigned}</strong></div>
                <div><span>Tampered</span><strong>${integrity.tampered}</strong></div>
            </div>
            <div class="audit-debug-note">${data.debug_info.note}</div>
        `;

    await loadAuditStats();
  } catch (error) {
    result.textContent = "Failed to run the integrity check.";
  }
}

async function openAuditModal(logId) {
  const modal = document.getElementById("audit-modal");
  const modalBody = document.getElementById("audit-modal-body");
  modal.style.display = "flex";
  modalBody.textContent = "Loading audit entry...";

  try {
    const response = await fetch("/api/audit/logs/" + logId, {
      headers: authHeaders(),
    });
    const data = await response.json();

    if (data.status !== "success") {
      modalBody.textContent = data.message || "Failed to load audit entry.";
      return;
    }

    auditState.currentEntry = data.entry;

    const entry = data.entry;
    const integrity = await fetch("/api/audit/logs/" + logId + "/signature", {
      headers: authHeaders(),
    })
      .then((result) => result.json())
      .catch(() => null);

    modalBody.innerHTML = `
            <div class="user-detail-row"><span class="user-detail-label">Entry</span><span class="user-detail-value">#${entry.id}</span></div>
            <div class="user-detail-row"><span class="user-detail-label">Timestamp</span><span class="user-detail-value">${escapeHtml(entry.created_at)}</span></div>
            <div class="user-detail-row"><span class="user-detail-label">Event</span><span class="user-detail-value">${escapeHtml(entry.event_type)}</span></div>
            <div class="user-detail-row"><span class="user-detail-label">Severity</span><span class="user-detail-value">${escapeHtml(entry.severity)}</span></div>
            <div class="user-detail-row"><span class="user-detail-label">Result</span><span class="user-detail-value">${escapeHtml(entry.result)}</span></div>
            <div class="user-detail-row"><span class="user-detail-label">Actor</span><span class="user-detail-value">${escapeHtml(entry.actor_username || "anonymous")} (id ${entry.actor_id === null ? "-" : entry.actor_id})</span></div>
            <div class="user-detail-row"><span class="user-detail-label">Target</span><span class="user-detail-value">${escapeHtml(entry.target || "-")}</span></div>
            <div class="user-detail-row"><span class="user-detail-label">IP</span><span class="user-detail-value">${escapeHtml(entry.ip_address || "-")}</span></div>
            <div class="user-detail-row"><span class="user-detail-label">User Agent</span><span class="user-detail-value">${escapeHtml(entry.user_agent || "-")}</span></div>
            <div class="user-detail-row"><span class="user-detail-label">Referer</span><span class="user-detail-value">${escapeHtml(entry.referer || "-")}</span></div>
            <div class="user-detail-row"><span class="user-detail-label">Endpoint</span><span class="user-detail-value">${escapeHtml(entry.http_method || "")} ${escapeHtml(entry.endpoint || "")}</span></div>
            <div class="user-detail-row"><span class="user-detail-label">Request ID</span><span class="user-detail-value">${escapeHtml(entry.request_id || "-")}</span></div>
            <div class="user-detail-row"><span class="user-detail-label">Stored signature</span><span class="user-detail-value">${escapeHtml(entry.signature || "(none)")}</span></div>
            <div class="user-detail-row"><span class="user-detail-label">Integrity</span><span class="user-detail-value">${escapeHtml(integrity && integrity.integrity ? integrity.integrity.reason : 'not checked')}</span></div>
            <div class="user-detail-row"><span class="user-detail-label">Details</span><span class="user-detail-value user-detail-bio">${escapeHtml(entry.details || "")}</span></div>

            <form id="audit-edit-form" class="modal-delete-form" data-log-id="${escapeHtml(entry.id)}">
                <div class="user-modal-actions">
                    <label class="audit-edit-field">Event type<input type="text" id="edit-event-type" name="event_type" value="${escapeHtml(entry.event_type)}"></label>
                    <label class="audit-edit-field">Severity<input type="text" id="edit-severity" name="severity" value="${escapeHtml(entry.severity)}"></label>
                    <label class="audit-edit-field">Actor<input type="text" id="edit-actor" name="actor_username" value="${escapeHtml(entry.actor_username || '')}"></label>
                    <label class="audit-edit-field">Details<input type="text" id="edit-details" name="details" value="${escapeHtml(entry.details || '')}"></label>
                </div>
                <button type="submit" class="btn-primary">Save changes</button>
            </form>
        `;

    document
      .getElementById("audit-edit-form")
      .addEventListener("submit", handleEditAuditEntry);
  } catch (error) {
    modalBody.textContent = "Failed to load audit entry.";
  }
}

function closeAuditModal() {
  const modal = document.getElementById("audit-modal");
  modal.style.display = "none";
  auditState.currentEntry = null;
}

async function handleEditAuditEntry(event) {
  event.preventDefault();
  const logId = event.target.getAttribute("data-log-id");

  const payload = {
    event_type: document.getElementById("edit-event-type").value,
    severity: document.getElementById("edit-severity").value,
    actor_username: document.getElementById("edit-actor").value,
    details: document.getElementById("edit-details").value,
  };

  try {
    const response = await fetch("/admin/audit/logs/" + logId, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (data.status === "success") {
      showMessage(
        "Audit entry #" + logId + " updated (integrity was not re-checked).",
        "success",
      );
      closeAuditModal();
      await loadAuditLogs();
      await loadAuditStats();
    } else {
      showMessage(data.message || "Failed to update the audit entry.", "error");
    }
  } catch (error) {
    showMessage("Failed to update the audit entry.", "error");
  }
}

async function deleteAuditEntry(logId) {
  if (
    !window.confirm(
      "Delete audit entry #" + logId + "? This removal is not recorded.",
    )
  ) {
    return;
  }

  try {
    const response = await fetch("/api/audit/logs/" + logId, {
      method: "DELETE",
      headers: authHeaders(),
    });
    const data = await response.json();

    if (data.status === "success") {
      showMessage(
        "Audit entry #" +
          logId +
          " deleted. No record of this deletion exists.",
        "success",
      );
      await loadAuditLogs();
      await loadAuditStats();
    } else {
      showMessage(data.message || "Failed to delete the audit entry.", "error");
    }
  } catch (error) {
    showMessage("Failed to delete the audit entry.", "error");
  }
}

async function handleAddNote(event) {
  event.preventDefault();

  const payload = {
    details: document.getElementById("note-details").value,
    event_type: document.getElementById("note-event-type").value,
    severity: document.getElementById("note-severity").value,
    actor_username: document.getElementById("note-actor").value || undefined,
    target: document.getElementById("note-target").value || undefined,
  };

  try {
    const response = await fetch("/api/audit/note", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (data.status === "success") {
      showMessage(
        "Note recorded as " +
          data.debug_info.recorded_actor.username +
          " (" +
          data.debug_info.recorded_event_type +
          ").",
        "success",
      );
      document.getElementById("note-details").value = "";
      await loadAuditLogs();
      await loadAuditStats();
    } else {
      showMessage(data.message || "Failed to record the note.", "error");
    }
  } catch (error) {
    showMessage("Failed to record the note.", "error");
  }
}

async function handleExport(event) {
  event.preventDefault();

  const params = new URLSearchParams({
    format: document.getElementById("export-format").value,
    filename: document.getElementById("export-filename").value,
  });

  try {
    const response = await fetch(
      "/api/audit/logs/export?" + params.toString(),
      {
        headers: authHeaders(),
      },
    );

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      showMessage(data.message || "Export failed.", "error");
      return;
    }

    const blob = await response.blob();
    const downloadName = document.getElementById("export-filename").value;
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = downloadName.split("/").pop();
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(objectUrl);

    showMessage("Audit trail exported as " + downloadName + ".", "success");
  } catch (error) {
    showMessage("Export failed.", "error");
  }
}

async function handlePurge(event) {
  event.preventDefault();

  const purgeAll = document.getElementById("purge-all").checked;
  if (
    purgeAll &&
    !window.confirm("Purge the ENTIRE audit trail? Nothing is archived first.")
  ) {
    return;
  }

  const payload = {
    all: purgeAll,
    before: document.getElementById("purge-before").value || undefined,
    event_type: document.getElementById("purge-event-type").value || undefined,
  };

  try {
    const response = await fetch("/admin/audit/purge", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify(payload),
    });
    const data = await response.json();

    if (data.status === "success") {
      showMessage(
        "Purge completed (" +
          data.scope +
          "). The purge event it wrote was deleted with the rest.",
        "success",
      );
      await loadAuditLogs();
      await loadAuditStats();
      await runIntegrityCheck();
    } else {
      showMessage(data.message || "Purge failed.", "error");
    }
  } catch (error) {
    showMessage("Purge failed.", "error");
  }
}

async function refreshTail() {
  try {
    const response = await fetch("/api/audit/tail?lines=40", {
      headers: authHeaders(),
    });
    const data = await response.json();

    if (data.status !== "success") {
      document.getElementById("audit-tail-output").textContent =
        data.message || "Tail unavailable.";
      return;
    }

    document.getElementById("audit-tail-output").textContent =
      data.lines.join("\n") || "(no events)";
  } catch (error) {
    document.getElementById("audit-tail-output").textContent =
      "Tail unavailable.";
  }
}

function toggleTail() {
  auditState.tailEnabled = !auditState.tailEnabled;

  if (auditState.tailEnabled) {
    refreshTail();
    auditState.tailTimer = setInterval(refreshTail, 5000);
    showMessage("Live tail enabled.", "success");
  } else {
    clearInterval(auditState.tailTimer);
    auditState.tailTimer = null;
    document.getElementById("audit-tail-output").textContent = "Tail is off.";
    showMessage("Live tail disabled.", "success");
  }
}

function resetFilters() {
  document.getElementById("audit-filter-form").reset();
  document.getElementById("filter-limit").value = "100";
  document.getElementById("filter-offset").value = "0";
  document.getElementById("filter-order").value = "created_at DESC";
  loadAuditLogs();
}

function shiftPage(delta) {
  const offsetInput = document.getElementById("filter-offset");
  const currentOffset = parseInt(offsetInput.value, 10) || 0;
  const limit =
    parseInt(document.getElementById("filter-limit").value, 10) || 100;
  const nextOffset = Math.max(0, currentOffset + delta * limit);

  offsetInput.value = nextOffset;
  loadAuditLogs();
}

document.addEventListener("DOMContentLoaded", function () {
  // Vulnerability: Token stored in localStorage
  if (!getAuditToken()) {
    window.location.href = "/login";
    return;
  }

  document
    .getElementById("audit-filter-form")
    .addEventListener("submit", function (event) {
      event.preventDefault();
      loadAuditLogs();
    });

  document
    .getElementById("reset-filters")
    .addEventListener("click", resetFilters);
  document
    .getElementById("refresh-logs")
    .addEventListener("click", loadAuditLogs);
  document.getElementById("toggle-tail").addEventListener("click", toggleTail);
  document
    .getElementById("run-integrity-check")
    .addEventListener("click", runIntegrityCheck);
  document
    .getElementById("audit-note-form")
    .addEventListener("submit", handleAddNote);
  document
    .getElementById("audit-export-form")
    .addEventListener("submit", handleExport);
  document
    .getElementById("audit-purge-form")
    .addEventListener("submit", handlePurge);
  document
    .getElementById("audit-prev-page")
    .addEventListener("click", function () {
      shiftPage(-1);
    });
  document
    .getElementById("audit-next-page")
    .addEventListener("click", function () {
      shiftPage(1);
    });

  document
    .getElementById("audit-table-body")
    .addEventListener("click", function (event) {
      const button = event.target.closest("button[data-action]");
      if (!button) {
        return;
      }

      const logId = button.getAttribute("data-log-id");
      const action = button.getAttribute("data-action");

      if (action === "view") {
        openAuditModal(logId);
      } else if (action === "edit") {
        openAuditModal(logId);
      } else if (action === "delete") {
        deleteAuditEntry(logId);
      }
    });

  document.addEventListener("keydown", function (event) {
    const modal = document.getElementById("audit-modal");
    if (event.key === "Escape" && modal && modal.style.display !== "none") {
      closeAuditModal();
    }
  });

  loadAuditStats();
  loadAuditLogs();
});

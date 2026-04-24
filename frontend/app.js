// frontend/app.js
/*
 * Main application logic.
 *
 * Manages calendar state, renders the monthly grid, and wires up all
 * user interactions (creating, editing, deleting events).
 */

import { fetchEvents, createEvent, deleteEvent, updateEvent } from "./api.js";

// ── State ─────────────────────────────────────────────────────────────────────

let currentDate  = new Date();       // month currently displayed
let currentUserId = parseInt(localStorage.getItem("userId") || "0", 10);
let events        = [];              // all events for currentUserId
let editingId     = null;            // id of event being edited, or null

// ── DOM refs ──────────────────────────────────────────────────────────────────

const $  = id => document.getElementById(id);

const monthLabel       = $("month-label");
const calendarGrid     = $("calendar-grid");
const upcomingList     = $("upcoming-events");
const eventModal       = $("event-modal");
const userModal        = $("user-modal");
const eventForm        = $("event-form");
const modalTitle       = $("modal-title");
const userDisplay      = $("user-display");
const deleteBtn        = $("delete-event-btn");
const recurrenceGroup  = $("recurrence-group");

const MONTHS = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December",
];

// ── Bootstrap ─────────────────────────────────────────────────────────────────

async function init() {
    bindUIEvents();
    openCalendarToCurrentMonth();

    if (!currentUserId) {
        showModal(userModal);
    } else {
        userDisplay.textContent = currentUserId;
        await loadAndRender();
    }
}

// ── Data loading ──────────────────────────────────────────────────────────────

async function loadAndRender() {
    try {
        events = await fetchEvents(currentUserId);
    } catch (err) {
        showToast("Could not load events: " + err.message, "error");
        events = [];
    }
    renderCalendar();
}

// ── Calendar rendering ────────────────────────────────────────────────────────
// Initializes the calendar to the current month and year when the page loads
function openCalendarToCurrentMonth() {
    currentDate = new Date();
    renderCalendar();
}

function renderCalendar() {
    const year  = currentDate.getFullYear();
    const month = currentDate.getMonth();   // 0-indexed

    monthLabel.textContent = `${MONTHS[month]} ${year}`;

    // Remove previous day cells (leave the 7 header cells in place).
    calendarGrid.querySelectorAll(".day-cell").forEach(el => el.remove());

    const firstWeekday  = new Date(year, month, 1).getDay();   // 0 = Sun
    const daysInMonth   = new Date(year, month + 1, 0).getDate();
    const daysInPrev    = new Date(year, month, 0).getDate();

    const todayStr = isoDate(new Date());

    // Build a date → events[] lookup for fast access.
    const byDate = buildEventsByDate();

    // Leading days from the previous month.
    for (let i = firstWeekday - 1; i >= 0; i--) {
        const d = daysInPrev - i;
        appendDayCell(year, month - 1, d, false, todayStr, byDate);
    }

    // Current-month days.
    for (let d = 1; d <= daysInMonth; d++) {
        appendDayCell(year, month, d, true, todayStr, byDate);
    }

    // Trailing days from the next month to fill the last row.
    const total    = firstWeekday + daysInMonth;
    const trailing = total % 7 === 0 ? 0 : 7 - (total % 7);
    for (let d = 1; d <= trailing; d++) {
        appendDayCell(year, month + 1, d, false, todayStr, byDate);
    }

    renderUpcoming();
}

function appendDayCell(year, month, day, isCurrentMonth, todayStr, byDate) {
    const date    = new Date(year, month, day);   // JS handles month overflow
    const dateStr = isoDate(date);
    const isToday = dateStr === todayStr;

    const cell = document.createElement("div");
    cell.className = [
        "day-cell",
        isCurrentMonth ? "" : "other-month",
        isToday        ? "today" : "",
    ].join(" ").trim();
    cell.dataset.date = dateStr;

    // Day number badge.
    const numEl = document.createElement("div");
    numEl.className = "day-num";
    numEl.textContent = date.getDate();
    cell.appendChild(numEl);

    // Event chips.
    const dayEvents  = byDate[dateStr] || [];
    const eventsEl   = document.createElement("div");
    eventsEl.className = "day-events";
    const MAX_CHIPS  = 3;

    dayEvents.slice(0, MAX_CHIPS).forEach(ev => {
        const chip = document.createElement("div");
        chip.className = `event-chip type-${ev.event_type || "event"}`;
        chip.textContent = ev.title;
        chip.addEventListener("click", e => { e.stopPropagation(); openEditModal(ev); });
        eventsEl.appendChild(chip);
    });

    if (dayEvents.length > MAX_CHIPS) {
        const more = document.createElement("div");
        more.className = "more-events";
        more.textContent = `+${dayEvents.length - MAX_CHIPS} more`;
        eventsEl.appendChild(more);
    }

    cell.appendChild(eventsEl);
    cell.addEventListener("click", () => openNewModal(dateStr));
    calendarGrid.appendChild(cell);
}

// Build a mapping from ISO date string (YYYY-MM-DD) to array of events.
function buildEventsByDate() {
    const map = {};
    for (const ev of events) {
        if (!ev.start_time) continue;
        const key = ev.start_time.slice(0, 10);
        (map[key] = map[key] || []).push(ev);
    }
    return map;
}

// ── Sidebar: upcoming events ──────────────────────────────────────────────────

function renderUpcoming() {
    const now = new Date();
    const upcoming = events
        .filter(ev => ev.start_time && new Date(ev.start_time) >= now)
        .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
        .slice(0, 10);

    upcomingList.innerHTML = "";

    if (upcoming.length === 0) {
        const li = document.createElement("li");
        li.className = "no-events";
        li.textContent = "No upcoming events";
        upcomingList.appendChild(li);
        return;
    }

    for (const ev of upcoming) {
        const li   = document.createElement("li");
        li.className = `event-list-item type-${ev.event_type || "event"}`;

        const title = document.createElement("div");
        title.className  = "ev-title";
        title.textContent = ev.title;

        const time = document.createElement("div");
        time.className  = "ev-time";
        time.textContent = formatEventTime(ev);

        li.appendChild(title);
        li.appendChild(time);
        li.addEventListener("click", () => openEditModal(ev));
        upcomingList.appendChild(li);
    }
}

function formatEventTime(ev) {
    if (!ev.start_time) return "No time set";
    return new Date(ev.start_time).toLocaleString(undefined, {
        month: "short", day: "numeric",
        hour: "numeric", minute: "2-digit",
    });
}

// ── Modal helpers ─────────────────────────────────────────────────────────────

function openNewModal(dateStr) {
    editingId = null;
    modalTitle.textContent = "New Event";
    eventForm.reset();
    $("event-id").value = "";
    deleteBtn.classList.add("hidden");
    recurrenceGroup.classList.add("hidden");

    if (dateStr) {
        $("event-start").value = `${dateStr}T09:00`;
        $("event-end").value   = `${dateStr}T10:00`;
    }

    showModal(eventModal);
}

function openEditModal(ev) {
    editingId = ev.id;
    modalTitle.textContent = "Edit Event";

    $("event-id").value          = ev.id;
    $("event-title").value       = ev.title          || "";
    $("event-type").value        = ev.event_type      || "event";
    $("event-start").value       = toDatetimeLocal(ev.start_time);
    $("event-end").value         = toDatetimeLocal(ev.end_time);
    $("event-location").value    = ev.location        || "";
    $("event-description").value = ev.description     || "";
    $("event-reminder").value    = ev.reminder_minutes != null ? ev.reminder_minutes : "";
    $("event-recurrence").value  = ev.recurrence_rule || "";

    recurrenceGroup.classList.toggle("hidden", ev.event_type !== "recurring");
    deleteBtn.classList.remove("hidden");

    showModal(eventModal);
}

// Convert SQLite "YYYY-MM-DD HH:MM:SS" to the "YYYY-MM-DDTHH:MM" format
// required by <input type="datetime-local">.
function toDatetimeLocal(str) {
    if (!str) return "";
    return str.replace(" ", "T").slice(0, 16);
}

function showModal(modal) { modal.classList.remove("hidden"); }
function hideModal(modal) { modal.classList.add("hidden"); }

// ── Form submission ───────────────────────────────────────────────────────────

async function handleFormSubmit(e) {
    e.preventDefault();

    const type     = $("event-type").value;
    const startRaw = $("event-start").value;
    const endRaw   = $("event-end").value;

    const data = {
        user_id:          currentUserId,
        title:            $("event-title").value.trim(),
        event_type:       type,
        start_time:       startRaw.replace("T", " "),
        end_time:         endRaw   ? endRaw.replace("T", " ")                     : null,
        location:         $("event-location").value.trim()    || null,
        description:      $("event-description").value.trim() || null,
        reminder_minutes: parseInt($("event-reminder").value) || null,
        recurrence_rule:  type === "recurring"
                            ? $("event-recurrence").value.trim() || null
                            : null,
        is_all_day:       type === "allday",
    };

    try {
        if (editingId) {
            await updateEvent(editingId, data);
            showToast("Event updated", "success");
        } else {
            await createEvent(data);
            showToast("Event created", "success");
        }
        hideModal(eventModal);
        await loadAndRender();
    } catch (err) {
        showToast("Error: " + err.message, "error");
    }
}

async function handleDelete() {
    if (!editingId) return;
    if (!confirm("Delete this event? This cannot be undone.")) return;

    try {
        await deleteEvent(editingId);
        showToast("Event deleted", "success");
        hideModal(eventModal);
        await loadAndRender();
    } catch (err) {
        showToast("Error: " + err.message, "error");
    }
}

// ── Toast ─────────────────────────────────────────────────────────────────────

function showToast(message, type = "info") {
    const container = $("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3200);
}

// ── Utilities ─────────────────────────────────────────────────────────────────

// Return "YYYY-MM-DD" for a Date object.
function isoDate(d) {
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
}

// ── Bind all UI events ────────────────────────────────────────────────────────

function bindUIEvents() {
    // Month navigation.
    $("prev-month").addEventListener("click", () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar();
    });
    $("next-month").addEventListener("click", () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar();
    });
    $("today-btn").addEventListener("click", () => {
        currentDate = new Date();
        renderCalendar();
    });

    // New event button (opens modal pre-filled with today).
    $("add-event-btn").addEventListener("click", () => openNewModal(isoDate(new Date())));

    // Event modal close triggers.
    $("close-modal").addEventListener("click", () => hideModal(eventModal));
    $("cancel-btn").addEventListener("click",  () => hideModal(eventModal));
    eventModal.addEventListener("click", e => { if (e.target === eventModal) hideModal(eventModal); });

    // Form actions.
    eventForm.addEventListener("submit", handleFormSubmit);
    deleteBtn.addEventListener("click",  handleDelete);

    // Show/hide recurrence field when event type changes.
    $("event-type").addEventListener("change", e => {
        recurrenceGroup.classList.toggle("hidden", e.target.value !== "recurring");
    });

    // User modal.
    $("change-user-btn").addEventListener("click", () => showModal(userModal));
    $("confirm-user-btn").addEventListener("click", async () => {
        const newId = parseInt($("user-id-input").value, 10);
        if (newId > 0) {
            currentUserId = newId;
            localStorage.setItem("userId", newId);
            userDisplay.textContent = newId;
            hideModal(userModal);
            await loadAndRender();
        }
    });

    // Allow pressing Enter in the user-ID field to confirm.
    $("user-id-input").addEventListener("keydown", e => {
        if (e.key === "Enter") $("confirm-user-btn").click();
    });
}

// ── Start ─────────────────────────────────────────────────────────────────────
init();
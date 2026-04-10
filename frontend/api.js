// frontend/api.js
/*
 * Backend API client.
 *
 * Wraps every fetch call to the Flask backend so the rest of the app
 * never has to deal with raw fetch, status codes, or JSON parsing.
 */

const API_BASE = "http://localhost:5000/api";

async function request(path, options = {}) {
    const res = await fetch(`${API_BASE}${path}`, {
        headers: { "Content-Type": "application/json", ...options.headers },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ error: res.statusText }));
        throw new Error(err.error || `HTTP ${res.status}`);
    }
    return res.json();
}

export async function fetchEvents(userId) {
    return request(`/events?user_id=${userId}`);
}

export async function fetchEvent(eventId) {
    return request(`/events/${eventId}`);
}

export async function createEvent(data) {
    return request("/events", { method: "POST", body: JSON.stringify(data) });
}

export async function updateEvent(eventId, data) {
    return request(`/events/${eventId}`, { method: "PUT", body: JSON.stringify(data) });
}

export async function deleteEvent(eventId) {
    return request(`/events/${eventId}`, { method: "DELETE" });
}

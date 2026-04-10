// frontend/app.js
/*
Frontend interaction logic.

This file will handle user interactions on the page, such as submitting
new events, updating the calendar display, making API calls to the backend,
and dynamically rendering event data in the interface.
*/

import { fetchEvents, createEvent, deleteEvent, updateEvent } from "./api.js";
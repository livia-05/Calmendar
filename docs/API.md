# API Reference

Base URL: `http://127.0.0.1:5000`

All request and response bodies are JSON. Dates use the format `YYYY-MM-DD` and times use `HH:MM` (24-hour).

---

## Tasks

### `GET /api/tasks`

Returns all tasks. Pass a `date` query parameter to filter to a single day.

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `date` | `YYYY-MM-DD` | Optional. Filter tasks to this date only. |

**Response** — `200 OK`
```json
[
  {
    "id": 1,
    "title": "Write project report",
    "date": "2026-06-04",
    "start_time": "09:00",
    "end_time": "11:00",
    "notes": "Focus on the summary section first",
    "priority": "high",
    "category": "work",
    "status": "in_progress",
    "created_at": "2026-06-04T08:30:00"
  }
]
```

---

### `GET /api/tasks/<id>`

Returns a single task by its ID.

**Response** — `200 OK` — same shape as a single item from the list above.

**Error** — `404` if no task with that ID exists.

---

### `POST /api/tasks`

Creates a new task.

**Request body**

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | yes | Name of the task |
| `date` | `YYYY-MM-DD` | yes | Date the task belongs to |
| `start_time` | `HH:MM` | no | Start time in 24-hour format |
| `end_time` | `HH:MM` | no | End time in 24-hour format |
| `notes` | string | no | Any notes or details about the task |
| `priority` | string | no | `low`, `medium` (default), or `high` |
| `category` | string | no | Free-form label, e.g. `work`, `personal` |

**Response** — `201 Created` — the newly created task object.

**Error** — `400` if `title` or `date` is missing.

---

### `PUT /api/tasks/<id>`

Updates an existing task. Send only the fields you want to change.

**Request body** — any combination of the fields below

| Field | Type | Description |
|---|---|---|
| `title` | string | New task name |
| `date` | `YYYY-MM-DD` | Reschedule to a different date |
| `start_time` | `HH:MM` | New start time |
| `end_time` | `HH:MM` | New end time |
| `notes` | string | Updated notes |
| `priority` | string | `low`, `medium`, or `high` |
| `category` | string | Updated category label |
| `status` | string | `not_started`, `in_progress`, or `completed` |

**Response** — `200 OK` — the updated task object.

**Errors** — `400` if no valid fields were provided; `404` if task not found.

---

### `DELETE /api/tasks/<id>`

Deletes a task permanently.

**Response** — `204 No Content`

**Error** — `404` if task not found.

---

## Profile

### `GET /api/profile`

Returns the current user profile, or `null` if none exists yet.

**Response** — `200 OK`
```json
{
  "id": 1,
  "name": "Olivia",
  "work_description": "Software engineer",
  "hobbies": "painting, hiking, music",
  "wake_time": "07:00",
  "sleep_time": "23:00",
  "max_daily_hours": 8,
  "break_style": "frequent_short",
  "stress_sensitivity": "medium",
  "onboarding_complete": 1,
  "created_at": "2026-06-01T10:00:00"
}
```

---

### `POST /api/profile`

Creates the user profile. Called once during onboarding. Sets `onboarding_complete` to `1` automatically.

**Request body**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | User's name |
| `work_description` | string | no | Description of their job or daily work |
| `hobbies` | string | no | Comma-separated list of hobbies, used to personalize break suggestions |
| `wake_time` | `HH:MM` | no | Typical wake-up time |
| `sleep_time` | `HH:MM` | no | Typical bedtime |
| `max_daily_hours` | integer | no | Max hours of productive work per day (default: `8`) |
| `break_style` | string | no | `frequent_short` (default) or `infrequent_long` |
| `stress_sensitivity` | string | no | `low`, `medium` (default), or `high` — affects overscheduling thresholds |

**Response** — `201 Created` — the created profile object.

**Error** — `400` if `name` is missing.

---

### `PUT /api/profile`

Updates the existing profile. Send only the fields you want to change. Accepts the same optional fields as `POST`.

**Response** — `200 OK` — the updated profile object.

**Error** — `400` if no valid fields were provided; `404` if no profile exists.

---

## Breaks

### `GET /api/breaks`

Returns all break activities. Filter with query parameters.

**Query parameters**

| Parameter | Type | Description |
|---|---|---|
| `screen_free` | `0` or `1` | Filter to only screen-free (or screen) activities |
| `favorited` | `0` or `1` | Filter to only favorited (or unfavorited) activities |

**Response** — `200 OK`
```json
[
  {
    "id": 1,
    "name": "Short Walk",
    "description": "Step outside or walk around the building",
    "category": "physical",
    "duration_minutes": 10,
    "is_screen_free": 1,
    "is_custom": 0,
    "is_favorited": 0,
    "created_at": "2026-06-01T10:00:00"
  }
]
```

---

### `POST /api/breaks`

Creates a custom break activity. The new activity is always marked `is_custom: 1`.

**Request body**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | yes | Name of the activity |
| `description` | string | no | Short description of what to do |
| `category` | string | no | Category label, e.g. `physical`, `creative` |
| `duration_minutes` | integer | no | Suggested duration in minutes |
| `is_screen_free` | `0` or `1` | no | Whether the activity is screen-free (default: `1`) |

**Response** — `201 Created` — the created break activity object.

**Error** — `400` if `name` is missing.

---

### `PUT /api/breaks/<id>/favorite`

Toggles the `is_favorited` flag on a break activity. If it was favorited, it becomes unfavorited, and vice versa.

**Response** — `200 OK` — the updated break activity object.

**Error** — `404` if the activity is not found.

---

### `DELETE /api/breaks/<id>`

Deletes a custom break activity. Built-in (non-custom) activities cannot be deleted.

**Response** — `204 No Content`

**Errors** — `403` if the activity is a built-in default; `404` if not found.

---

## Reflections

### `GET /api/reflections`

Returns all reflections from the past 7 days, ordered newest first. Reflections older than 7 days are automatically deleted when this endpoint is called.

**Response** — `200 OK`
```json
[
  {
    "id": 1,
    "date": "2026-06-04",
    "mood": 4,
    "notes": "Productive morning, afternoon dragged a bit.",
    "ai_summary": "You wrapped up 3 tasks today...",
    "created_at": "2026-06-04T20:00:00"
  }
]
```

---

### `GET /api/reflections/<date>`

Returns the reflection for a specific date, or `null` if none exists.

**Response** — `200 OK` — a single reflection object, or `null`.

---

### `POST /api/reflections`

Creates a reflection for a given date. Cannot be used for future dates.

**Request body**

| Field | Type | Required | Description |
|---|---|---|---|
| `date` | `YYYY-MM-DD` | yes | The date being reflected on (must not be in the future) |
| `mood` | integer 1–5 | no | Mood score: 1 = very difficult, 5 = great |
| `notes` | string | no | Free-form notes about the day |
| `ai_summary` | string | no | Pre-generated summary text |

**Response** — `201 Created` — the created reflection object.

**Errors** — `400` if `date` is missing or is a future date; `409` if a reflection for that date already exists.

---

### `PUT /api/reflections/<date>`

Updates an existing reflection. Cannot be used for future dates.

**Request body** — any combination of `mood`, `notes`, `ai_summary`.

**Response** — `200 OK` — the updated reflection object.

**Errors** — `400` if no valid fields were provided or date is in the future; `404` if no reflection exists for that date.

---

### `POST /api/reflections/<date>/summary`

Generates an AI-written summary for the given date and saves it to the reflection. Reads the day's tasks, mood, and notes from the database, then calls Claude to write a warm, personalized summary. Falls back to a rule-based summary if the AI is unavailable.

**Response** — `200 OK` — the full reflection object with `ai_summary` populated.
```json
{
  "id": 1,
  "date": "2026-06-04",
  "mood": 4,
  "notes": "Good focus in the morning.",
  "ai_summary": "You wrapped up the project report and two meetings today — solid, focused work. The afternoon tasks can wait until tomorrow with a clear head. Rest well tonight; you showed up and that's what matters.",
  "created_at": "2026-06-04T20:00:00"
}
```

**Error** — `400` if date is in the future.

---

## AI

### `POST /api/ai/schedule-analysis`

Analyzes whether the day is overscheduled and whether a break nudge should be shown. Uses the user's profile (max daily hours, stress sensitivity) to judge the threshold. Falls back to a `503` if the AI service is unavailable.

**Request body**

| Field | Type | Required | Description |
|---|---|---|---|
| `date` | `YYYY-MM-DD` | yes | The date to analyze |

**Response** — `200 OK`
```json
{
  "overscheduled": true,
  "overscheduled_message": "You have 10 hours of tasks today — well above your 8-hour limit. Consider moving one item to tomorrow.",
  "needs_break": true,
  "break_message": "With a day this packed, a short break now will help you finish strong."
}
```

If `overscheduled` is `false`, `overscheduled_message` will be `null`. If `needs_break` is `false`, `break_message` will be `null`.

**Error** — `400` if `date` is missing; `503` if the AI service fails.

---

### `POST /api/ai/break-suggestion`

Returns a personalized break suggestion for the given date. Uses the user's hobbies, work type, and today's tasks to pick something relevant. If the AI is unavailable, falls back to a rule-based suggestion from a local pool of 96 activities.

**Request body**

| Field | Type | Required | Description |
|---|---|---|---|
| `date` | `YYYY-MM-DD` | yes | The date to generate a suggestion for |

**Response** — `200 OK`
```json
{
  "name": "Sketch or doodle",
  "description": "Grab any pen and paper and draw whatever comes to mind — no goal, just flow.",
  "duration_minutes": 10,
  "reason": "After a day of screen-heavy work, stepping away to draw gives your eyes and mind a genuine rest."
}
```

**Error** — `400` if `date` is missing.

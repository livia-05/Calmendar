# Database Schema

Calmendar uses a single SQLite database stored at `database/calmendar.db`. It is created automatically when the server first starts. The schema is defined in `database/schema.sql`.

---

## Tables

- [user_profile](#user_profile)
- [tasks](#tasks)
- [reflections](#reflections)
- [break_activities](#break_activities)

---

## user_profile

Stores the single user profile collected during onboarding. The app reads this row to personalize break suggestions, overscheduling thresholds, and AI prompts. There is only ever one row.

| Column | Type | Default | Description |
|---|---|---|---|
| `id` | `INTEGER` | auto | Primary key |
| `name` | `TEXT NOT NULL` | — | User's name |
| `work_description` | `TEXT` | `NULL` | Description of their job or daily work. Used by the AI to understand the type of cognitive load they experience. |
| `hobbies` | `TEXT` | `NULL` | Comma-separated list of hobbies, e.g. `"painting, hiking, music"`. Used to score and match break suggestions. |
| `wake_time` | `TEXT` | `NULL` | Typical wake-up time in `HH:MM` format |
| `sleep_time` | `TEXT` | `NULL` | Typical bedtime in `HH:MM` format |
| `max_daily_hours` | `INTEGER` | `8` | Maximum hours of productive work per day. The AI uses this as the baseline for overscheduling detection. |
| `break_style` | `TEXT` | `'frequent_short'` | Preferred break cadence. Must be `frequent_short` or `infrequent_long`. Determines whether suggested breaks are 5–10 min or 20–30 min. |
| `stress_sensitivity` | `TEXT` | `'medium'` | How easily the user gets overwhelmed. Must be `low`, `medium`, or `high`. Lowers the overscheduling threshold for high-sensitivity users. |
| `onboarding_complete` | `INTEGER` | `0` | Set to `1` when the user finishes onboarding. The app redirects to `/onboarding` until this is `1`. |
| `created_at` | `TEXT` | `CURRENT_TIMESTAMP` | ISO 8601 timestamp of when the profile was created |

---

## tasks

Stores every task the user creates. Tasks have an optional time block (`start_time` / `end_time`), which is used to render them on the 24-hour timeline and calculate total scheduled hours for overscheduling detection.

| Column | Type | Default | Description |
|---|---|---|---|
| `id` | `INTEGER` | auto | Primary key |
| `title` | `TEXT NOT NULL` | — | Name of the task |
| `date` | `TEXT NOT NULL` | — | Date the task belongs to, stored as `YYYY-MM-DD` |
| `start_time` | `TEXT` | `NULL` | Start time as `HH:MM` (24-hour). `NULL` means the task is unscheduled. |
| `end_time` | `TEXT` | `NULL` | End time as `HH:MM` (24-hour). Used with `start_time` to calculate block duration. |
| `notes` | `TEXT` | `NULL` | Any additional notes or details the user attached to the task |
| `priority` | `TEXT` | `'medium'` | Task priority. Must be `low`, `medium`, or `high`. Controls color coding on the timeline. |
| `category` | `TEXT` | `NULL` | Free-form label the user assigns, e.g. `work`, `personal`, `school`. Used by the AI to understand the nature of the day. |
| `status` | `TEXT` | `'not_started'` | Current status. Must be `not_started`, `in_progress`, or `completed`. |
| `created_at` | `TEXT` | `CURRENT_TIMESTAMP` | ISO 8601 timestamp of when the task was created |

---

## reflections

Stores one end-of-day reflection per date. The `date` column has a `UNIQUE` constraint so only one reflection can exist per day. Reflections older than 7 days are automatically deleted when `GET /api/reflections` is called.

| Column | Type | Default | Description |
|---|---|---|---|
| `id` | `INTEGER` | auto | Primary key |
| `date` | `TEXT NOT NULL UNIQUE` | — | The date being reflected on, stored as `YYYY-MM-DD` |
| `mood` | `INTEGER` | `NULL` | Mood rating from `1` (very difficult) to `5` (great). Enforced by a `CHECK` constraint. |
| `notes` | `TEXT` | `NULL` | Free-form notes the user wrote about their day |
| `ai_summary` | `TEXT` | `NULL` | The AI-generated (or rule-based fallback) end-of-day summary. Populated when the user clicks "Summarize" on the reflection page or hits `POST /api/reflections/<date>/summary`. |
| `created_at` | `TEXT` | `CURRENT_TIMESTAMP` | ISO 8601 timestamp of when the reflection was created |

---

## break_activities

Stores the library of break activities shown to the user. The table is pre-populated with 10 built-in defaults (`is_custom = 0`) when the database is first initialized. Users can add their own (`is_custom = 1`) and delete them, but built-in activities cannot be deleted.

| Column | Type | Default | Description |
|---|---|---|---|
| `id` | `INTEGER` | auto | Primary key |
| `name` | `TEXT NOT NULL` | — | Display name of the activity, e.g. `"Short Walk"` |
| `description` | `TEXT` | `NULL` | One or two sentences describing what to actually do |
| `category` | `TEXT` | `NULL` | Category label, e.g. `physical`, `mindfulness`, `creative`, `social`, `rest` |
| `duration_minutes` | `INTEGER` | `NULL` | Suggested duration in minutes |
| `is_screen_free` | `INTEGER` | `1` | `1` if the activity does not require a screen, `0` if it does. Stored as an integer boolean. |
| `is_custom` | `INTEGER` | `0` | `0` for built-in defaults, `1` for user-created activities. Custom activities can be deleted; built-ins cannot. |
| `is_favorited` | `INTEGER` | `0` | `1` if the user has favorited this activity, `0` otherwise. Toggled via `PUT /api/breaks/<id>/favorite`. |
| `created_at` | `TEXT` | `CURRENT_TIMESTAMP` | ISO 8601 timestamp of when the activity was added |

### Built-in defaults

The following 10 activities are inserted on first run:

| Name | Category | Duration | Screen-free |
|---|---|---|---|
| Short Walk | physical | 10 min | yes |
| Stretching | physical | 5 min | yes |
| Breathing Exercise | mindfulness | 5 min | yes |
| Grab a Snack | rest | 5 min | yes |
| Quick Meditation | mindfulness | 10 min | yes |
| Journal | creative | 10 min | yes |
| Listen to Music | rest | 10 min | no |
| Watch a Video | rest | 15 min | no |
| Doodle / Sketch | creative | 10 min | yes |
| Call a Friend | social | 10 min | yes |

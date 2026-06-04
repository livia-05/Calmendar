# CLI Reference

The CLI connects to the running Flask server at `http://127.0.0.1:5000`. Start the server first with `uv run python run.py`, then use the commands below.

All commands are run with:
```
uv run python -m cli.cli <command>
```

---

## Commands

- [tasks list](#tasks-list)
- [tasks add](#tasks-add)
- [tasks status](#tasks-status)
- [tasks delete](#tasks-delete)
- [breaks list](#breaks-list)
- [breaks add](#breaks-add)
- [breaks favorite](#breaks-favorite)
- [reflect](#reflect)
- [profile](#profile)

---

## tasks list

List tasks for a given date. Defaults to today.

```
uv run python -m cli.cli tasks list [--date DATE]
```

**Options**

| Flag | Description |
|---|---|
| `--date DATE` | Date to list tasks for in `YYYY-MM-DD` format. Defaults to today. |

**Example — today's tasks**
```
$ uv run python -m cli.cli tasks list

Tasks for 2026-06-04
  ○ [1] Write project report  09:00–11:00
  ◐ [2] Team standup  09:30–10:00
  ● [3] Review pull requests  11:00–12:00
```

**Example — specific date**
```
$ uv run python -m cli.cli tasks list --date 2026-06-03

Tasks for 2026-06-03
  ● [4] Morning journaling
  ● [5] Grocery run  10:00–11:00
  ○ [6] Email catch-up
```

Status icons: `○` = not started, `◐` = in progress, `●` = completed. Task titles are color-coded by priority (red = high, yellow = medium, green = low).

---

## tasks add

Add a new task interactively. The CLI prompts for each field; press Enter to skip optional ones.

```
uv run python -m cli.cli tasks add
```

**Example**
```
$ uv run python -m cli.cli tasks add

Title: Finish slide deck
Date (YYYY-MM-DD) [2026-06-04]:
Start time HH:MM  (leave blank to skip): 14:00
End time   HH:MM  (leave blank to skip): 16:00
Priority (low, medium, high) [medium]: high
Category           (leave blank to skip): work
Notes              (leave blank to skip): Include Q2 results

○ Task added (id 7): Finish slide deck
```

---

## tasks status

Update the status of an existing task.

```
uv run python -m cli.cli tasks status <TASK_ID> <STATUS>
```

**Arguments**

| Argument | Description |
|---|---|
| `TASK_ID` | Integer ID of the task (shown in `tasks list`) |
| `STATUS` | One of: `not_started`, `in_progress`, `completed` |

**Example — mark a task in progress**
```
$ uv run python -m cli.cli tasks status 7 in_progress

◐  [7] Finish slide deck → in_progress
```

**Example — mark a task complete**
```
$ uv run python -m cli.cli tasks status 7 completed

●  [7] Finish slide deck → completed
```

---

## tasks delete

Delete a task by its ID. Asks for confirmation before deleting.

```
uv run python -m cli.cli tasks delete <TASK_ID>
```

**Arguments**

| Argument | Description |
|---|---|
| `TASK_ID` | Integer ID of the task to delete |

**Example**
```
$ uv run python -m cli.cli tasks delete 7

Delete task 7? [y/N]: y
Deleted.
```

---

## breaks list

List available break activities. Shows ID, name, duration, and whether it requires a screen.

```
uv run python -m cli.cli breaks list [--screen-free] [--favorites]
```

**Options**

| Flag | Description |
|---|---|
| `--screen-free` | Show only screen-free activities |
| `--favorites` | Show only activities you have favorited |

**Example — all breaks**
```
$ uv run python -m cli.cli breaks list

Break Activities
    [1]  Short Walk  10min
    [2]  Stretching  5min
  ♥ [3]  Breathing Exercise  5min
    [4]  Grab a Snack  5min
    [5]  Quick Meditation  10min
    [6]  Journal  10min
    [7]  Listen to Music  10min [screen]
    [8]  Watch a Video  15min [screen]
    [9]  Doodle / Sketch  10min
    [10] Call a Friend  10min
```

The `♥` icon marks favorited activities. `[screen]` marks activities that require a screen.

**Example — screen-free only**
```
$ uv run python -m cli.cli breaks list --screen-free

Break Activities
    [1]  Short Walk  10min
    [2]  Stretching  5min
  ♥ [3]  Breathing Exercise  5min
    ...
```

---

## breaks add

Add a custom break activity interactively.

```
uv run python -m cli.cli breaks add
```

**Example**
```
$ uv run python -m cli.cli breaks add

Name: Play with my cat
Description (leave blank to skip): Spend a few minutes playing with your cat using a toy.
Category    (leave blank to skip): social
Duration in minutes (leave blank to skip): 10
Is this screen-free? [Y/n]: Y

Break activity added (id 11): Play with my cat
```

---

## breaks favorite

Toggle the favorite status of a break activity. Run it again on the same ID to unfavorite.

```
uv run python -m cli.cli breaks favorite <BREAK_ID>
```

**Arguments**

| Argument | Description |
|---|---|
| `BREAK_ID` | Integer ID of the break activity (shown in `breaks list`) |

**Example — favorite**
```
$ uv run python -m cli.cli breaks favorite 1

Short Walk favorited ♥.
```

**Example — unfavorite (same command)**
```
$ uv run python -m cli.cli breaks favorite 1

Short Walk unfavorited.
```

---

## reflect

Log your end-of-day reflection for a given date. If a reflection already exists for that date, it is updated. Defaults to today.

```
uv run python -m cli.cli reflect [--date DATE]
```

**Options**

| Flag | Description |
|---|---|
| `--date DATE` | Date to reflect on in `YYYY-MM-DD` format. Defaults to today. |

**Example**
```
$ uv run python -m cli.cli reflect

End-of-day reflection for 2026-06-04
Mood (1-5): 4
Any notes? (leave blank to skip): Good focus in the morning. Afternoon slowed down.

Reflection saved.

You wrapped up the project report and your team standup today — solid, consistent work.
The slide deck is still ahead, but you'll come to it fresh tomorrow. Rest well tonight;
you showed up and that's what matters.
```

The italicized summary at the end is the AI-generated (or rule-based fallback) day summary, only shown if one has already been generated for that date.

---

## profile

Display your current user profile.

```
uv run python -m cli.cli profile
```

**Example**
```
$ uv run python -m cli.cli profile

Profile: Olivia
  Work Description: Software engineer
  Hobbies: painting, hiking, music
  Wake Time: 07:00
  Sleep Time: 23:00
  Max Daily Hours: 8
  Break Style: frequent_short
  Stress Sensitivity: medium
```

If no profile exists yet, the CLI will tell you to complete onboarding at `http://127.0.0.1:5000`.

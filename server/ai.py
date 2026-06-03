import os
import json
import anthropic
from server.database import get_db

_client = None
MODEL_FAST = 'claude-haiku-4-5-20251001'
MODEL_FULL = 'claude-sonnet-4-6'


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise RuntimeError('ANTHROPIC_API_KEY is not set')
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _format_tasks(tasks):
    if not tasks:
        return 'No tasks scheduled'
    lines = []
    for t in tasks:
        time_str = ''
        if t['start_time']:
            time_str = f" ({t['start_time']}"
            if t['end_time']:
                time_str += f"–{t['end_time']}"
            time_str += ')'
        lines.append(f"- {t['title']}{time_str} [{t['priority']} priority, {t['status']}]")
    return '\n'.join(lines)


def _total_hours(tasks):
    total_min = 0
    for t in tasks:
        if t['start_time'] and t['end_time']:
            sh, sm = map(int, t['start_time'].split(':'))
            eh, em = map(int, t['end_time'].split(':'))
            total_min += (eh * 60 + em) - (sh * 60 + sm)
    return total_min / 60


def analyze_schedule(date):
    """Read today's tasks + profile from DB and ask Claude whether the day is overscheduled
    and whether the user needs a break nudge. Returns a dict with four keys:
    overscheduled (bool), overscheduled_message (str|None),
    needs_break (bool), break_message (str|None)."""
    db = get_db()
    profile = db.execute('SELECT * FROM user_profile ORDER BY id LIMIT 1').fetchone()
    tasks = db.execute(
        'SELECT * FROM tasks WHERE date = ? ORDER BY start_time', (date,)
    ).fetchall()

    total_hours = _total_hours(tasks)

    if profile:
        profile_ctx = (
            f"Name: {profile['name']}\n"
            f"Work: {profile['work_description'] or 'not specified'}\n"
            f"Max daily hours: {profile['max_daily_hours']}\n"
            f"Stress sensitivity: {profile['stress_sensitivity']}\n"
            f"Break style: {profile['break_style']}\n"
            f"Wake: {profile['wake_time'] or 'not set'}, Sleep: {profile['sleep_time'] or 'not set'}"
        )
    else:
        profile_ctx = 'No profile'

    prompt = f"""You are a mindful scheduling assistant for Calmendar, a personal daily planner.

User profile:
{profile_ctx}

Tasks for {date}:
{_format_tasks(tasks)}
Total scheduled time: {total_hours:.1f} hours

Respond with ONLY a JSON object — no markdown, no explanation:
{{
  "overscheduled": true or false,
  "overscheduled_message": "1-2 sentence specific message about why this day is too full, or null if not overscheduled",
  "needs_break": true or false,
  "break_message": "1-2 sentence warm nudge to take a break if schedule is heavy, or null"
}}

Use the user's stress sensitivity and max_daily_hours to judge overscheduling — don't use a fixed threshold.
High-priority or cognitively heavy tasks should lower the threshold. Be warm and specific, not generic."""

    response = _get_client().messages.create(
        model=MODEL_FAST,
        max_tokens=300,
        messages=[{'role': 'user', 'content': prompt}]
    )

    return json.loads(response.content[0].text)


def suggest_break(date):
    """Read today's tasks + profile from DB and ask Claude for a specific, personalized
    break activity suggestion. Returns a dict with name, description, duration_minutes, reason."""
    db = get_db()
    profile = db.execute('SELECT * FROM user_profile ORDER BY id LIMIT 1').fetchone()
    tasks = db.execute(
        'SELECT * FROM tasks WHERE date = ? ORDER BY start_time', (date,)
    ).fetchall()

    if profile:
        break_style_desc = (
            'frequent short breaks (5–10 min)'
            if profile['break_style'] == 'frequent_short'
            else 'infrequent longer breaks (20–30 min)'
        )
        profile_ctx = (
            f"Hobbies: {profile['hobbies'] or 'not specified'}\n"
            f"Break style preference: {break_style_desc}\n"
            f"Work type: {profile['work_description'] or 'not specified'}"
        )
    else:
        profile_ctx = 'No profile'

    prompt = f"""You are a mindful well-being assistant for Calmendar.

User profile:
{profile_ctx}

Today's schedule:
{_format_tasks(tasks)}

Suggest one specific break activity tailored to this person's hobbies and what they've been doing today.
Respond with ONLY a JSON object — no markdown:
{{
  "name": "short activity name",
  "description": "what to do in 1-2 sentences",
  "duration_minutes": number,
  "reason": "why this fits this person right now, 1 sentence"
}}"""

    response = _get_client().messages.create(
        model=MODEL_FAST,
        max_tokens=250,
        messages=[{'role': 'user', 'content': prompt}]
    )

    return json.loads(response.content[0].text)


def generate_day_summary(date, completed, pending, mood=None, notes=None):
    """Ask Claude to write a warm, specific end-of-day summary grounded in the user's
    actual tasks and reflection notes."""
    db = get_db()
    profile = db.execute('SELECT * FROM user_profile ORDER BY id LIMIT 1').fetchone()

    completed_str = '\n'.join(f'- {t["title"]}' for t in completed) if completed else 'none'
    pending_str = '\n'.join(f'- {t["title"]}' for t in pending) if pending else 'none'

    if profile:
        profile_ctx = (
            f"Name: {profile['name']}\n"
            f"Work: {profile['work_description'] or 'not specified'}\n"
            f"Hobbies: {profile['hobbies'] or 'not specified'}"
        )
    else:
        profile_ctx = 'No profile'

    mood_line = f"\nMood today: {mood}/5" if mood else ''
    notes_line = f"\nUser's reflection notes: {notes}" if notes else ''

    prompt = f"""You are a warm, encouraging daily reflection assistant for Calmendar.

User profile:
{profile_ctx}

Date: {date}
Completed tasks:
{completed_str}

Still pending:
{pending_str}{mood_line}{notes_line}

Write a brief, genuine end-of-day summary in 2-3 sentences. Acknowledge specific accomplishments,
address pending work gently and positively, and close with an encouraging thought tailored to this person.
Avoid generic phrases like "great job" — be specific and human."""

    response = _get_client().messages.create(
        model=MODEL_FULL,
        max_tokens=200,
        messages=[{'role': 'user', 'content': prompt}]
    )

    return response.content[0].text.strip()

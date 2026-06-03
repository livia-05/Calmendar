import os
import re
import json
import random
import hashlib
import anthropic
from server.database import get_db


# ── Local (no-API) suggestion pool ──────────────────────────────────────────

_ACTIVITY_POOL = [
    {
        "name": "Go for a walk",
        "description": "Head outside for a short walk — around the block or somewhere nearby.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["hiking", "walk", "outdoor", "nature", "running", "exercise"],
        "tags": ["physical", "outdoor", "screen_free"],
        "reason": "Getting outside and moving clears your head after focused work."
    },
    {
        "name": "Listen to music",
        "description": "Put on a favorite album or playlist, close your eyes, and just listen.",
        "short_mins": 10, "long_mins": 25,
        "hobby_keywords": ["music", "guitar", "piano", "singing", "concert", "band"],
        "tags": ["creative", "relaxing", "screen_free"],
        "reason": "Music you enjoy is one of the fastest ways to decompress between tasks."
    },
    {
        "name": "Stretch or do yoga",
        "description": "A few gentle stretches or a short yoga flow to release tension in your body.",
        "short_mins": 5, "long_mins": 20,
        "hobby_keywords": ["yoga", "stretch", "fitness", "gym", "pilates", "exercise"],
        "tags": ["physical", "mindful", "screen_free"],
        "reason": "Stretching counteracts the tension that builds up during long periods of sitting."
    },
    {
        "name": "Read a few pages",
        "description": "Pick up your book and read a few pages — no pressure to finish anything.",
        "short_mins": 10, "long_mins": 30,
        "hobby_keywords": ["reading", "books", "novel", "literature", "fiction"],
        "tags": ["quiet", "screen_free", "relaxing"],
        "reason": "Reading gives your analytical mind a rest while keeping you pleasantly engaged."
    },
    {
        "name": "Make tea or a snack",
        "description": "Step away from your screen, go to the kitchen, and make something to enjoy.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["cooking", "baking", "food", "coffee", "tea", "kitchen"],
        "tags": ["screen_free", "relaxing"],
        "reason": "A small ritual like making food gives you a satisfying, natural scene change."
    },
    {
        "name": "Sketch or doodle",
        "description": "Grab any pen and paper and draw whatever comes to mind — no goal, just flow.",
        "short_mins": 10, "long_mins": 20,
        "hobby_keywords": ["art", "drawing", "painting", "sketch", "illustration", "creative", "design"],
        "tags": ["creative", "screen_free", "relaxing"],
        "reason": "Unstructured drawing lets your mind wander freely, which is exactly what recharges it."
    },
    {
        "name": "Quick meditation",
        "description": "Sit comfortably, close your eyes, and focus on your breathing for a few minutes.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["meditation", "mindful", "mindfulness", "yoga", "calm", "zen"],
        "tags": ["mindful", "screen_free", "quiet"],
        "reason": "Even a brief breathing pause measurably reduces stress and sharpens focus."
    },
    {
        "name": "Watch something short",
        "description": "Pull up a short video or an episode of something you enjoy and fully relax.",
        "short_mins": 15, "long_mins": 30,
        "hobby_keywords": ["tv", "movies", "netflix", "youtube", "film", "anime", "shows"],
        "tags": ["screen", "entertaining", "relaxing"],
        "reason": "Passive entertainment lets your brain rest without demanding more from you."
    },
    {
        "name": "Write in a journal",
        "description": "Spend a few minutes writing whatever is on your mind — thoughts, feelings, anything.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["journaling", "writing", "diary", "blogging", "journal"],
        "tags": ["reflective", "screen_free", "quiet"],
        "reason": "Getting thoughts out of your head and onto paper clears mental clutter."
    },
    {
        "name": "Quick workout",
        "description": "A few minutes of jumping jacks, push-ups, or whatever exercise you enjoy.",
        "short_mins": 5, "long_mins": 20,
        "hobby_keywords": ["gym", "fitness", "workout", "exercise", "running", "sport", "crossfit"],
        "tags": ["physical", "energetic", "screen_free"],
        "reason": "Short bursts of exercise release endorphins and boost your energy almost immediately."
    },
    {
        "name": "Text or call a friend",
        "description": "Reach out to someone — even a quick message to check in goes a long way.",
        "short_mins": 5, "long_mins": 15,
        "hobby_keywords": ["social", "friends", "family", "people", "chat"],
        "tags": ["social", "relaxing"],
        "reason": "A quick social connection reminds you there is life outside the to-do list."
    },
    {
        "name": "Step outside for fresh air",
        "description": "Go outside, even just to your doorstep or balcony, and breathe for a minute.",
        "short_mins": 5, "long_mins": 10,
        "hobby_keywords": ["outdoor", "nature", "garden", "balcony"],
        "tags": ["outdoor", "screen_free", "mindful"],
        "reason": "Fresh air and a change of scenery is one of the simplest and most effective resets."
    },
]

_SCREEN_WORK_WORDS = {
    'computer', 'coding', 'code', 'screen', 'design', 'writing', 'office',
    'desk', 'remote', 'laptop', 'developer', 'engineer', 'analyst', 'research',
    'editing', 'student', 'studying', 'homework', 'assignment',
}


def suggest_break_local(date):
    """Rule-based break suggestion using profile + today's tasks + recent task history.
    No API key required."""
    db = get_db()
    profile = db.execute('SELECT * FROM user_profile ORDER BY id LIMIT 1').fetchone()
    today_tasks = db.execute(
        'SELECT * FROM tasks WHERE date = ? ORDER BY start_time', (date,)
    ).fetchall()
    recent_tasks = db.execute(
        "SELECT * FROM tasks WHERE date < ? AND date >= date(?, '-7 days')",
        (date, date)
    ).fetchall()

    hobbies     = (profile['hobbies'] or '').lower()           if profile else ''
    work        = (profile['work_description'] or '').lower()  if profile else ''
    break_style = profile['break_style']                       if profile else 'frequent_short'

    # Detect screen-heavy work from profile
    screen_heavy = any(w in work for w in _SCREEN_WORK_WORDS)

    # Collect task categories from today + recent days for context
    def _cats(tasks):
        return [t['category'].lower() for t in tasks if t['category']]

    today_cats  = _cats(today_tasks)
    recent_cats = _cats(recent_tasks)
    all_cats    = today_cats + recent_cats

    # Dominant category this week (most frequent)
    dominant = max(set(all_cats), key=all_cats.count) if all_cats else None

    # If most tasks are screen/work/study, treat as screen-heavy regardless of profile
    screen_task_words = {'work', 'study', 'school', 'coding', 'homework', 'writing', 'research'}
    if dominant and any(w in dominant for w in screen_task_words):
        screen_heavy = True

    # Date-based offset so suggestions rotate day to day
    day_seed = int(hashlib.md5(date.encode()).hexdigest(), 16)

    scored = []
    for i, act in enumerate(_ACTIVITY_POOL):
        score = 0.0

        # Hobby keyword match — strongest signal
        for kw in act['hobby_keywords']:
            if kw in hobbies:
                score += 5

        # Boost screen-free activities for screen-heavy workers/days
        if screen_heavy and 'screen_free' in act['tags']:
            score += 3
        # Penalise screen entertainment for screen-heavy days
        if screen_heavy and 'screen' in act['tags'] and 'screen_free' not in act['tags']:
            score -= 3

        # Boost physical/outdoor if today is packed with desk-style tasks
        if screen_heavy and 'physical' in act['tags']:
            score += 2
        if screen_heavy and 'outdoor' in act['tags']:
            score += 1

        # Variety: rotate priority across activities using a daily seed
        variety = ((i + day_seed) % len(_ACTIVITY_POOL)) / len(_ACTIVITY_POOL)
        score += variety

        scored.append((score, i, act))

    scored.sort(key=lambda x: x[0], reverse=True)
    best = scored[0][2]

    duration = best['short_mins'] if break_style == 'frequent_short' else best['long_mins']

    # Personalise the reason with today's context when possible
    reason = best['reason']
    if dominant and screen_heavy and 'screen_free' in best['tags']:
        reason = f"After a day of {dominant} work, stepping away from your screen will help you recharge. {reason}"
    elif dominant:
        reason = f"With a day focused on {dominant}, {reason[0].lower()}{reason[1:]}"

    return {
        "name": best['name'],
        "description": best['description'],
        "duration_minutes": duration,
        "reason": reason,
    }

_client = None
MODEL_FAST = 'claude-haiku-4-5-20251001'
MODEL_FULL = 'claude-sonnet-4-6'


def _parse_json(text):
    text = re.sub(r'^```(?:json)?\s*', '', text.strip())
    text = re.sub(r'\s*```$', '', text.strip())
    return json.loads(text.strip())


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

    result = json.loads(response.content[0].text)
    # If the day is overscheduled, a break nudge should always show too
    if result.get('overscheduled') and not result.get('needs_break'):
        result['needs_break'] = True
        if not result.get('break_message'):
            result['break_message'] = "With a day this packed, a short break will help you stay focused and finish strong."
    return result


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

    return _parse_json(response.content[0].text)


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

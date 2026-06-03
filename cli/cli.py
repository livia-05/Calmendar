import click
import httpx
from datetime import date as dt

BASE_URL = 'http://127.0.0.1:5000'

STATUS_ICONS = {
    'not_started': '○',
    'in_progress':  '◐',
    'completed':    '●',
}

PRIORITY_COLORS = {
    'high':   'red',
    'medium': 'yellow',
    'low':    'green',
}


def api(method, path, **kwargs):
    try:
        r = httpx.request(method, f'{BASE_URL}{path}', **kwargs)
        r.raise_for_status()
        if r.status_code == 204:
            return None
        return r.json()
    except httpx.ConnectError:
        click.echo(click.style(
            'Error: server is not running. Start it with: uv run python run.py', fg='red'
        ))
        raise SystemExit(1)
    except httpx.HTTPStatusError as e:
        try:
            msg = e.response.json().get('error', str(e))
        except Exception:
            msg = str(e)
        click.echo(click.style(f'Error: {msg}', fg='red'))
        raise SystemExit(1)


@click.group()
def cli():
    """Calmendar — your mindful daily planner."""
    pass


# ── Tasks ──────────────────────────────────────────────────────────────────

@cli.group()
def tasks():
    """Manage your daily tasks."""
    pass


@tasks.command('list')
@click.option('--date', 'target_date', default=str(dt.today()), show_default=True,
              help='Date to list tasks for (YYYY-MM-DD)')
def list_tasks(target_date):
    """List tasks for a given date."""
    items = api('GET', '/api/tasks', params={'date': target_date})
    if not items:
        click.echo(f'No tasks for {target_date}.')
        return
    click.echo(click.style(f'\nTasks for {target_date}', bold=True))
    for t in items:
        icon  = STATUS_ICONS.get(t['status'], '?')
        color = PRIORITY_COLORS.get(t['priority'], 'white')
        time_str = (click.style(f"  {t['start_time']}–{t['end_time']}", dim=True)
                    if t['start_time'] else '')
        click.echo(
            f"  {icon} [{t['id']}] "
            + click.style(t['title'], fg=color)
            + time_str
        )


@tasks.command('add')
def add_task():
    """Add a new task (interactive)."""
    title    = click.prompt('Title')
    date     = click.prompt('Date (YYYY-MM-DD)', default=str(dt.today()))
    start    = click.prompt('Start time HH:MM  (leave blank to skip)', default='', show_default=False) or None
    end      = click.prompt('End time   HH:MM  (leave blank to skip)', default='', show_default=False) or None
    priority = click.prompt('Priority', type=click.Choice(['low', 'medium', 'high']), default='medium')
    category = click.prompt('Category           (leave blank to skip)', default='', show_default=False) or None
    notes    = click.prompt('Notes              (leave blank to skip)', default='', show_default=False) or None

    task = api('POST', '/api/tasks', json={
        'title': title, 'date': date, 'start_time': start, 'end_time': end,
        'priority': priority, 'category': category, 'notes': notes,
    })
    click.echo(click.style(f'\n○ Task added (id {task["id"]}): {task["title"]}', fg='green'))


@tasks.command('status')
@click.argument('task_id', type=int)
@click.argument('status', type=click.Choice(['not_started', 'in_progress', 'completed']))
def set_status(task_id, status):
    """Update a task's status.\n\nSTATUS: not_started | in_progress | completed"""
    task = api('PUT', f'/api/tasks/{task_id}', json={'status': status})
    icon = STATUS_ICONS[task['status']]
    click.echo(f'{icon}  [{task["id"]}] {task["title"]} → {click.style(status, bold=True)}')


@tasks.command('delete')
@click.argument('task_id', type=int)
def delete_task(task_id):
    """Delete a task by ID."""
    if click.confirm(f'Delete task {task_id}?'):
        api('DELETE', f'/api/tasks/{task_id}')
        click.echo(click.style('Deleted.', fg='yellow'))


# ── Breaks ─────────────────────────────────────────────────────────────────

@cli.group()
def breaks():
    """Browse and manage break activities."""
    pass


@breaks.command('list')
@click.option('--screen-free', is_flag=True, help='Only show screen-free activities')
@click.option('--favorites',   is_flag=True, help='Only show favorited activities')
def list_breaks(screen_free, favorites):
    """List available break activities."""
    params = {}
    if screen_free:
        params['screen_free'] = 1
    if favorites:
        params['favorited'] = 1
    items = api('GET', '/api/breaks', params=params)
    if not items:
        click.echo('No break activities found.')
        return
    click.echo(click.style('\nBreak Activities', bold=True))
    for b in items:
        fav      = click.style('♥ ', fg='magenta') if b['is_favorited'] else '  '
        screen   = click.style(' [screen]', dim=True) if not b['is_screen_free'] else ''
        duration = click.style(f"  {b['duration_minutes']}min", dim=True) if b['duration_minutes'] else ''
        click.echo(f"  {fav}[{b['id']}] {b['name']}{duration}{screen}")


@breaks.command('favorite')
@click.argument('break_id', type=int)
def favorite_break(break_id):
    """Toggle favorite on a break activity."""
    b = api('PUT', f'/api/breaks/{break_id}/favorite')
    state = click.style('favorited ♥', fg='magenta') if b['is_favorited'] else 'unfavorited'
    click.echo(f'{b["name"]} {state}.')


@breaks.command('add')
def add_break():
    """Add a custom break activity."""
    name        = click.prompt('Name')
    description = click.prompt('Description (leave blank to skip)', default='', show_default=False) or None
    category    = click.prompt('Category    (leave blank to skip)', default='', show_default=False) or None
    duration    = click.prompt('Duration in minutes (leave blank to skip)', default='', show_default=False)
    screen_free = click.confirm('Is this screen-free?', default=True)

    b = api('POST', '/api/breaks', json={
        'name': name, 'description': description, 'category': category,
        'duration_minutes': int(duration) if duration else None,
        'is_screen_free': int(screen_free),
    })
    click.echo(click.style(f'\nBreak activity added (id {b["id"]}): {b["name"]}', fg='green'))


# ── Reflect ────────────────────────────────────────────────────────────────

@cli.command()
@click.option('--date', 'target_date', default=str(dt.today()), show_default=True,
              help='Date to reflect on (YYYY-MM-DD)')
def reflect(target_date):
    """Log your end-of-day reflection."""
    click.echo(click.style(f'\nEnd-of-day reflection for {target_date}', bold=True))
    mood  = click.prompt('Mood (1–5)', type=click.IntRange(1, 5))
    notes = click.prompt('Any notes? (leave blank to skip)', default='', show_default=False) or None

    existing = api('GET', f'/api/reflections/{target_date}')
    if existing:
        r = api('PUT', f'/api/reflections/{target_date}', json={'mood': mood, 'notes': notes})
    else:
        r = api('POST', '/api/reflections', json={'date': target_date, 'mood': mood, 'notes': notes})

    click.echo(click.style('\nReflection saved.', fg='green'))
    if r and r.get('ai_summary'):
        click.echo(click.style('\n' + r['ai_summary'], italic=True))


# ── Profile ────────────────────────────────────────────────────────────────

@cli.command()
def profile():
    """Show your current profile."""
    p = api('GET', '/api/profile')
    if not p:
        click.echo('No profile found. Complete onboarding at http://127.0.0.1:5000')
        return
    click.echo(click.style(f'\nProfile: {p["name"]}', bold=True))
    for key in ['work_description', 'hobbies', 'wake_time', 'sleep_time',
                'max_daily_hours', 'break_style', 'stress_sensitivity']:
        val = p.get(key)
        if val is not None:
            click.echo(f'  {key.replace("_", " ").title()}: {val}')


if __name__ == '__main__':
    cli()

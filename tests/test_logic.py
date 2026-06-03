from server.routes.reflections import _build_summary, _CLOSERS


def _tasks(*titles):
    return [{'title': t} for t in titles]


# ── Completed tasks ───────────────────────────────────────────────────────────

def test_single_completed_task_is_named(client):
    s = _build_summary(_tasks('Write tests'), [])
    assert 'Write tests' in s


def test_multiple_completed_tasks_shows_count(client):
    s = _build_summary(_tasks('A', 'B', 'C'), [])
    assert '3' in s


def test_first_two_completed_tasks_are_named(client):
    s = _build_summary(_tasks('Task A', 'Task B', 'Task C'), [])
    assert 'Task A' in s
    assert 'Task B' in s


def test_no_completed_tasks_is_handled(client):
    s = _build_summary([], _tasks('Pending task'))
    assert 'lighter day' in s


# ── Pending tasks ─────────────────────────────────────────────────────────────

def test_single_pending_task_is_named(client):
    s = _build_summary([], _tasks('Review PR'))
    assert 'Review PR' in s


def test_multiple_pending_shows_count(client):
    s = _build_summary([], _tasks('A', 'B', 'C'))
    assert '3' in s


def test_no_pending_says_all_done(client):
    s = _build_summary(_tasks('Finished task'), [])
    assert 'Everything on your list is done' in s


# ── Uplifting closer ──────────────────────────────────────────────────────────

def test_summary_always_ends_with_closer(client):
    s = _build_summary([], [])
    assert any(closer in s for closer in _CLOSERS)


def test_summary_has_three_parts(client):
    s = _build_summary(_tasks('Done'), _tasks('Pending'))
    sentences = [p.strip() for p in s.split('.') if p.strip()]
    assert len(sentences) >= 3

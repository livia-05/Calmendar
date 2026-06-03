-- Calmendar Database Schema

CREATE TABLE IF NOT EXISTS user_profile (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,
    work_description    TEXT,
    hobbies             TEXT,
    wake_time           TEXT,
    sleep_time          TEXT,
    max_daily_hours     INTEGER DEFAULT 8,
    break_style         TEXT CHECK(break_style IN ('frequent_short', 'infrequent_long')) DEFAULT 'frequent_short',
    stress_sensitivity  TEXT CHECK(stress_sensitivity IN ('low', 'medium', 'high')) DEFAULT 'medium',
    onboarding_complete INTEGER DEFAULT 0,
    created_at          TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    date        TEXT NOT NULL,
    start_time  TEXT,
    end_time    TEXT,
    notes       TEXT,
    priority    TEXT CHECK(priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
    category    TEXT,
    status      TEXT CHECK(status IN ('not_started', 'in_progress', 'completed')) DEFAULT 'not_started',
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reflections (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT NOT NULL UNIQUE,
    mood        INTEGER CHECK(mood BETWEEN 1 AND 5),
    notes       TEXT,
    ai_summary  TEXT,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS break_activities (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT NOT NULL,
    description      TEXT,
    category         TEXT,
    duration_minutes INTEGER,
    is_screen_free   INTEGER DEFAULT 1,
    is_custom        INTEGER DEFAULT 0,
    is_favorited     INTEGER DEFAULT 0,
    created_at       TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Default break activities
INSERT INTO break_activities (name, description, category, duration_minutes, is_screen_free) VALUES
    ('Short Walk',        'Step outside or walk around the building',         'physical',    10, 1),
    ('Stretching',        'Light full-body stretching at your desk or floor', 'physical',     5, 1),
    ('Breathing Exercise','Box breathing or 4-7-8 technique to reset focus',  'mindfulness',  5, 1),
    ('Grab a Snack',      'Step away and have a healthy snack',               'rest',         5, 1),
    ('Quick Meditation',  'Guided or silent meditation to clear your mind',   'mindfulness', 10, 1),
    ('Journal',           'Free-write thoughts or a gratitude list',          'creative',    10, 1),
    ('Listen to Music',   'Put on a favorite playlist and decompress',        'rest',        10, 0),
    ('Watch a Video',     'Short video or show episode',                      'rest',        15, 0),
    ('Doodle / Sketch',   'Draw or doodle freely, no pressure',               'creative',    10, 1),
    ('Call a Friend',     'Quick catch-up call with someone you like',        'social',      10, 1);

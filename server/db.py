import sqlite3

from flask import current_app, g

from services.seed_service import seed_database



SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    currency_code TEXT NOT NULL DEFAULT 'INR',
    created_by_user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by_user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS group_members (
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, user_id),
    FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id),
    CHECK (role IN ('owner', 'member'))
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    payer_user_id INTEGER NOT NULL,
    created_by_user_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    amount_paise INTEGER NOT NULL,
    currency_code TEXT NOT NULL DEFAULT 'INR',
    expense_date TEXT NOT NULL,
    split_mode TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'manual',
    notes TEXT,
    ai_confidence REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE,
    FOREIGN KEY (payer_user_id) REFERENCES users (id),
    FOREIGN KEY (created_by_user_id) REFERENCES users (id),
    CHECK (amount_paise > 0),
    CHECK (split_mode IN ('equal_all', 'equal_subset', 'custom', 'weights')),
    CHECK (source_type IN ('manual', 'ai_natural_language', 'ai_bill_text'))
);

CREATE TABLE IF NOT EXISTS expense_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    amount_paise INTEGER NOT NULL,
    weight INTEGER,
    share_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (expense_id) REFERENCES expenses (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id),
    CHECK (amount_paise >= 0),
    CHECK (weight IS NULL OR weight > 0)
);

CREATE TABLE IF NOT EXISTS expense_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    amount_paise INTEGER NOT NULL,
    assigned_user_ids_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (expense_id) REFERENCES expenses (id) ON DELETE CASCADE,
    CHECK (amount_paise >= 0)
);

CREATE INDEX IF NOT EXISTS idx_group_members_user_id
    ON group_members (user_id);

CREATE INDEX IF NOT EXISTS idx_expenses_group_id
    ON expenses (group_id);

CREATE INDEX IF NOT EXISTS idx_expenses_expense_date
    ON expenses (expense_date DESC);

CREATE INDEX IF NOT EXISTS idx_expense_shares_expense_id
    ON expense_shares (expense_id);

CREATE INDEX IF NOT EXISTS idx_expense_items_expense_id
    ON expense_items (expense_id);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(SCHEMA_SQL)
    db.commit()


def seed_db():
    db = get_db()
    user_count = db.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
    if user_count == 0:
        seed_database(db)


def init_app(app):
    app.teardown_appcontext(close_db)

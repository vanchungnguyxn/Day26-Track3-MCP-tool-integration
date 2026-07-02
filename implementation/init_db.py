"""Initialize the SQLite database with schema and seed data."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "lab.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cohort TEXT NOT NULL,
    score REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    instructor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    grade REAL,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
"""

SEED_SQL = """
INSERT INTO students (name, cohort, score) VALUES
    ('Alice Nguyen', 'A1', 92.5),
    ('Bob Tran', 'A1', 78.0),
    ('Carol Le', 'B2', 88.5),
    ('David Pham', 'B2', 95.0),
    ('Eva Hoang', 'A1', 84.0);

INSERT INTO courses (title, instructor) VALUES
    ('Database Systems', 'Dr. Linh'),
    ('Machine Learning', 'Prof. Minh'),
    ('Web Development', 'Ms. Hana');

INSERT INTO enrollments (student_id, course_id, grade) VALUES
    (1, 1, 90.0),
    (1, 2, 94.0),
    (2, 1, 75.0),
    (3, 2, 89.0),
    (4, 3, 96.0),
    (5, 1, 82.0);
"""


def create_database(db_path: Path | str | None = None, force: bool = False) -> Path:
    """Create the SQLite database file, apply schema, and insert seed rows."""
    path = Path(db_path) if db_path else DB_PATH

    if force and path.exists():
        path.unlink()

    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA_SQL)
        if force or _is_empty(conn):
            conn.executescript(SEED_SQL)
        conn.commit()
    finally:
        conn.close()

    return path


def _is_empty(conn: sqlite3.Connection) -> bool:
    cursor = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='students'"
    )
    if cursor.fetchone()[0] == 0:
        return True

    cursor = conn.execute("SELECT COUNT(*) FROM students")
    return cursor.fetchone()[0] == 0


if __name__ == "__main__":
    created = create_database(force=True)
    print(f"Database ready at {created}")

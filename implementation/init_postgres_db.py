"""PostgreSQL schema and seed helpers."""

from __future__ import annotations

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    cohort TEXT NOT NULL,
    score DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    instructor TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS enrollments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    course_id INTEGER NOT NULL REFERENCES courses(id),
    grade DOUBLE PRECISION
);
"""

SEED_SQL = """
INSERT INTO students (name, cohort, score)
SELECT * FROM (VALUES
    ('Alice Nguyen', 'A1', 92.5),
    ('Bob Tran', 'A1', 78.0),
    ('Carol Le', 'B2', 88.5),
    ('David Pham', 'B2', 95.0),
    ('Eva Hoang', 'A1', 84.0)
) AS seed(name, cohort, score)
WHERE NOT EXISTS (SELECT 1 FROM students);

INSERT INTO courses (title, instructor)
SELECT * FROM (VALUES
    ('Database Systems', 'Dr. Linh'),
    ('Machine Learning', 'Prof. Minh'),
    ('Web Development', 'Ms. Hana')
) AS seed(title, instructor)
WHERE NOT EXISTS (SELECT 1 FROM courses);

INSERT INTO enrollments (student_id, course_id, grade)
SELECT * FROM (VALUES
    (1, 1, 90.0),
    (1, 2, 94.0),
    (2, 1, 75.0),
    (3, 2, 89.0),
    (4, 3, 96.0),
    (5, 1, 82.0)
) AS seed(student_id, course_id, grade)
WHERE NOT EXISTS (SELECT 1 FROM enrollments);
"""


def create_database(connection_url: str) -> None:
    """Apply schema and seed data to a PostgreSQL database."""
    import psycopg

    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(SCHEMA_SQL)
            cursor.execute(SEED_SQL)
        conn.commit()


if __name__ == "__main__":
    import os
    import sys

    url = os.getenv("DATABASE_URL")
    if not url:
        print("Set DATABASE_URL before running init_postgres_db.py", file=sys.stderr)
        sys.exit(1)
    create_database(url)
    print(f"PostgreSQL database ready at {url}")

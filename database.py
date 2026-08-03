import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("data", "story_studio.db")

def init_db():
    """Initializes the SQLite database with required tables and handles migrations."""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create chapters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chapters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            storyline TEXT,
            content TEXT,
            tone TEXT,
            length TEXT,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    ''')

    # Migration check for new columns
    cursor.execute("PRAGMA table_info(chapters)")
    columns = [row[1] for row in cursor.fetchall()]
    if "summary" not in columns:
        cursor.execute("ALTER TABLE chapters ADD COLUMN summary TEXT")
    if "provider" not in columns:
        cursor.execute("ALTER TABLE chapters ADD COLUMN provider TEXT")
    if "model" not in columns:
        cursor.execute("ALTER TABLE chapters ADD COLUMN model TEXT")
    if "writing_profile" not in columns:
        cursor.execute("ALTER TABLE chapters ADD COLUMN writing_profile TEXT")

    conn.commit()
    conn.close()

def create_project(name):
    """Creates a new project in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO projects (name) VALUES (?)", (name,))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_all_projects():
    """Returns a list of all projects."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM projects ORDER BY name")
    projects = cursor.fetchall()
    conn.close()
    return projects

def save_chapter(project_id, title, storyline, content, tone, length, summary=None, provider=None, model=None, writing_profile=None):
    """Saves a generated chapter to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chapters (project_id, title, storyline, content, tone, length, summary, provider, model, writing_profile)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (project_id, title, storyline, content, tone, length, summary, provider, model, writing_profile))
    conn.commit()
    chapter_id = cursor.lastrowid
    conn.close()
    return chapter_id

def get_chapters_by_project(project_id):
    """Retrieves all chapters for a specific project."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, storyline, content, tone, length, summary, created_at, provider, model, writing_profile 
        FROM chapters 
        WHERE project_id = ? 
        ORDER BY created_at DESC
    ''', (project_id,))
    chapters = cursor.fetchall()
    conn.close()
    return chapters

def update_chapter_summary(chapter_id, summary):
    """Updates the summary for a specific chapter."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE chapters
        SET summary = ?
        WHERE id = ?
    ''', (summary, chapter_id))
    conn.commit()
    conn.close()

def get_latest_story_context(project_id, limit=5):
    """
    Retrieves summaries from the latest saved chapters in chronological order.
    Ignores chapters whose summary is empty or None.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # First, select the latest chapters with summaries in descending order of id, limited to limit
    # Then order that subquery in ascending order to return them chronologically.
    cursor.execute('''
        SELECT summary FROM (
            SELECT id, summary 
            FROM chapters 
            WHERE project_id = ? AND summary IS NOT NULL AND summary != ''
            ORDER BY id DESC 
            LIMIT ?
        )
        ORDER BY id ASC
    ''', (project_id, limit))
    summaries = [row[0] for row in cursor.fetchall()]
    conn.close()
    return summaries

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")

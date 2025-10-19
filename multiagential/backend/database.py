import sqlite3
import json
from typing import List, Dict

DB_FILE = "adaptive_learning.db"

def init_db():
    """Initializes the database and creates the tables if they don't exist."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Quizzes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                id TEXT PRIMARY KEY,
                questions TEXT NOT NULL
            )
        """)
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY
            )
        """)
        # Progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                user_id TEXT PRIMARY KEY,
                current_topic TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Course enrollments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_enrollments (
                user_id TEXT,
                course_id TEXT,
                enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_module_id TEXT,
                PRIMARY KEY (user_id, course_id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Module progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS module_progress (
                user_id TEXT,
                course_id TEXT,
                module_id TEXT,
                completed BOOLEAN DEFAULT FALSE,
                completed_at DATETIME,
                PRIMARY KEY (user_id, course_id, module_id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        conn.commit()

def create_user(user_id: str):
    """Creates a new user."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
        conn.commit()

def get_user(user_id: str) -> bool:
    """Checks if a user exists."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone() is not None

def update_progress(user_id: str, topic: str):
    """Updates the user's progress."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO progress (user_id, current_topic) VALUES (?, ?)",
            (user_id, topic)
        )
        conn.commit()

def get_progress(user_id: str) -> str:
    """Gets the user's progress."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT current_topic FROM progress WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def store_quiz(quiz_id: str, questions: List[Dict]):
    """Stores a quiz in the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO quizzes (id, questions) VALUES (?, ?)",
            (quiz_id, json.dumps(questions))
        )
        conn.commit()

def get_quiz(quiz_id: str) -> List[Dict]:
    """Retrieves a quiz from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT questions FROM quizzes WHERE id = ?", (quiz_id,))
        result = cursor.fetchone()
        if result:
            return json.loads(result[0])
        return None

def delete_quiz(quiz_id: str):
    """Deletes a quiz from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
        conn.commit()

# Course management functions

def enroll_user_in_course(user_id: str, course_id: str):
    """Enrolls a user in a course."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO course_enrollments (user_id, course_id, enrolled_at, last_accessed) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (user_id, course_id)
        )
        conn.commit()

def update_course_access(user_id: str, course_id: str, module_id: str = None):
    """Updates the last accessed time and module for a course."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        if module_id:
            cursor.execute(
                "UPDATE course_enrollments SET last_accessed = CURRENT_TIMESTAMP, last_module_id = ? WHERE user_id = ? AND course_id = ?",
                (module_id, user_id, course_id)
            )
        else:
            cursor.execute(
                "UPDATE course_enrollments SET last_accessed = CURRENT_TIMESTAMP WHERE user_id = ? AND course_id = ?",
                (user_id, course_id)
            )
        conn.commit()

def get_user_enrollments(user_id: str) -> List[Dict]:
    """Gets all course enrollments for a user with last access info."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT course_id, enrolled_at, last_accessed, last_module_id FROM course_enrollments WHERE user_id = ? ORDER BY last_accessed DESC",
            (user_id,)
        )
        results = cursor.fetchall()
        return [
            {
                "course_id": row[0],
                "enrolled_at": row[1],
                "last_accessed": row[2],
                "last_module_id": row[3]
            }
            for row in results
        ]

def update_module_progress(user_id: str, course_id: str, module_id: str, completed: bool):
    """Updates progress for a specific module."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        if completed:
            cursor.execute(
                "INSERT OR REPLACE INTO module_progress (user_id, course_id, module_id, completed, completed_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (user_id, course_id, module_id, completed)
            )
        else:
            cursor.execute(
                "INSERT OR REPLACE INTO module_progress (user_id, course_id, module_id, completed) VALUES (?, ?, ?, ?)",
                (user_id, course_id, module_id, completed)
            )
        conn.commit()

def get_course_progress(user_id: str, course_id: str) -> Dict[str, bool]:
    """Gets module completion status for a specific course."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT module_id, completed FROM module_progress WHERE user_id = ? AND course_id = ?",
            (user_id, course_id)
        )
        results = cursor.fetchall()
        return {row[0]: bool(row[1]) for row in results}

def get_user_course_summary(user_id: str) -> Dict:
    """Gets a summary of user's course activity."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Get total enrollments
        cursor.execute("SELECT COUNT(*) FROM course_enrollments WHERE user_id = ?", (user_id,))
        total_enrollments = cursor.fetchone()[0]
        
        # Get total completed modules
        cursor.execute("SELECT COUNT(*) FROM module_progress WHERE user_id = ? AND completed = 1", (user_id,))
        completed_modules = cursor.fetchone()[0]
        
        # Get most recently accessed course
        cursor.execute(
            "SELECT course_id, last_module_id FROM course_enrollments WHERE user_id = ? ORDER BY last_accessed DESC LIMIT 1",
            (user_id,)
        )
        recent_course = cursor.fetchone()
        
        return {
            "total_enrollments": total_enrollments,
            "completed_modules": completed_modules,
            "recent_course_id": recent_course[0] if recent_course else None,
            "recent_module_id": recent_course[1] if recent_course else None
        }

import sqlite3
import os

def record_wrong_answer(item_id: str, loss_reason: str = "概念錯誤"):
    """
    Writes a wrong answer back to the RDQ Shared SQLite DB.
    """
    env_path = os.environ.get("ECOSYSTEM_DB_PATH")
    db_path = env_path if env_path else "~/.education_ecosystem/review_index.db"
    db_path = os.path.expanduser(db_path)

    if not os.path.exists(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # Create DB if it doesn't exist just in case, though RDQ should create it
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT DEFAULT 'local_user',
                item_id TEXT NOT NULL,
                status TEXT NOT NULL,
                loss_reason TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
    else:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

    try:
        # Simple insert for the mock logic
        cursor.execute(
            "INSERT INTO review_index (item_id, status, loss_reason) VALUES (?, ?, ?)",
            (item_id, 'uncertain', loss_reason)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error writing to DB: {e}")
        return False
    finally:
        conn.close()

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
        # For AntiGravity's new schema we also need 'priority' column
        try:
            cursor.execute("ALTER TABLE review_index ADD COLUMN priority TEXT")
        except sqlite3.OperationalError:
            pass

        cursor.execute(
            "INSERT INTO review_index (item_id, status, loss_reason, priority) VALUES (?, ?, ?, ?)",
            (item_id, 'uncertain', loss_reason, 'red')
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error writing to DB: {e}")
        return False
    finally:
        conn.close()

def inject_sample_wrong_questions():
    """Injects 15 sample wrong questions into the RDQ DB for testing the dashboard."""
    env_path = os.environ.get("ECOSYSTEM_DB_PATH")
    db_path = env_path if env_path else "~/.education_ecosystem/review_index.db"
    db_path = os.path.expanduser(db_path)

    if not os.path.exists(db_path):
        record_wrong_answer("init", "init")

    samples = [
        ("chi_read_01", "看錯題", "red"), ("chi_verb_02", "概念錯誤", "yellow"), ("chi_noun_03", "看錯題", "green"),
        ("math_geo_01", "計算錯誤", "red"), ("math_alg_02", "推理不足", "yellow"), ("math_stat_03", "看錯題", "red"),
        ("soc_his_01", "概念錯誤", "yellow"), ("soc_geo_02", "概念錯誤", "red"), ("soc_civ_03", "看錯題", "green"),
        ("sci_bio_01", "推理不足", "red"), ("sci_phy_02", "概念錯誤", "yellow"), ("sci_che_03", "計算錯誤", "green"),
        ("eng_gram_01", "概念錯誤", "red"), ("eng_vocab_02", "看錯題", "yellow"), ("eng_read_03", "推理不足", "green")
    ]

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE review_index ADD COLUMN priority TEXT")
    except sqlite3.OperationalError:
        pass

    for item_id, reason, prio in samples:
        cursor.execute(
            "INSERT INTO review_index (item_id, status, loss_reason, priority) VALUES (?, ?, ?, ?)",
            (item_id, 'uncertain', reason, prio)
        )
    conn.commit()
    conn.close()

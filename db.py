import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Config dictionary (safe even if password has @ or special chars)
CFG = {
    "dbname": os.getenv("PG_DB", "hackdb"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASS", "1234"),
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_PORT", "5432"),
}


def init_db():
    """Create essays table if it does not exist"""
    conn = psycopg2.connect(**CFG)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS essays (
        id SERIAL PRIMARY KEY,
        student_id TEXT,
        original_text TEXT NOT NULL,
        corrected_text TEXT NOT NULL,
        feedback TEXT NOT NULL,
        model_name TEXT NOT NULL,
        latency_ms INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database initialized (essays table ready).")


def insert_essay(student_id, original, corrected, feedback, model_name, latency_ms):
    """Insert one essay into DB and return new essay ID"""
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**CFG)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO essays (student_id, original_text, corrected_text, feedback, model_name, latency_ms)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (student_id, original, corrected, feedback, model_name, latency_ms)
        )
        eid = cur.fetchone()
        conn.commit()
        if eid:
            print(f"✅ Essay inserted with ID: {eid[0]}")
            return eid[0]
        else:
            print("⚠️ Insert query returned no ID")
            return None
    except Exception as e:
        print("❌ DB Insert Failed:", e)
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_all_essays(limit=10):
    """Fetch essays (default: last 10)"""
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(**CFG)
        cur = conn.cursor()
        cur.execute("""
            SELECT id, student_id, original_text, corrected_text, feedback, model_name, created_at
            FROM essays
            ORDER BY created_at DESC
            LIMIT %s;
        """, (limit,))
        rows = cur.fetchall()
        return rows
    except Exception as e:
        print(" Fetch essays failed:", e)
        return []
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            
if __name__ == "__main__":
    init_db()






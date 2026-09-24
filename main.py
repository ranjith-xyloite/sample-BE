from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
import time

app = FastAPI(title="XyOps Sample API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "database-1"),
        database=os.getenv("DB_NAME", "sampledb"),
        user=os.getenv("DB_USER", "sampleuser"),
        password=os.getenv("DB_PASS", "samplepass123"),
        port=int(os.getenv("DB_PORT", 5432)),
        connect_timeout=5
    )

@app.on_event("startup")
def init_db_on_startup():
    """Auto-creates the messages table on startup with retry logic so DB is immediately ready."""
    for attempt in range(10):
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                INSERT INTO messages (text) 
                SELECT 'Welcome to XyOps Sample Stack!' 
                WHERE NOT EXISTS (SELECT 1 FROM messages);
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("Database table auto-initialized successfully on startup!")
            break
        except Exception as e:
            print(f"Waiting for database to be ready (attempt {attempt+1}/10): {e}")
            time.sleep(2)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "backend", "version": "1.0.0"}

@app.get("/api/db-test")
def db_test():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM messages")
        count = cur.fetchone()[0]
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {
            "status": "connected",
            "db": os.getenv("DB_NAME", "sampledb"),
            "host": os.getenv("DB_HOST", "database-1"),
            "pg_version": version,
            "message_count": count
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/messages")
def get_messages():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.execute("SELECT id, text, created_at FROM messages ORDER BY id DESC LIMIT 20")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        items = [{"id": r[0], "text": r[1], "created_at": str(r[2])} for r in rows]
        return {"status": "ok", "messages": items}
    except Exception as e:
        return {"status": "error", "messages": [], "detail": str(e)}

@app.post("/api/messages")
def add_message(payload: dict):
    text = payload.get("text", "")
    if not text:
        return {"status": "error", "detail": "Text cannot be empty"}
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.execute("INSERT INTO messages (text) VALUES (%s) RETURNING id, created_at", (text,))
        res = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "created", "id": res[0], "created_at": str(res[1]), "text": text}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

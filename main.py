from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os

app = FastAPI(title="XyOps Sample API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_HOST = os.getenv("DB_HOST", "database-1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "sampledb")
DB_USER = os.getenv("DB_USER", "sampleuser")
DB_PASS = os.getenv("DB_PASS", "samplepass123")

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "backend", "version": "1.0.0"}

@app.get("/api/db-test")
def db_test():
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM messages;")
        count = cur.fetchone()[0]
        cur.close(); conn.close()
        return {"status": "connected", "db": DB_NAME, "host": DB_HOST, "pg_version": version, "message_count": count}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/messages")
def get_messages():
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("SELECT id, text, created_at FROM messages ORDER BY created_at DESC LIMIT 20;")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return {"messages": [{"id": r[0], "text": r[1], "created_at": str(r[2])} for r in rows]}
    except Exception as e:
        return {"messages": [], "error": str(e)}

@app.post("/api/messages")
def add_message(payload: dict):
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS, connect_timeout=5)
        cur = conn.cursor()
        cur.execute("INSERT INTO messages (text) VALUES (%s) RETURNING id;", (payload.get("text", "Hello!"),))
        new_id = cur.fetchone()[0]
        conn.commit(); cur.close(); conn.close()
        return {"id": new_id, "text": payload.get("text"), "status": "created"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

import psycopg2
import psycopg2.extras
from app.utils.logger import get_logger
from datetime import datetime, timezone
import json

logger = get_logger(__name__)

DB_CONFIG = {
    "dbname": "health_monitor_db",
    "user": "health_user",
    "password": "health_password",
    "host": "localhost",
    "port": "5432",
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Postgres connection error: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS health_logs (
                        id SERIAL PRIMARY KEY,
                        session_id VARCHAR(255) NOT NULL,
                        timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        condition VARCHAR(255),
                        systolic_bp INT,
                        diastolic_bp INT,
                        sugar_fasting FLOAT,
                        sugar_postmeal FLOAT,
                        weight_kg FLOAT,
                        mood VARCHAR(100),
                        symptoms TEXT[],
                        notes TEXT
                    );
                """)
            conn.commit()
            logger.info("Postgres health_logs table initialized.")
        except Exception as e:
            logger.error(f"Error initializing Postgres: {e}")
        finally:
            conn.close()

def insert_health_log(entry: dict):
    conn = get_db_connection()
    if not conn:
        return
    try:
        # Avoid KeyError if symptom is missing by pulling directly from the entry
        val_entry = {k: v for k, v in entry.items()}
        if 'timestamp' not in val_entry:
            val_entry['timestamp'] = datetime.now(timezone.utc).isoformat()
            
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO health_logs (
                    session_id, timestamp, condition, systolic_bp, diastolic_bp, 
                    sugar_fasting, sugar_postmeal, weight_kg, mood, symptoms, notes
                ) VALUES (
                    %(session_id)s, %(timestamp)s, %(condition)s, %(systolic_bp)s, %(diastolic_bp)s,
                    %(sugar_fasting)s, %(sugar_postmeal)s, %(weight_kg)s, %(mood)s, %(symptoms)s, %(notes)s
                )
            """, {
                'session_id': val_entry.get('session_id'),
                'timestamp': val_entry.get('timestamp'),
                'condition': val_entry.get('condition'),
                'systolic_bp': val_entry.get('systolic_bp'),
                'diastolic_bp': val_entry.get('diastolic_bp'),
                'sugar_fasting': val_entry.get('sugar_fasting'),
                'sugar_postmeal': val_entry.get('sugar_postmeal'),
                'weight_kg': val_entry.get('weight_kg'),
                'mood': val_entry.get('mood'),
                'symptoms': val_entry.get('symptoms') or [],
                'notes': val_entry.get('notes'),
            })
        conn.commit()
    except Exception as e:
        logger.error(f"Error inserting into Postgres: {e}")
    finally:
        conn.close()

def get_health_logs_by_session(session_id: str):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT * FROM health_logs 
                WHERE session_id = %s 
                ORDER BY timestamp ASC
            """, (session_id,))
            rows = cur.fetchall()
            
            # Format timestamp back to ISO
            result = []
            for r in rows:
                d = dict(r)
                if isinstance(d['timestamp'], datetime):
                    d['timestamp'] = d['timestamp'].isoformat()
                result.append(d)
                
            return result
    except Exception as e:
        logger.error(f"Error fetching from Postgres: {e}")
        return []
    finally:
        conn.close()

def get_all_postgres_logs():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT * FROM health_logs ORDER BY timestamp DESC LIMIT 200")
            rows = cur.fetchall()
            
            result = []
            for r in rows:
                d = dict(r)
                if isinstance(d['timestamp'], datetime):
                    d['timestamp'] = d['timestamp'].isoformat()
                result.append(d)
                
            return result
    except Exception as e:
        logger.error(f"Error fetching all from Postgres: {e}")
        return []
    finally:
        conn.close()

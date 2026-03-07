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
    "host": "127.0.0.1",
    "port": "5433",
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
                        chronic_disease VARCHAR(255),
                        systolic_bp INT,
                        diastolic_bp INT,
                        sugar_fasting FLOAT,
                        sugar_postmeal FLOAT,
                        weight_kg FLOAT,
                        mood VARCHAR(100),
                        symptoms TEXT[],
                        notes TEXT
                    );
                    
                    -- Add column if it doesn't exist for backward compatibility
                    ALTER TABLE health_logs ADD COLUMN IF NOT EXISTS chronic_disease VARCHAR(255);

                    CREATE TABLE IF NOT EXISTS doctor_advice (
                        id SERIAL PRIMARY KEY,
                        session_id VARCHAR(255) NOT NULL,
                        chronic_disease VARCHAR(255) NOT NULL,
                        point TEXT NOT NULL,
                        timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
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
                    session_id, timestamp, condition, chronic_disease, systolic_bp, diastolic_bp, 
                    sugar_fasting, sugar_postmeal, weight_kg, mood, symptoms, notes
                ) VALUES (
                    %(session_id)s, %(timestamp)s, %(condition)s, %(chronic_disease)s, %(systolic_bp)s, %(diastolic_bp)s,
                    %(sugar_fasting)s, %(sugar_postmeal)s, %(weight_kg)s, %(mood)s, %(symptoms)s, %(notes)s
                )
            """, {
                'session_id': val_entry.get('session_id'),
                'timestamp': val_entry.get('timestamp'),
                'condition': val_entry.get('condition'),
                'chronic_disease': val_entry.get('chronic_disease'),
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

def get_health_logs_by_session(session_id: str, chronic_disease: str = None):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            query = "SELECT * FROM health_logs WHERE session_id = %s"
            params = [session_id]
            
            if chronic_disease:
                # Filter by chronic_disease OR (is null/General)
                query += " AND (LOWER(chronic_disease) = LOWER(%s) OR chronic_disease = 'None / General Monitoring' OR chronic_disease IS NULL)"
                params.append(chronic_disease)
                
            query += " ORDER BY timestamp ASC"
            
            cur.execute(query, tuple(params))
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


def insert_doctor_advice(session_id: str, chronic_disease: str, point: str):
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO doctor_advice (session_id, chronic_disease, point, timestamp)
                VALUES (%s, %s, %s, %s)
            """, (session_id, chronic_disease, point, datetime.now(timezone.utc).isoformat()))
        conn.commit()
    except Exception as e:
        logger.error(f"Error inserting doctor advice into Postgres: {e}")
    finally:
        conn.close()


def get_doctor_advices_by_disease(session_id: str, chronic_disease: str):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT point as content, timestamp FROM doctor_advice 
                WHERE session_id = %s AND LOWER(chronic_disease) = LOWER(%s)
                ORDER BY timestamp DESC
            """, (session_id, chronic_disease))
            rows = cur.fetchall()

            result = []
            for r in rows:
                d = dict(r)
                if isinstance(d['timestamp'], datetime):
                    d['timestamp'] = d['timestamp'].isoformat()
                result.append(d)
            return result
    except Exception as e:
        logger.error(f"Error fetching doctor advice from Postgres: {e}")
        return []
    finally:
        conn.close()


def delete_doctor_advices_by_disease(session_id: str, chronic_disease: str):
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM doctor_advice 
                WHERE session_id = %s AND LOWER(chronic_disease) = LOWER(%s)
            """, (session_id, chronic_disease))
        conn.commit()
    except Exception as e:
        logger.error(f"Error deleting doctor advice from Postgres: {e}")
    finally:
        conn.close()


def delete_health_logs_by_disease(session_id: str, chronic_disease: str):
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            # If disease is "None / General Monitoring", we might need to handle NULLs or explicit strings
            if chronic_disease.lower() in ["none / general monitoring", "general", "none"]:
                cur.execute("""
                    DELETE FROM health_logs 
                    WHERE session_id = %s AND (chronic_disease = %s OR chronic_disease IS NULL OR chronic_disease = '')
                """, (session_id, chronic_disease))
            else:
                cur.execute("""
                    DELETE FROM health_logs 
                    WHERE session_id = %s AND LOWER(chronic_disease) = LOWER(%s)
                """, (session_id, chronic_disease))
        conn.commit()
    except Exception as e:
        logger.error(f"Error deleting health logs from Postgres: {e}")
    finally:
        conn.close()

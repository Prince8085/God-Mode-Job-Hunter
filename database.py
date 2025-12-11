"""
Database module - SQLite operations for job tracking
"""
import sqlite3
import pandas as pd
from datetime import datetime
from config import BASE_DIR
import os
import json

DB_PATH = os.path.join(BASE_DIR, "jobs.db")


def get_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)


def init_db():
    """Initialize database with jobs table"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            link TEXT UNIQUE,
            description TEXT,
            salary TEXT,
            hr_email TEXT,
            keywords TEXT,
            is_scam BOOLEAN DEFAULT 0,
            domain_age_days INTEGER DEFAULT -1,
            legitimacy_score INTEGER DEFAULT 50,
            status TEXT DEFAULT 'Pending',
            resume_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create index for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON jobs(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON jobs(source)")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized!")


def add_job(job_dict: dict) -> bool:
    """
    Add new job to database.
    Returns True if added, False if duplicate.
    Auto-syncs to CSV!
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO jobs (
                source, title, company, link, description, salary,
                hr_email, keywords, is_scam, domain_age_days,
                legitimacy_score, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job_dict.get('source', 'Unknown'),
            job_dict.get('title', 'Unknown'),
            job_dict.get('company', 'Unknown'),
            job_dict.get('link', ''),
            job_dict.get('description', '')[:2000],  # Limit size
            job_dict.get('salary', 'Not Mentioned'),
            job_dict.get('hr_email', ''),
            json.dumps(job_dict.get('keywords', [])),
            1 if job_dict.get('is_scam', False) else 0,
            job_dict.get('domain_age_days', -1),
            job_dict.get('legitimacy_score', 50),
            job_dict.get('status', 'Pending')
        ))
        conn.commit()
        
        # Get the inserted job ID and sync to CSV
        job_id = cursor.lastrowid
        job_dict['id'] = job_id
        
        # Auto-sync to CSV
        try:
            from utils.csv_manager import add_job_to_csv
            add_job_to_csv(job_dict)
        except Exception as e:
            print(f"CSV sync warning: {e}")
        
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # Duplicate link
        conn.close()
        return False
    except Exception as e:
        print(f"DB Error: {e}")
        conn.close()
        return False


def get_pending_jobs(limit: int = 20) -> list:
    """Get all pending jobs"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM jobs 
        WHERE status = 'Pending' AND is_scam = 0
        ORDER BY legitimacy_score DESC, created_at DESC
        LIMIT ?
    """, (limit,))
    
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jobs


def get_job_by_id(job_id: int) -> dict:
    """Get single job by ID"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def update_status(job_id: int, status: str) -> bool:
    """Update job status - Auto-syncs to CSV!"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE jobs SET status = ? WHERE id = ?",
        (status, job_id)
    )
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    # Auto-sync to CSV
    if success:
        try:
            from utils.csv_manager import update_job_in_csv
            update_job_in_csv(job_id, {'status': status})
        except Exception as e:
            print(f"CSV sync warning: {e}")
    
    return success


def update_resume_path(job_id: int, path: str) -> bool:
    """Update resume path for a job"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE jobs SET resume_path = ? WHERE id = ?",
        (path, job_id)
    )
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def get_stats() -> dict:
    """Get job statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute("SELECT COUNT(*) FROM jobs")
    stats['total'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'Pending'")
    stats['pending'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'Applied'")
    stats['applied'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'Ignored'")
    stats['ignored'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE is_scam = 1")
    stats['scams_blocked'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT source, COUNT(*) as count FROM jobs GROUP BY source")
    stats['by_source'] = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    return stats


def get_all_jobs() -> list:
    """Get all jobs for export"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jobs


def export_to_csv(filepath: str) -> str:
    """Export all jobs to CSV file"""
    jobs = get_all_jobs()
    
    if not jobs:
        return None
    
    df = pd.DataFrame(jobs)
    df.to_csv(filepath, index=False, encoding='utf-8')
    return filepath


def clear_old_jobs(days: int = 30):
    """Clear jobs older than specified days"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM jobs 
        WHERE created_at < datetime('now', '-' || ? || ' days')
        AND status IN ('Ignored', 'Applied')
    """, (days,))
    
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

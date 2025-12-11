"""
CSV Manager - Persistent job tracking with auto-sync
All jobs are automatically saved and updated in CSV
"""
import csv
import os
from datetime import datetime
from typing import List, Dict, Optional
from config import OUTPUT_DIR

# CSV file path
CSV_FILE = os.path.join(OUTPUT_DIR, "jobs_master.csv")

# CSV columns
CSV_COLUMNS = [
    'id', 'source', 'title', 'company', 'link', 'salary', 
    'status', 'legitimacy_score', 'hr_email', 'applied_date',
    'notes', 'created_at', 'updated_at'
]


def ensure_csv_exists():
    """Create CSV file with headers if it doesn't exist"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
        print(f"📄 Created master CSV: {CSV_FILE}")
    
    return CSV_FILE


def read_all_jobs_csv() -> List[Dict]:
    """Read all jobs from CSV"""
    ensure_csv_exists()
    
    jobs = []
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                jobs.append(dict(row))
    except Exception as e:
        print(f"Error reading CSV: {e}")
    
    return jobs


def write_all_jobs_csv(jobs: List[Dict]):
    """Write all jobs to CSV (full rewrite)"""
    ensure_csv_exists()
    
    try:
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction='ignore')
            writer.writeheader()
            for job in jobs:
                writer.writerow(job)
    except Exception as e:
        print(f"Error writing CSV: {e}")


def add_job_to_csv(job: Dict) -> bool:
    """Add a new job to CSV"""
    ensure_csv_exists()
    
    # Prepare job data
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    csv_job = {
        'id': job.get('id', ''),
        'source': job.get('source', 'Unknown'),
        'title': str(job.get('title', ''))[:100],
        'company': str(job.get('company', ''))[:50],
        'link': job.get('link', ''),
        'salary': str(job.get('salary', 'Not Mentioned'))[:50],
        'status': job.get('status', 'Pending'),
        'legitimacy_score': job.get('legitimacy_score', 50),
        'hr_email': job.get('hr_email', ''),
        'applied_date': '',
        'notes': '',
        'created_at': now,
        'updated_at': now
    }
    
    try:
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction='ignore')
            writer.writerow(csv_job)
        return True
    except Exception as e:
        print(f"Error adding to CSV: {e}")
        return False


def update_job_in_csv(job_id: int, updates: Dict) -> bool:
    """Update a job's status/fields in CSV"""
    jobs = read_all_jobs_csv()
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    updated = False
    
    for job in jobs:
        if str(job.get('id')) == str(job_id):
            for key, value in updates.items():
                if key in CSV_COLUMNS:
                    job[key] = value
            job['updated_at'] = now
            
            # If status is Applied, set applied_date
            if updates.get('status') == 'Applied' and not job.get('applied_date'):
                job['applied_date'] = now
            
            updated = True
            break
    
    if updated:
        write_all_jobs_csv(jobs)
    
    return updated


def get_csv_stats() -> Dict:
    """Get statistics from CSV"""
    jobs = read_all_jobs_csv()
    
    stats = {
        'total': len(jobs),
        'pending': 0,
        'applied': 0,
        'ignored': 0,
        'by_source': {}
    }
    
    for job in jobs:
        status = job.get('status', 'Pending')
        if status == 'Pending':
            stats['pending'] += 1
        elif status == 'Applied':
            stats['applied'] += 1
        elif status == 'Ignored':
            stats['ignored'] += 1
        
        source = job.get('source', 'Unknown')
        stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
    
    return stats


def get_pending_jobs_csv(limit: int = 10) -> List[Dict]:
    """Get pending jobs from CSV"""
    jobs = read_all_jobs_csv()
    pending = [j for j in jobs if j.get('status', 'Pending') == 'Pending']
    return pending[:limit]


def get_applied_jobs_csv() -> List[Dict]:
    """Get applied jobs from CSV"""
    jobs = read_all_jobs_csv()
    return [j for j in jobs if j.get('status') == 'Applied']


def search_jobs_csv(query: str) -> List[Dict]:
    """Search jobs by title, company, or source"""
    jobs = read_all_jobs_csv()
    query = query.lower()
    
    results = []
    for job in jobs:
        if (query in str(job.get('title', '')).lower() or
            query in str(job.get('company', '')).lower() or
            query in str(job.get('source', '')).lower()):
            results.append(job)
    
    return results


def sync_db_to_csv():
    """Sync all jobs from database to CSV"""
    try:
        from database import get_all_jobs
        
        db_jobs = get_all_jobs()
        
        # Read existing CSV
        csv_jobs = read_all_jobs_csv()
        existing_ids = {str(j.get('id')) for j in csv_jobs}
        
        # Add missing jobs
        new_count = 0
        for job in db_jobs:
            if str(job.get('id')) not in existing_ids:
                add_job_to_csv(job)
                new_count += 1
        
        print(f"📄 Synced {new_count} new jobs to CSV")
        return new_count
        
    except Exception as e:
        print(f"Sync error: {e}")
        return 0


def get_csv_path() -> str:
    """Get the path to the master CSV file"""
    ensure_csv_exists()
    return CSV_FILE


def format_csv_summary() -> str:
    """Format a summary of CSV data for display"""
    stats = get_csv_stats()
    
    summary = f"""📄 *Master CSV Summary*

*Jobs Tracked:* {stats['total']}
• Pending: {stats['pending']}
• Applied: {stats['applied']}
• Ignored: {stats['ignored']}

*By Source:*
"""
    for source, count in sorted(stats['by_source'].items(), key=lambda x: -x[1])[:8]:
        summary += f"• {source}: {count}\n"
    
    summary += f"\n📁 File: `jobs_master.csv`"
    
    return summary


if __name__ == "__main__":
    # Test
    print("\n=== Testing CSV Manager ===\n")
    
    ensure_csv_exists()
    print(f"CSV Path: {CSV_FILE}")
    
    # Sync from DB
    sync_db_to_csv()
    
    # Show stats
    stats = get_csv_stats()
    print(f"\nStats: {stats}")

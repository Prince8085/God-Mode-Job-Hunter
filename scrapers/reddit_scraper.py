"""
Reddit Scraper - PRAW integration for job posts
"""
import praw
from typing import List, Dict
import re
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT


# Target subreddits for job hunting
TARGET_SUBREDDITS = [
    "developersIndia",
    "remotejobs", 
    "forhire",
    "IndiaJobs",
    "cscareerquestions",
    "jobbit",
    "remotework",
    "startupjobs"
]

# Keywords to identify hiring posts
HIRING_KEYWORDS = [
    'hiring', 'hire', 'looking for', 'job opening', 'position',
    'intern', 'developer needed', 'engineer needed', 'we are hiring',
    'join our team', 'opportunity', 'remote position', 'wfh'
]

# Keywords to EXCLUDE (people looking for jobs, not hiring)
EXCLUDE_KEYWORDS = [
    'looking for job', 'need a job', 'hire me', 'available for',
    'seeking employment', 'job search', 'resume review'
]


def extract_salary(text: str) -> str:
    """Try to extract salary from post"""
    patterns = [
        r'[\$₹]\s*(\d+[,\d]*\s*[-–to]\s*\d+[,\d]*)',
        r'(\d+)\s*[-–to]\s*(\d+)\s*(lpa|lakh|k)',
        r'salary[:\s]*(\d+[^\n]*)',
        r'ctc[:\s]*(\d+[^\n]*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(0)[:50]
    
    return "Not Mentioned"


def extract_company(text: str, title: str) -> str:
    """Try to extract company name"""
    # Common patterns
    patterns = [
        r'at\s+([A-Z][a-zA-Z0-9\s]+)',
        r'company[:\s]+([A-Za-z0-9\s]+)',
        r'\[([A-Za-z0-9\s]+)\]',
    ]
    
    combined = f"{title} {text}"
    
    for pattern in patterns:
        match = re.search(pattern, combined)
        if match:
            company = match.group(1).strip()
            if len(company) > 2 and len(company) < 50:
                return company
    
    return "Startup/Indie"


def scan_reddit(posts_per_sub: int = 25) -> List[Dict]:
    """
    Scan Reddit for job postings.
    
    Returns:
        List of job dictionaries
    """
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        print("⚠️ Reddit credentials not configured!")
        return []
    
    jobs = []
    
    try:
        # Initialize Reddit instance
        print("🔴 Connecting to Reddit...")
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        
        for subreddit_name in TARGET_SUBREDDITS:
            try:
                print(f"   Scanning r/{subreddit_name}...")
                subreddit = reddit.subreddit(subreddit_name)
                
                # Get both new and hot posts
                posts = list(subreddit.new(limit=posts_per_sub))
                
                for post in posts:
                    title_lower = post.title.lower()
                    body_lower = (post.selftext or "").lower()
                    combined = f"{title_lower} {body_lower}"
                    
                    # Skip if it's someone looking for a job (not hiring)
                    if any(kw in combined for kw in EXCLUDE_KEYWORDS):
                        continue
                    
                    # Check if it's a hiring post
                    if not any(kw in combined for kw in HIRING_KEYWORDS):
                        continue
                    
                    # Extract details
                    salary = extract_salary(post.selftext or "")
                    company = extract_company(post.selftext or "", post.title)
                    
                    # Use post URL or external URL if available
                    link = post.url if post.url != post.permalink else f"https://reddit.com{post.permalink}"
                    
                    jobs.append({
                        "source": f"Reddit/r/{subreddit_name}",
                        "title": post.title[:200],
                        "company": company,
                        "link": link,
                        "description": (post.selftext or "")[:2000],
                        "salary": salary,
                        "score": post.score,
                        "comments": post.num_comments
                    })
                    
            except Exception as e:
                print(f"   ❌ Error scanning r/{subreddit_name}: {e}")
                continue
        
        print(f"✅ Found {len(jobs)} Reddit job posts")
        
    except Exception as e:
        print(f"❌ Reddit Error: {e}")
    
    return jobs


if __name__ == "__main__":
    # Test the scraper
    jobs = scan_reddit(posts_per_sub=10)
    for job in jobs[:5]:
        print(f"\n🔴 {job['title'][:60]}...")
        print(f"   Company: {job['company']}")
        print(f"   Salary: {job['salary']}")
        print(f"   Score: {job['score']} | Comments: {job['comments']}")

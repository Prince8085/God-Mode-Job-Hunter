"""
LinkedIn Scraper - Time-based job search (last 1 hour / 24 hours)
Uses LinkedIn's URL parameters to filter recent postings
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time
import random
from urllib.parse import urlencode
import re


# LinkedIn time filters (f_TPR parameter)
# r86400 = last 24 hours
# r3600 = last 1 hour
# r604800 = last week
TIME_FILTERS = {
    "1hour": "r3600",
    "24hours": "r86400",
    "1week": "r604800",
    "1month": "r2592000"
}

# Job search keywords
DEFAULT_KEYWORDS = [
    "software engineer",
    "python developer",
    "full stack developer",
    "backend developer",
    "frontend developer",
    "data scientist",
    "machine learning engineer",
    "devops engineer"
]

# Locations
LOCATIONS = {
    "india": "102713980",
    "bangalore": "105214831",
    "mumbai": "104187959",
    "delhi": "104738732",
    "hyderabad": "105556991",
    "pune": "114806696",
    "remote": "92000000"  # Worldwide remote
}

# Headers to mimic browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def build_linkedin_url(
    keyword: str,
    location: str = "india",
    time_filter: str = "24hours",
    experience_level: str = None,
    job_type: str = None,
    start: int = 0
) -> str:
    """
    Build LinkedIn job search URL with filters.
    
    Args:
        keyword: Search keyword
        location: Location (india, bangalore, remote, etc.)
        time_filter: 1hour, 24hours, 1week, 1month
        experience_level: Entry level, Mid-Senior, etc.
        job_type: Full-time, Part-time, Internship, Contract
        start: Pagination offset
    
    Returns:
        LinkedIn search URL
    """
    base_url = "https://www.linkedin.com/jobs/search/"
    
    params = {
        "keywords": keyword,
        "location": location.title() if location not in LOCATIONS else "",
        "geoId": LOCATIONS.get(location.lower(), "102713980"),  # Default India
        "f_TPR": TIME_FILTERS.get(time_filter, "r86400"),
        "position": 1,
        "pageNum": 0,
        "start": start
    }
    
    # Experience level filter
    experience_map = {
        "internship": "1",
        "entry": "2",
        "associate": "3",
        "mid-senior": "4",
        "director": "5",
        "executive": "6"
    }
    if experience_level and experience_level.lower() in experience_map:
        params["f_E"] = experience_map[experience_level.lower()]
    
    # Job type filter
    job_type_map = {
        "full-time": "F",
        "part-time": "P",
        "contract": "C",
        "internship": "I",
        "temporary": "T"
    }
    if job_type and job_type.lower() in job_type_map:
        params["f_JT"] = job_type_map[job_type.lower()]
    
    return f"{base_url}?{urlencode(params)}"


def parse_job_card(card) -> Dict:
    """Parse individual job card from LinkedIn"""
    try:
        # Title
        title_elem = card.find("h3", class_="base-search-card__title")
        title = title_elem.get_text(strip=True) if title_elem else "Unknown"
        
        # Company
        company_elem = card.find("h4", class_="base-search-card__subtitle")
        company = company_elem.get_text(strip=True) if company_elem else "Unknown"
        
        # Location
        location_elem = card.find("span", class_="job-search-card__location")
        location = location_elem.get_text(strip=True) if location_elem else ""
        
        # Link
        link_elem = card.find("a", class_="base-card__full-link")
        link = link_elem.get("href", "") if link_elem else ""
        
        # Clean up link (remove tracking params)
        if link:
            link = link.split("?")[0]
        
        # Posted time
        time_elem = card.find("time", class_="job-search-card__listdate")
        posted = time_elem.get_text(strip=True) if time_elem else ""
        
        return {
            "title": title,
            "company": company,
            "location": location,
            "link": link,
            "posted": posted
        }
    except Exception as e:
        print(f"Error parsing job card: {e}")
        return None


def scrape_linkedin_page(url: str) -> List[Dict]:
    """Scrape a single LinkedIn search page"""
    jobs = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"   ⚠️ LinkedIn returned status {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find job cards
        job_cards = soup.find_all("div", class_="base-card")
        
        for card in job_cards:
            job = parse_job_card(card)
            if job and job.get("link"):
                jobs.append(job)
        
    except requests.RequestException as e:
        print(f"   ❌ Request failed: {e}")
    except Exception as e:
        print(f"   ❌ Parse error: {e}")
    
    return jobs


def scan_linkedin(
    keywords: List[str] = None,
    location: str = "india",
    time_filter: str = "1hour",
    max_results: int = 50
) -> List[Dict]:
    """
    Scan LinkedIn for recent job postings.
    
    Args:
        keywords: List of job keywords to search
        location: Location filter
        time_filter: 1hour, 24hours, 1week
        max_results: Maximum jobs to return
    
    Returns:
        List of job dictionaries
    """
    if keywords is None:
        keywords = DEFAULT_KEYWORDS[:5]  # Use first 5 default keywords
    
    all_jobs = []
    seen_links = set()
    
    print(f"💼 Scanning LinkedIn ({time_filter} filter)...")
    print(f"   Location: {location}")
    print(f"   Keywords: {', '.join(keywords[:3])}...")
    
    for keyword in keywords:
        if len(all_jobs) >= max_results:
            break
        
        try:
            # Build URL with time filter
            url = build_linkedin_url(
                keyword=keyword,
                location=location,
                time_filter=time_filter
            )
            
            print(f"   Searching: {keyword}")
            
            # Scrape the page
            jobs = scrape_linkedin_page(url)
            
            for job in jobs:
                if job["link"] in seen_links:
                    continue
                seen_links.add(job["link"])
                
                # Format for our system
                all_jobs.append({
                    "source": "LinkedIn",
                    "title": job["title"],
                    "company": job["company"],
                    "link": job["link"],
                    "description": f"Location: {job['location']} | Posted: {job['posted']}",
                    "salary": "Not Mentioned",
                    "location": job["location"],
                    "posted": job["posted"]
                })
            
            # Random delay to avoid rate limiting
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            print(f"   ⚠️ Error searching '{keyword}': {e}")
            continue
    
    print(f"✅ Found {len(all_jobs)} LinkedIn jobs (posted in last {time_filter})")
    return all_jobs[:max_results]


def scan_linkedin_fast(time_filter: str = "1hour") -> List[Dict]:
    """
    Quick scan with predefined searches for recent jobs.
    Best for finding jobs posted in the last hour!
    """
    quick_searches = [
        {"keyword": "software engineer", "location": "india"},
        {"keyword": "python developer", "location": "bangalore"},
        {"keyword": "full stack", "location": "india"},
        {"keyword": "backend developer", "location": "remote"},
    ]
    
    all_jobs = []
    seen_links = set()
    
    print(f"⚡ Quick LinkedIn Scan (Last {time_filter})...")
    
    for search in quick_searches:
        url = build_linkedin_url(
            keyword=search["keyword"],
            location=search["location"],
            time_filter=time_filter
        )
        
        jobs = scrape_linkedin_page(url)
        
        for job in jobs:
            if job["link"] not in seen_links:
                seen_links.add(job["link"])
                all_jobs.append({
                    "source": "LinkedIn",
                    "title": job["title"],
                    "company": job["company"],
                    "link": job["link"],
                    "description": f"Location: {job['location']} | Posted: {job['posted']}",
                    "salary": "Not Mentioned"
                })
        
        time.sleep(random.uniform(1.5, 3))
    
    print(f"✅ Quick scan found {len(all_jobs)} jobs")
    return all_jobs


# Generate LinkedIn search URLs for manual use
def get_linkedin_urls(keyword: str = "software engineer") -> dict:
    """
    Get LinkedIn URLs with different time filters.
    Useful for manual checking or browser automation.
    """
    return {
        "last_1_hour": build_linkedin_url(keyword, "india", "1hour"),
        "last_24_hours": build_linkedin_url(keyword, "india", "24hours"),
        "last_week": build_linkedin_url(keyword, "india", "1week"),
        "remote_1_hour": build_linkedin_url(keyword, "remote", "1hour"),
    }


if __name__ == "__main__":
    # Test the scraper
    print("\n=== Testing LinkedIn Scraper ===\n")
    
    # Show URL structure
    print("📎 URL Examples (Last 1 Hour):")
    urls = get_linkedin_urls("python developer")
    for name, url in urls.items():
        print(f"   {name}: {url[:80]}...")
    
    print("\n")
    
    # Quick scan
    jobs = scan_linkedin_fast("1hour")
    
    for job in jobs[:5]:
        print(f"\n💼 {job['title']}")
        print(f"   Company: {job['company']}")
        print(f"   {job['description']}")

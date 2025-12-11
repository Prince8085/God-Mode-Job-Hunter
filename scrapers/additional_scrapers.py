"""
Additional Scrapers - Naukri, Internshala, Wellfound, HackerNews, etc.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time
import random
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def scan_hackernews_jobs() -> List[Dict]:
    """
    Scan HackerNews 'Who is Hiring' threads
    Monthly threads with hundreds of startup jobs!
    """
    jobs = []
    
    try:
        print("🟠 Scanning HackerNews Jobs...")
        
        # HN Jobs API
        url = "https://hacker-news.firebaseio.com/v0/jobstories.json"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return []
        
        job_ids = response.json()[:30]  # Top 30 jobs
        
        for job_id in job_ids:
            try:
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{job_id}.json"
                item = requests.get(item_url, timeout=5).json()
                
                if item and item.get('type') == 'job':
                    jobs.append({
                        "source": "HackerNews",
                        "title": item.get('title', 'Startup Job')[:200],
                        "company": "YC/Startup",
                        "link": item.get('url', f"https://news.ycombinator.com/item?id={job_id}"),
                        "description": item.get('text', '')[:1000] if item.get('text') else '',
                        "salary": "Competitive (Startup)",
                    })
                
                time.sleep(0.2)
            except:
                continue
        
        print(f"✅ Found {len(jobs)} HackerNews jobs")
        
    except Exception as e:
        print(f"❌ HackerNews error: {e}")
    
    return jobs


def scan_remoteok() -> List[Dict]:
    """
    Scan RemoteOK - Remote jobs worldwide
    """
    jobs = []
    
    try:
        print("🌍 Scanning RemoteOK...")
        
        url = "https://remoteok.com/api"
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        
        for item in data[1:31]:  # Skip header, get 30 jobs
            if isinstance(item, dict):
                jobs.append({
                    "source": "RemoteOK",
                    "title": item.get('position', 'Remote Role')[:200],
                    "company": item.get('company', 'Remote Company'),
                    "link": f"https://remoteok.com{item.get('url', '')}",
                    "description": item.get('description', '')[:1000],
                    "salary": item.get('salary', 'Competitive'),
                    "tags": item.get('tags', [])
                })
        
        print(f"✅ Found {len(jobs)} RemoteOK jobs")
        
    except Exception as e:
        print(f"❌ RemoteOK error: {e}")
    
    return jobs


def scan_github_jobs() -> List[Dict]:
    """
    Scan GitHub trending repos for job postings
    Many companies post jobs in their repos
    """
    jobs = []
    
    try:
        print("🐙 Scanning GitHub for job postings...")
        
        # Search GitHub for job postings
        search_queries = [
            "hiring software engineer india",
            "job opening developer remote",
            "we are hiring python",
        ]
        
        for query in search_queries[:1]:  # Limit to avoid rate limits
            url = f"https://api.github.com/search/repositories?q={query}&sort=updated&per_page=10"
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for repo in data.get('items', []):
                    if 'hiring' in repo.get('description', '').lower() or 'job' in repo.get('name', '').lower():
                        jobs.append({
                            "source": "GitHub",
                            "title": repo.get('name', 'Unknown')[:100],
                            "company": repo.get('owner', {}).get('login', 'Unknown'),
                            "link": repo.get('html_url', ''),
                            "description": repo.get('description', '')[:500],
                            "salary": "Not Mentioned",
                        })
            
            time.sleep(1)
        
        print(f"✅ Found {len(jobs)} GitHub jobs")
        
    except Exception as e:
        print(f"❌ GitHub error: {e}")
    
    return jobs


def scan_simplyhired() -> List[Dict]:
    """
    Scan SimplyHired India
    """
    jobs = []
    
    try:
        print("🎯 Scanning SimplyHired...")
        
        keywords = ["software engineer", "python developer", "full stack"]
        
        for kw in keywords[:1]:
            url = f"https://www.simplyhired.co.in/search?q={kw.replace(' ', '+')}&l=india"
            response = requests.get(url, headers=HEADERS, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find job cards
                cards = soup.find_all('article', class_='SerpJob')[:10]
                
                for card in cards:
                    try:
                        title_elem = card.find('a', class_='SerpJob-link')
                        company_elem = card.find('span', class_='SerpJob-company')
                        
                        if title_elem:
                            jobs.append({
                                "source": "SimplyHired",
                                "title": title_elem.get_text(strip=True)[:200],
                                "company": company_elem.get_text(strip=True) if company_elem else "Unknown",
                                "link": "https://www.simplyhired.co.in" + title_elem.get('href', ''),
                                "description": "",
                                "salary": "Not Mentioned",
                            })
                    except:
                        continue
            
            time.sleep(1)
        
        print(f"✅ Found {len(jobs)} SimplyHired jobs")
        
    except Exception as e:
        print(f"❌ SimplyHired error: {e}")
    
    return jobs


def scan_arbeitnow() -> List[Dict]:
    """
    Scan Arbeitnow - Remote & Europe jobs (many accept India remote)
    Has a nice free API!
    """
    jobs = []
    
    try:
        print("🇪🇺 Scanning Arbeitnow...")
        
        url = "https://arbeitnow.com/api/job-board-api"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            for item in data.get('data', [])[:20]:
                # Filter for remote or relevant
                if item.get('remote', False) or 'india' in item.get('location', '').lower():
                    jobs.append({
                        "source": "Arbeitnow",
                        "title": item.get('title', '')[:200],
                        "company": item.get('company_name', 'Unknown'),
                        "link": item.get('url', ''),
                        "description": item.get('description', '')[:1000],
                        "salary": "Remote/International",
                        "tags": item.get('tags', [])
                    })
        
        print(f"✅ Found {len(jobs)} Arbeitnow jobs")
        
    except Exception as e:
        print(f"❌ Arbeitnow error: {e}")
    
    return jobs


def scan_all_additional() -> List[Dict]:
    """
    Run all additional scrapers
    """
    all_jobs = []
    
    # HackerNews
    try:
        all_jobs.extend(scan_hackernews_jobs())
    except:
        pass
    
    # RemoteOK
    try:
        all_jobs.extend(scan_remoteok())
    except:
        pass
    
    # Arbeitnow
    try:
        all_jobs.extend(scan_arbeitnow())
    except:
        pass
    
    # SimplyHired
    try:
        all_jobs.extend(scan_simplyhired())
    except:
        pass
    
    return all_jobs


if __name__ == "__main__":
    print("\n=== Testing Additional Scrapers ===\n")
    
    jobs = scan_all_additional()
    print(f"\n📊 Total: {len(jobs)} jobs from additional sources")
    
    for job in jobs[:5]:
        print(f"\n🔹 {job['source']}: {job['title'][:50]}")
        print(f"   Company: {job['company']}")

"""
Google Dorking Scraper - Advanced search for hidden jobs
Uses expert-level Google dorks to find jobs on ATS platforms
"""
from googlesearch import search
from typing import List, Dict
import time
import random
from urllib.parse import urlparse


# Expert-level Google Dorks for job hunting
# These find jobs that aren't on major portals!
GOOGLE_DORKS = [
    # Lever ATS - Very popular with startups
    'site:lever.co "software engineer" India',
    'site:lever.co "developer" remote India',
    'site:lever.co "backend" India freshers',
    'site:lever.co "frontend" India entry',
    'site:lever.co "full stack" India',
    'site:lever.co "python" India',
    'site:lever.co "machine learning" India',
    
    # Greenhouse ATS - Enterprise companies
    'site:greenhouse.io "software" India',
    'site:greenhouse.io "engineer" Bangalore',
    'site:greenhouse.io "developer" remote India',
    
    # Ashby ATS - Growing startups
    'site:jobs.ashbyhq.com "engineering" India',
    'site:jobs.ashbyhq.com "developer" India',
    
    # Workable ATS
    'site:apply.workable.com "software" India',
    'site:apply.workable.com "developer" remote',
    
    # Wellfound (AngelList) - Startups
    'site:wellfound.com "software engineer" India',
    'site:wellfound.com "developer" India startup',
    
    # Direct company career pages
    'inurl:careers "software engineer" India "apply now"',
    'inurl:jobs "developer" India "apply"',
    
    # YC Companies
    'site:ycombinator.com/jobs "India" OR "remote"',
    
    # Specific tech stacks
    'site:lever.co "python" OR "django" OR "fastapi" India',
    'site:lever.co "react" OR "typescript" OR "nextjs" India',
    'site:greenhouse.io "java" OR "spring" India',
    
    # Remote-first companies
    '"remote" "software engineer" India "apply" site:notion.site',
    '"we are hiring" "developer" India site:notion.so',
]

# Additional time-sensitive dorks (jobs posted recently)
RECENT_DORKS = [
    'site:lever.co "software" India after:2024-01-01',
    'site:greenhouse.io "developer" India after:2024-01-01',
]


def extract_company_from_url(url: str) -> str:
    """Extract company name from ATS URL"""
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        # Lever: jobs.lever.co/company-name
        if 'lever.co' in parsed.netloc:
            if path_parts:
                return path_parts[0].replace('-', ' ').title()
        
        # Greenhouse: boards.greenhouse.io/company-name
        elif 'greenhouse.io' in parsed.netloc:
            if path_parts:
                return path_parts[0].replace('-', ' ').title()
        
        # Ashby: jobs.ashbyhq.com/company-name
        elif 'ashbyhq.com' in parsed.netloc:
            if path_parts:
                return path_parts[0].replace('-', ' ').title()
        
        # Workable: company.workable.com
        elif 'workable.com' in parsed.netloc:
            subdomain = parsed.netloc.split('.')[0]
            if subdomain != 'apply':
                return subdomain.replace('-', ' ').title()
        
        # Wellfound/AngelList
        elif 'wellfound.com' in parsed.netloc or 'angel.co' in parsed.netloc:
            if len(path_parts) > 1:
                return path_parts[1].replace('-', ' ').title()
        
        return "Direct Startup"
        
    except:
        return "Unknown"


def extract_role_from_url(url: str) -> str:
    """Try to extract role from URL path"""
    try:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        # Usually the last part of URL contains role
        if len(path_parts) > 1:
            role = path_parts[-1].replace('-', ' ').replace('_', ' ')
            # Clean up common suffixes
            role = role.replace(' at ', ' ').replace(' in ', ' ')
            return role.title()[:100]
        
        return "Engineering Role"
        
    except:
        return "Software Role"


def scan_google(results_per_dork: int = 5) -> List[Dict]:
    """
    Scan Google for hidden jobs using advanced dorks.
    
    Returns:
        List of job dictionaries
    """
    jobs = []
    seen_urls = set()
    
    print("🔍 Starting Google Dorking (Expert Mode)...")
    
    # Use subset of dorks to avoid rate limiting
    dorks_to_use = random.sample(GOOGLE_DORKS, min(10, len(GOOGLE_DORKS)))
    
    for dork in dorks_to_use:
        try:
            print(f"   Searching: {dork[:50]}...")
            
            # Google search with delay to avoid blocking
            results = search(dork, num_results=results_per_dork, lang='en')
            
            for url in results:
                # Skip if already seen
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                # Skip non-job URLs
                if any(skip in url.lower() for skip in ['login', 'signup', 'blog', 'about']):
                    continue
                
                # Extract details from URL
                company = extract_company_from_url(url)
                role = extract_role_from_url(url)
                
                # Determine source platform
                source = "Google Search"
                if 'lever.co' in url:
                    source = "Lever ATS"
                elif 'greenhouse.io' in url:
                    source = "Greenhouse ATS"
                elif 'ashbyhq.com' in url:
                    source = "Ashby ATS"
                elif 'workable.com' in url:
                    source = "Workable ATS"
                elif 'wellfound.com' in url:
                    source = "Wellfound"
                
                jobs.append({
                    "source": source,
                    "title": role,
                    "company": company,
                    "link": url,
                    "description": f"Job found via Google Dorking: {dork[:100]}",
                    "salary": "Not Mentioned",
                    "dork_used": dork
                })
            
            # Random delay between searches to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
        except Exception as e:
            print(f"   ⚠️ Dork failed: {e}")
            time.sleep(2)  # Wait before next query
            continue
    
    print(f"✅ Found {len(jobs)} jobs via Google Dorking")
    return jobs


def scan_google_targeted(role: str, location: str = "India") -> List[Dict]:
    """
    Targeted Google search for specific role.
    
    Args:
        role: Job role to search for (e.g., "Python Developer")
        location: Location preference
    
    Returns:
        List of job dictionaries
    """
    custom_dorks = [
        f'site:lever.co "{role}" {location}',
        f'site:greenhouse.io "{role}" {location}',
        f'site:wellfound.com "{role}" {location}',
        f'inurl:careers "{role}" {location} "apply"',
    ]
    
    jobs = []
    seen_urls = set()
    
    print(f"🎯 Targeted search for: {role} in {location}")
    
    for dork in custom_dorks:
        try:
            results = search(dork, num_results=5, lang='en')
            
            for url in results:
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                company = extract_company_from_url(url)
                
                jobs.append({
                    "source": "Targeted Search",
                    "title": role,
                    "company": company,
                    "link": url,
                    "description": f"Targeted search for {role}",
                    "salary": "Not Mentioned"
                })
            
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"   ⚠️ Search failed: {e}")
            continue
    
    return jobs


if __name__ == "__main__":
    # Test the scraper
    print("\n=== Testing Google Dorking ===\n")
    jobs = scan_google(results_per_dork=3)
    
    for job in jobs[:10]:
        print(f"\n🔍 {job['title']}")
        print(f"   Company: {job['company']}")
        print(f"   Source: {job['source']}")
        print(f"   Link: {job['link'][:60]}...")

"""
Smart Job Applier - Semi-Auto and Quick Apply Features
Supports: Lever, Greenhouse, Workday, LinkedIn Easy Apply, and more
"""
import webbrowser
import os
import time
from typing import Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import ASSETS_DIR, OUTPUT_DIR

# Resume path
RESUME_PATH = os.path.join(OUTPUT_DIR, "Resume_ATS_latest.docx")


def detect_platform(url: str) -> str:
    """Detect the job platform from URL"""
    url_lower = url.lower()
    
    if 'lever.co' in url_lower or 'jobs.lever' in url_lower:
        return 'lever'
    elif 'greenhouse.io' in url_lower or 'boards.greenhouse' in url_lower:
        return 'greenhouse'
    elif 'workday.com' in url_lower or 'myworkday' in url_lower:
        return 'workday'
    elif 'linkedin.com/jobs' in url_lower:
        return 'linkedin'
    elif 'indeed.com' in url_lower:
        return 'indeed'
    elif 'naukri.com' in url_lower:
        return 'naukri'
    elif 'internshala.com' in url_lower:
        return 'internshala'
    elif 'angel.co' in url_lower or 'wellfound.com' in url_lower:
        return 'wellfound'
    elif 'glassdoor.com' in url_lower:
        return 'glassdoor'
    else:
        return 'generic'


def get_chrome_driver(headless: bool = False) -> webdriver.Chrome:
    """Get configured Chrome WebDriver"""
    options = Options()
    
    if headless:
        options.add_argument('--headless')
    
    # Basic options for stability
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # Make it look like a real browser
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User agent
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"❌ Chrome driver error: {e}")
        return None


# ============== SIMPLE BROWSER OPEN ==============

def open_in_browser(url: str) -> bool:
    """
    Semi-Auto Apply: Simply open the job link in default browser
    User can then fill the form manually
    """
    try:
        print(f"🌐 Opening in browser: {url}")
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"❌ Browser open error: {e}")
        return False


def open_multiple_jobs(urls: list) -> int:
    """Open multiple job links in browser tabs"""
    opened = 0
    for url in urls[:10]:  # Max 10 at a time
        if open_in_browser(url):
            opened += 1
            time.sleep(0.5)  # Small delay between tabs
    return opened


# ============== QUICK APPLY FUNCTIONS ==============

def quick_apply_lever(url: str, profile: Dict) -> Tuple[bool, str]:
    """
    Quick Apply for Lever jobs
    Lever has a standard form structure
    """
    driver = None
    try:
        print(f"🚀 Quick Apply: Lever - {url}")
        driver = get_chrome_driver(headless=False)
        
        if not driver:
            return False, "Chrome driver not available"
        
        driver.get(url)
        time.sleep(3)
        
        # Look for Apply button
        try:
            apply_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.postings-btn, button.postings-btn, [data-qa='btn-apply']"))
            )
            apply_btn.click()
            time.sleep(2)
        except:
            # Maybe already on apply page
            pass
        
        identity = profile.get('identity', {})
        
        # Fill name
        try:
            name_field = driver.find_element(By.CSS_SELECTOR, "input[name='name'], input[placeholder*='name' i]")
            name_field.clear()
            name_field.send_keys(identity.get('full_name', ''))
        except:
            pass
        
        # Fill email
        try:
            email_field = driver.find_element(By.CSS_SELECTOR, "input[name='email'], input[type='email']")
            email_field.clear()
            email_field.send_keys(identity.get('email', ''))
        except:
            pass
        
        # Fill phone
        try:
            phone_field = driver.find_element(By.CSS_SELECTOR, "input[name='phone'], input[type='tel']")
            phone_field.clear()
            phone_field.send_keys(identity.get('phone', ''))
        except:
            pass
        
        # Upload resume if file exists
        try:
            resume_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            if os.path.exists(RESUME_PATH):
                resume_input.send_keys(RESUME_PATH)
                time.sleep(1)
        except:
            pass
        
        # Fill LinkedIn
        try:
            linkedin_field = driver.find_element(By.CSS_SELECTOR, "input[name*='linkedin' i], input[placeholder*='linkedin' i]")
            linkedin_field.clear()
            linkedin_field.send_keys(identity.get('linkedin', ''))
        except:
            pass
        
        # Fill portfolio/website
        try:
            website_field = driver.find_element(By.CSS_SELECTOR, "input[name*='website' i], input[name*='portfolio' i]")
            website_field.clear()
            website_field.send_keys(identity.get('portfolio', ''))
        except:
            pass
        
        print("✅ Form pre-filled! Please review and submit.")
        
        # Keep browser open for user to review
        input("Press Enter after you've reviewed and submitted...")
        
        return True, "Form pre-filled successfully"
        
    except Exception as e:
        return False, str(e)
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def quick_apply_greenhouse(url: str, profile: Dict) -> Tuple[bool, str]:
    """
    Quick Apply for Greenhouse jobs
    """
    driver = None
    try:
        print(f"🚀 Quick Apply: Greenhouse - {url}")
        driver = get_chrome_driver(headless=False)
        
        if not driver:
            return False, "Chrome driver not available"
        
        driver.get(url)
        time.sleep(3)
        
        identity = profile.get('identity', {})
        
        # Fill first name
        try:
            first_name = driver.find_element(By.CSS_SELECTOR, "input[name*='first_name'], #first_name")
            first_name.clear()
            name_parts = identity.get('full_name', '').split()
            first_name.send_keys(name_parts[0] if name_parts else '')
        except:
            pass
        
        # Fill last name
        try:
            last_name = driver.find_element(By.CSS_SELECTOR, "input[name*='last_name'], #last_name")
            last_name.clear()
            name_parts = identity.get('full_name', '').split()
            last_name.send_keys(name_parts[-1] if len(name_parts) > 1 else '')
        except:
            pass
        
        # Fill email
        try:
            email_field = driver.find_element(By.CSS_SELECTOR, "input[name*='email'], input[type='email']")
            email_field.clear()
            email_field.send_keys(identity.get('email', ''))
        except:
            pass
        
        # Fill phone
        try:
            phone_field = driver.find_element(By.CSS_SELECTOR, "input[name*='phone'], input[type='tel']")
            phone_field.clear()
            phone_field.send_keys(identity.get('phone', ''))
        except:
            pass
        
        # Upload resume
        try:
            resume_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            if os.path.exists(RESUME_PATH):
                resume_input.send_keys(RESUME_PATH)
        except:
            pass
        
        print("✅ Form pre-filled! Please review and submit.")
        input("Press Enter after you've reviewed and submitted...")
        
        return True, "Form pre-filled successfully"
        
    except Exception as e:
        return False, str(e)
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


def smart_apply(url: str, profile: Dict = None) -> Tuple[bool, str, str]:
    """
    Smart Apply - Detects platform and uses appropriate method
    Returns: (success, message, method_used)
    """
    platform = detect_platform(url)
    
    if profile is None:
        # Load profile
        try:
            from utils.ats_resume import load_profile
            profile = load_profile()
        except:
            profile = {}
    
    print(f"📋 Platform detected: {platform}")
    
    # Quick apply supported platforms
    if platform == 'lever':
        success, msg = quick_apply_lever(url, profile)
        return success, msg, "Quick Apply (Lever)"
    
    elif platform == 'greenhouse':
        success, msg = quick_apply_greenhouse(url, profile)
        return success, msg, "Quick Apply (Greenhouse)"
    
    # Semi-auto for others - just open browser
    else:
        success = open_in_browser(url)
        method = f"Semi-Auto ({platform.title()})"
        msg = "Browser opened - please fill the form manually" if success else "Failed to open browser"
        return success, msg, method


def get_apply_method_info(url: str) -> Dict:
    """Get info about how this job will be applied"""
    platform = detect_platform(url)
    
    quick_apply_platforms = ['lever', 'greenhouse']
    
    return {
        'platform': platform,
        'quick_apply_supported': platform in quick_apply_platforms,
        'method': 'Quick Apply (Auto-fill)' if platform in quick_apply_platforms else 'Semi-Auto (Browser)',
        'description': 'Form will be pre-filled automatically' if platform in quick_apply_platforms else 'Link will open in browser'
    }


# ============== BATCH APPLY ==============

def batch_semi_apply(job_list: list) -> Dict:
    """Open multiple job links for batch applying"""
    results = {
        'total': len(job_list),
        'opened': 0,
        'failed': 0
    }
    
    for job in job_list[:15]:  # Max 15 at a time
        url = job.get('link', '')
        if url and open_in_browser(url):
            results['opened'] += 1
        else:
            results['failed'] += 1
        time.sleep(0.3)
    
    return results


if __name__ == "__main__":
    print("\n=== Testing Smart Applier ===\n")
    
    # Test platform detection
    test_urls = [
        "https://jobs.lever.co/company/123",
        "https://boards.greenhouse.io/company/jobs/456",
        "https://www.linkedin.com/jobs/view/789",
        "https://company.com/careers/job-123"
    ]
    
    for url in test_urls:
        info = get_apply_method_info(url)
        print(f"URL: {url[:40]}...")
        print(f"  Platform: {info['platform']}")
        print(f"  Method: {info['method']}")
        print()

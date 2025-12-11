"""
Web Applier - Selenium browser automation for applying to jobs
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from typing import Optional
from config import OUTPUT_DIR


def setup_browser(headless: bool = False) -> webdriver.Chrome:
    """
    Setup Chrome browser with optimal settings.
    
    Args:
        headless: Run in headless mode (invisible)
    
    Returns:
        Chrome WebDriver instance
    """
    options = Options()
    
    if headless:
        options.add_argument('--headless')
    
    # Common settings
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-popup-blocking')
    
    # Avoid detection
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User agent
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Initialize driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Additional anti-detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def open_job_link(url: str, take_screenshot: bool = True) -> dict:
    """
    Open job link in browser.
    
    Args:
        url: Job URL to open
        take_screenshot: Whether to take a screenshot
    
    Returns:
        Dict with success status and details
    """
    result = {
        "success": False,
        "url": url,
        "screenshot": None,
        "page_title": None,
        "message": ""
    }
    
    driver = None
    
    try:
        print(f"🌐 Opening: {url[:60]}...")
        
        # Setup browser
        driver = setup_browser(headless=False)
        
        # Navigate to URL
        driver.get(url)
        
        # Wait for page load
        time.sleep(3)
        
        # Get page title
        result["page_title"] = driver.title
        
        # Take screenshot
        if take_screenshot:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            screenshot_path = os.path.join(OUTPUT_DIR, f"screenshot_{int(time.time())}.png")
            driver.save_screenshot(screenshot_path)
            result["screenshot"] = screenshot_path
            print(f"📸 Screenshot saved: {screenshot_path}")
        
        result["success"] = True
        result["message"] = f"Opened: {driver.title}"
        
        # Keep browser open for user to interact
        print("✅ Browser opened. Press Enter to close...")
        input()
        
    except Exception as e:
        result["message"] = f"Error: {str(e)}"
        print(f"❌ {result['message']}")
    
    finally:
        if driver:
            driver.quit()
    
    return result


def apply_to_lever_job(url: str, resume_path: str = None) -> dict:
    """
    Semi-automated apply to Lever job.
    Opens the page and helps with form filling.
    """
    result = {
        "success": False,
        "url": url,
        "message": ""
    }
    
    driver = None
    
    try:
        driver = setup_browser(headless=False)
        driver.get(url)
        time.sleep(3)
        
        # Look for apply button
        try:
            apply_btn = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Apply')]"))
            )
            apply_btn.click()
            time.sleep(2)
        except:
            pass
        
        result["success"] = True
        result["message"] = "Page opened. Complete the form manually."
        
        print("✅ Lever job page opened. Complete the application manually.")
        print("   Press Enter when done...")
        input()
        
    except Exception as e:
        result["message"] = str(e)
    
    finally:
        if driver:
            driver.quit()
    
    return result


def quick_open_multiple(urls: list, delay: int = 2) -> list:
    """
    Open multiple job links in sequence.
    
    Args:
        urls: List of job URLs
        delay: Seconds between each
    
    Returns:
        List of results
    """
    results = []
    driver = None
    
    try:
        driver = setup_browser(headless=False)
        
        for i, url in enumerate(urls):
            print(f"[{i+1}/{len(urls)}] Opening: {url[:50]}...")
            
            try:
                driver.execute_script(f"window.open('{url}', '_blank');")
                time.sleep(delay)
            except Exception as e:
                print(f"   Error: {e}")
            
            results.append({"url": url, "opened": True})
        
        print(f"\n✅ Opened {len(urls)} tabs. Review and apply!")
        print("   Press Enter when done...")
        input()
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        if driver:
            driver.quit()
    
    return results


if __name__ == "__main__":
    # Test
    print("\n=== Testing Web Applier ===\n")
    
    test_url = "https://www.google.com"
    result = open_job_link(test_url, take_screenshot=True)
    print(f"Result: {result}")

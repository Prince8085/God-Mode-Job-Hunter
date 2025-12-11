"""
Domain Validator - Whois lookup for scam detection
Checks domain age and flags suspicious websites
"""
import whois
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict
import socket


# Free email domains - suspicious if used by "companies"
FREE_EMAIL_DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "mail.com", "protonmail.com", "aol.com", "icloud.com",
    "zoho.com", "yandex.com", "gmx.com", "mail.ru"
]

# Known legitimate job platform domains
TRUSTED_DOMAINS = [
    "linkedin.com", "indeed.com", "naukri.com", "foundit.in",
    "glassdoor.com", "lever.co", "greenhouse.io", "ashbyhq.com",
    "workable.com", "wellfound.com", "angel.co", "instahyre.com",
    "internshala.com", "cutshort.io", "hirist.com", "monster.com"
]


def extract_domain(url_or_email: str) -> str:
    """Extract domain from URL or email address"""
    url_or_email = url_or_email.strip().lower()
    
    # If it's an email
    if "@" in url_or_email and not url_or_email.startswith("http"):
        return url_or_email.split("@")[-1]
    
    # If it's a URL
    try:
        parsed = urlparse(url_or_email)
        domain = parsed.netloc or parsed.path
        
        # Remove www.
        if domain.startswith("www."):
            domain = domain[4:]
        
        # Remove port if present
        if ":" in domain:
            domain = domain.split(":")[0]
        
        return domain
    except:
        return url_or_email


def get_root_domain(domain: str) -> str:
    """Get root domain (e.g., jobs.company.com -> company.com)"""
    parts = domain.split(".")
    
    # Handle cases like .co.in, .com.au
    if len(parts) >= 3 and parts[-2] in ["co", "com", "org", "net", "ac"]:
        return ".".join(parts[-3:])
    elif len(parts) >= 2:
        return ".".join(parts[-2:])
    
    return domain


def check_domain_age(url_or_email: str) -> Dict:
    """
    Check domain legitimacy using Whois lookup.
    
    Args:
        url_or_email: URL or email to check
    
    Returns:
        Dict with domain, age_days, risk_level, creation_date, details
    """
    domain = extract_domain(url_or_email)
    root_domain = get_root_domain(domain)
    
    result = {
        "domain": domain,
        "root_domain": root_domain,
        "age_days": -1,
        "risk_level": "UNKNOWN",
        "creation_date": "Unknown",
        "details": ""
    }
    
    # Check if it's a free email domain
    if root_domain in FREE_EMAIL_DOMAINS:
        result["risk_level"] = "WARNING"
        result["details"] = "Free email provider - verify company exists independently"
        return result
    
    # Check if it's a trusted job platform
    if root_domain in TRUSTED_DOMAINS:
        result["risk_level"] = "TRUSTED"
        result["details"] = "Known job platform"
        return result
    
    # Whois lookup
    try:
        w = whois.whois(root_domain)
        
        if w is None or w.domain_name is None:
            result["details"] = "Domain not found in Whois"
            return result
        
        # Get creation date
        creation_date = w.creation_date
        
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        
        if creation_date:
            # Calculate age
            if isinstance(creation_date, datetime):
                age_days = (datetime.now() - creation_date).days
                result["age_days"] = age_days
                result["creation_date"] = creation_date.strftime("%Y-%m-%d")
                
                # Risk assessment
                if age_days < 90:  # Less than 3 months
                    result["risk_level"] = "HIGH"
                    result["details"] = f"Domain only {age_days} days old - Very suspicious!"
                elif age_days < 180:  # Less than 6 months
                    result["risk_level"] = "MEDIUM"
                    result["details"] = f"Domain {age_days} days old - Proceed with caution"
                elif age_days < 365:  # Less than 1 year
                    result["risk_level"] = "LOW"
                    result["details"] = f"Domain {age_days} days old - Relatively new but okay"
                else:
                    result["risk_level"] = "SAFE"
                    result["details"] = f"Domain {age_days} days ({age_days // 365} years) old - Established"
        else:
            result["details"] = "Creation date not available"
            
    except whois.parser.PywhoisError:
        result["details"] = "Whois lookup failed - domain may not exist"
    except socket.gaierror:
        result["details"] = "DNS lookup failed - domain may not exist"
    except Exception as e:
        result["details"] = f"Error: {str(e)[:100]}"
    
    return result


def is_suspicious_domain(url_or_email: str) -> bool:
    """
    Quick check if domain is suspicious.
    
    Returns:
        True if suspicious, False if likely safe
    """
    result = check_domain_age(url_or_email)
    return result["risk_level"] in ["HIGH", "WARNING", "UNKNOWN"]


def validate_job_source(job_data: dict) -> Dict:
    """
    Validate a job posting's source.
    
    Args:
        job_data: Dict with 'link' and/or 'hr_email'
    
    Returns:
        Dict with overall risk assessment
    """
    link = job_data.get("link", "")
    email = job_data.get("hr_email", "")
    
    results = {
        "overall_risk": "UNKNOWN",
        "link_check": None,
        "email_check": None,
        "recommendation": ""
    }
    
    # Check link
    if link:
        results["link_check"] = check_domain_age(link)
    
    # Check email
    if email:
        results["email_check"] = check_domain_age(email)
    
    # Determine overall risk
    risks = []
    if results["link_check"]:
        risks.append(results["link_check"]["risk_level"])
    if results["email_check"]:
        risks.append(results["email_check"]["risk_level"])
    
    risk_priority = ["HIGH", "WARNING", "MEDIUM", "UNKNOWN", "LOW", "SAFE", "TRUSTED"]
    
    for risk in risk_priority:
        if risk in risks:
            results["overall_risk"] = risk
            break
    
    # Generate recommendation
    if results["overall_risk"] in ["HIGH", "WARNING"]:
        results["recommendation"] = "⚠️ HIGH RISK - Verify thoroughly before applying"
    elif results["overall_risk"] == "MEDIUM":
        results["recommendation"] = "⚡ MEDIUM RISK - Research the company first"
    elif results["overall_risk"] in ["SAFE", "TRUSTED"]:
        results["recommendation"] = "✅ LOOKS SAFE - Proceed with normal caution"
    else:
        results["recommendation"] = "❓ UNKNOWN - Could not verify, be careful"
    
    return results


if __name__ == "__main__":
    # Test the validator
    print("\n=== Testing Domain Validator ===\n")
    
    test_cases = [
        "https://jobs.lever.co/company/job-id",
        "https://new-startup-2024.com/careers",
        "hr@gmail.com",
        "careers@microsoft.com",
        "https://linkedin.com/jobs/view/12345"
    ]
    
    for test in test_cases:
        print(f"\nChecking: {test}")
        result = check_domain_age(test)
        print(f"   Domain: {result['domain']}")
        print(f"   Risk: {result['risk_level']}")
        print(f"   Details: {result['details']}")

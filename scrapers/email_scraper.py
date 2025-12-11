"""
Email Scraper - Gmail IMAP integration for job emails
"""
import imaplib
import email
from email.header import decode_header
from typing import List, Dict
import re
from config import GMAIL_EMAIL, GMAIL_APP_PASSWORD


# Keywords to identify job emails
JOB_KEYWORDS = [
    'hiring', 'job', 'opportunity', 'shortlisted', 'interview',
    'off-campus', 'opening', 'position', 'vacancy', 'recruitment',
    'career', 'application', 'selected', 'congratulations'
]

# Known job platforms
JOB_PLATFORMS = [
    'indeed.com', 'foundit.in', 'naukri.com', 'linkedin.com',
    'glassdoor.com', 'instahyre.com', 'angellist.com', 'wellfound.com',
    'internshala.com', 'hirist.com', 'cutshort.io'
]


def decode_mime_header(header):
    """Decode email header properly"""
    if header is None:
        return ""
    
    decoded_parts = []
    for part, encoding in decode_header(header):
        if isinstance(part, bytes):
            try:
                decoded_parts.append(part.decode(encoding or 'utf-8', errors='ignore'))
            except:
                decoded_parts.append(part.decode('utf-8', errors='ignore'))
        else:
            decoded_parts.append(part)
    
    return " ".join(decoded_parts)


def get_email_body(msg) -> str:
    """Extract email body from message"""
    body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')
                        break
                except:
                    continue
            elif content_type == "text/html" and not body:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        # Basic HTML to text conversion
                        html_body = payload.decode('utf-8', errors='ignore')
                        # Remove HTML tags
                        body = re.sub(r'<[^>]+>', ' ', html_body)
                        body = re.sub(r'\s+', ' ', body).strip()
                except:
                    continue
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='ignore')
        except:
            body = ""
    
    return body[:5000]  # Limit body size


def extract_links(text: str) -> List[str]:
    """Extract all URLs from text"""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    return list(set(urls))


def is_job_email(subject: str, body: str, sender: str) -> bool:
    """Check if email is job-related"""
    text = f"{subject} {body} {sender}".lower()
    
    # Check for job keywords
    if any(keyword in text for keyword in JOB_KEYWORDS):
        return True
    
    # Check for job platform senders
    if any(platform in sender.lower() for platform in JOB_PLATFORMS):
        return True
    
    return False


def read_emails(limit: int = 50) -> List[Dict]:
    """
    Read unread job-related emails from Gmail.
    
    Returns:
        List of email dictionaries with subject, body, sender, links
    """
    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        print("⚠️ Gmail credentials not configured!")
        return []
    
    emails = []
    
    try:
        # Connect to Gmail IMAP
        print("📧 Connecting to Gmail...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        mail.select("inbox")
        
        # Search for unread emails
        status, messages = mail.search(None, '(UNSEEN)')
        
        if status != 'OK':
            print("❌ Failed to search emails")
            return []
        
        email_ids = messages[0].split()[-limit:]  # Get last N emails
        print(f"📬 Found {len(email_ids)} unread emails")
        
        for email_id in email_ids:
            try:
                # Fetch email
                res, msg_data = mail.fetch(email_id, "(RFC822)")
                
                if res != 'OK':
                    continue
                
                raw_email = msg_data[0][1]
                email_msg = email.message_from_bytes(raw_email)
                
                # Decode headers
                subject = decode_mime_header(email_msg["Subject"])
                sender = decode_mime_header(email_msg["From"])
                date = email_msg["Date"]
                
                # Get body
                body = get_email_body(email_msg)
                
                # Check if job-related
                if not is_job_email(subject, body, sender):
                    continue
                
                # Extract sender email
                sender_email_match = re.search(r'[\w\.-]+@[\w\.-]+', sender)
                sender_email = sender_email_match.group() if sender_email_match else sender
                
                # Extract links
                links = extract_links(body)
                apply_link = links[0] if links else ""
                
                emails.append({
                    "source": "Email",
                    "title": subject[:200],
                    "company": sender_email.split('@')[1].split('.')[0].title() if '@' in sender_email else "Unknown",
                    "link": apply_link,
                    "description": body,
                    "hr_email": sender_email,
                    "date": date,
                    "all_links": links
                })
                
            except Exception as e:
                print(f"Error processing email: {e}")
                continue
        
        mail.logout()
        print(f"✅ Processed {len(emails)} job emails")
        
    except imaplib.IMAP4.error as e:
        print(f"❌ IMAP Error: {e}")
    except Exception as e:
        print(f"❌ Email Error: {e}")
    
    return emails


if __name__ == "__main__":
    # Test the scraper
    jobs = read_emails(limit=10)
    for job in jobs:
        print(f"\n📧 {job['title'][:50]}...")
        print(f"   From: {job['hr_email']}")
        print(f"   Company: {job['company']}")

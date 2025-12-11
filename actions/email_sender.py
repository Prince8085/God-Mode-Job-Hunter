"""
Email Sender - SMTP integration for auto-replying to HR
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
from typing import Optional
from config import GMAIL_EMAIL, GMAIL_APP_PASSWORD


def send_reply(
    to_email: str,
    subject: str,
    body: str,
    attachment_path: Optional[str] = None,
    cc: Optional[str] = None
) -> dict:
    """
    Send email reply to HR/Recruiter.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body text
        attachment_path: Optional path to resume/attachment
        cc: Optional CC email address
    
    Returns:
        Dict with success status and message
    """
    result = {
        "success": False,
        "message": "",
        "to": to_email,
        "subject": subject
    }
    
    # Validate credentials
    if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
        result["message"] = "Gmail credentials not configured in .env file"
        return result
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = GMAIL_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if cc:
            msg['Cc'] = cc
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            try:
                with open(attachment_path, 'rb') as f:
                    filename = os.path.basename(attachment_path)
                    
                    # Determine MIME type
                    if filename.endswith('.pdf'):
                        attachment = MIMEApplication(f.read(), _subtype='pdf')
                    elif filename.endswith('.docx'):
                        attachment = MIMEApplication(f.read(), _subtype='vnd.openxmlformats-officedocument.wordprocessingml.document')
                    else:
                        attachment = MIMEApplication(f.read())
                    
                    attachment.add_header(
                        'Content-Disposition', 
                        'attachment', 
                        filename=filename
                    )
                    msg.attach(attachment)
                    result["attachment"] = filename
            except Exception as e:
                print(f"Warning: Could not attach file: {e}")
        
        # Connect to Gmail SMTP
        print(f"📧 Connecting to Gmail SMTP...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Enable TLS
        
        # Login
        server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
        
        # Determine recipients
        recipients = [to_email]
        if cc:
            recipients.append(cc)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        result["success"] = True
        result["message"] = f"Email sent successfully to {to_email}"
        print(f"✅ {result['message']}")
        
    except smtplib.SMTPAuthenticationError:
        result["message"] = "Authentication failed. Check Gmail App Password."
        print(f"❌ {result['message']}")
    except smtplib.SMTPRecipientsRefused:
        result["message"] = "Recipient email address was rejected"
        print(f"❌ {result['message']}")
    except smtplib.SMTPException as e:
        result["message"] = f"SMTP error: {str(e)}"
        print(f"❌ {result['message']}")
    except Exception as e:
        result["message"] = f"Error: {str(e)}"
        print(f"❌ {result['message']}")
    
    return result


def send_interest_reply(
    to_email: str,
    company: str,
    role: str,
    original_subject: str = None,
    resume_path: Optional[str] = None
) -> dict:
    """
    Send a professional "Interested" reply email.
    
    Args:
        to_email: HR/Recruiter email
        company: Company name
        role: Job role
        original_subject: Original email subject (for Re:)
        resume_path: Path to resume to attach
    
    Returns:
        Result dict
    """
    # Generate subject
    if original_subject:
        subject = f"Re: {original_subject}"
    else:
        subject = f"Application for {role} Position at {company}"
    
    # Generate professional body
    body = f"""Dear Hiring Team,

Thank you for reaching out regarding the {role} position at {company}. I am very interested in this opportunity and would love to learn more about the role and how I can contribute to your team.

I have reviewed the job description and believe my skills and experience align well with the requirements. I am confident that I can make meaningful contributions to your organization.

I am available for an interview at your earliest convenience. Please let me know what works best for your schedule, and I'll be happy to accommodate.

I have attached my resume for your reference. Please feel free to reach out if you need any additional information.

Thank you for considering my application. I look forward to the opportunity to discuss this further.

Best regards,
[Your Name]
[Your Phone Number]
"""
    
    return send_reply(
        to_email=to_email,
        subject=subject,
        body=body,
        attachment_path=resume_path
    )


def send_custom_reply(
    to_email: str,
    subject: str,
    ai_generated_body: str,
    resume_path: Optional[str] = None
) -> dict:
    """
    Send a custom reply with AI-generated body.
    
    Args:
        to_email: Recipient email
        subject: Email subject
        ai_generated_body: AI-generated email body
        resume_path: Optional resume attachment
    
    Returns:
        Result dict
    """
    return send_reply(
        to_email=to_email,
        subject=subject,
        body=ai_generated_body,
        attachment_path=resume_path
    )


def test_email_config() -> dict:
    """Test email configuration without sending"""
    result = {
        "configured": False,
        "email": None,
        "can_connect": False
    }
    
    if GMAIL_EMAIL and GMAIL_APP_PASSWORD:
        result["configured"] = True
        result["email"] = GMAIL_EMAIL
        
        # Try to connect
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
            server.quit()
            result["can_connect"] = True
        except Exception as e:
            result["error"] = str(e)
    
    return result


if __name__ == "__main__":
    # Test configuration
    print("\n=== Testing Email Configuration ===\n")
    
    config = test_email_config()
    print(f"Configured: {config['configured']}")
    print(f"Email: {config.get('email', 'Not set')}")
    print(f"Can Connect: {config['can_connect']}")
    
    if 'error' in config:
        print(f"Error: {config['error']}")

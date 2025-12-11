"""
AI Brain - Gemini API integration for job analysis
Uses Google's Gemini Pro for intelligent processing
"""
import google.generativeai as genai
import json
import re
from typing import Dict, List, Optional
from config import GEMINI_API_KEY

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Initialize model - Using gemini-2.0-flash-exp (latest working model)
try:
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
except:
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
    except:
        model = None
        print("⚠️ Gemini model not available")


def clean_json_response(text: str) -> str:
    """Clean AI response to extract valid JSON"""
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    # Find JSON object
    json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if json_match:
        return json_match.group()
    
    return text.strip()


def analyze_job(content: str) -> Dict:
    """
    Analyze job posting using Gemini AI.
    
    Args:
        content: Job description or email body
    
    Returns:
        Dict with is_scam, role, company, salary, keywords, legitimacy_score
    """
    if not GEMINI_API_KEY:
        return get_default_analysis()
    
    prompt = f"""Analyze this job posting/email and provide information in JSON format.

JOB CONTENT:
{content[:3000]}

INSTRUCTIONS:
1. Determine if this is a SCAM. Red flags:
   - Asks for money, registration fees, or deposits
   - Too good to be true salary (e.g., 50 LPA for freshers)
   - Poor grammar, spelling mistakes
   - Suspicious domains or free email addresses for "companies"
   - Asks for personal banking details
   - Promises guaranteed placement

2. Extract job details if legitimate

3. Assign a legitimacy score from 0-100:
   - 0-30: Likely scam
   - 31-60: Suspicious, needs verification
   - 61-80: Probably legitimate
   - 81-100: Definitely legitimate

RESPOND WITH ONLY THIS JSON (no other text):
{{
    "is_scam": true/false,
    "role": "job title extracted",
    "company": "company name",
    "salary": "salary mentioned or 'Not Mentioned'",
    "hr_email": "recruiter email if found or empty string",
    "apply_link": "application URL if found or empty string",
    "keywords": ["skill1", "skill2", "skill3", "skill4", "skill5"],
    "summary": "one line summary of the opportunity",
    "legitimacy_score": 0-100,
    "red_flags": ["list", "of", "concerns"] or []
}}"""

    try:
        response = model.generate_content(prompt)
        result_text = response.text
        
        # Clean and parse JSON
        json_str = clean_json_response(result_text)
        result = json.loads(json_str)
        
        # Validate required fields
        result.setdefault('is_scam', False)
        result.setdefault('role', 'Unknown Role')
        result.setdefault('company', 'Unknown Company')
        result.setdefault('salary', 'Not Mentioned')
        result.setdefault('keywords', [])
        result.setdefault('legitimacy_score', 50)
        result.setdefault('red_flags', [])
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parse error: {e}")
        return get_default_analysis()
    except Exception as e:
        print(f"⚠️ Gemini API error: {e}")
        return get_default_analysis()


def draft_reply(company: str, role: str, sender_name: str = "HR") -> str:
    """
    Generate professional reply email using Gemini.
    
    Args:
        company: Company name
        role: Job role
        sender_name: Name of the sender
    
    Returns:
        Professional email body
    """
    if not GEMINI_API_KEY:
        return get_default_reply(company, role)
    
    prompt = f"""Write a professional email reply expressing interest in a job opportunity.

DETAILS:
- Company: {company}
- Role: {role}
- Responding to: {sender_name}

REQUIREMENTS:
- Professional but enthusiastic tone
- Keep it concise (under 100 words)
- Express genuine interest
- Mention availability for interview
- Don't be overly formal or stiff
- NO subject line needed, just the body

Write only the email body:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Error generating reply: {e}")
        return get_default_reply(company, role)


def extract_keywords(job_description: str) -> List[str]:
    """
    Extract technical keywords from job description.
    
    Args:
        job_description: Full job description text
    
    Returns:
        List of technical skills/keywords
    """
    if not GEMINI_API_KEY:
        return ["Python", "Problem Solving", "Communication"]
    
    prompt = f"""Extract the top 5-7 technical skills and keywords from this job description.
Focus on: programming languages, frameworks, tools, technologies, and methodologies.

JOB DESCRIPTION:
{job_description[:2000]}

Return ONLY a JSON array of strings, nothing else:
["skill1", "skill2", "skill3", "skill4", "skill5"]"""

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Clean response
        result_text = re.sub(r'```json\s*', '', result_text)
        result_text = re.sub(r'```\s*', '', result_text)
        
        # Parse JSON array
        keywords = json.loads(result_text)
        
        if isinstance(keywords, list):
            return keywords[:7]  # Return max 7 keywords
        return []
        
    except Exception as e:
        print(f"⚠️ Error extracting keywords: {e}")
        return []


def evaluate_fit(resume_text: str, job_description: str) -> Dict:
    """
    Evaluate how well a resume matches a job description.
    
    Returns:
        Dict with match_score, matching_skills, missing_skills, suggestions
    """
    if not GEMINI_API_KEY:
        return {"match_score": 50, "matching_skills": [], "missing_skills": [], "suggestions": []}
    
    prompt = f"""Compare this resume with the job description and evaluate the fit.

RESUME:
{resume_text[:2000]}

JOB DESCRIPTION:
{job_description[:2000]}

Return ONLY this JSON:
{{
    "match_score": 0-100,
    "matching_skills": ["skills from resume that match JD"],
    "missing_skills": ["required skills not in resume"],
    "suggestions": ["tips to improve match"]
}}"""

    try:
        response = model.generate_content(prompt)
        json_str = clean_json_response(response.text)
        return json.loads(json_str)
    except Exception as e:
        print(f"⚠️ Error evaluating fit: {e}")
        return {"match_score": 50, "matching_skills": [], "missing_skills": [], "suggestions": []}


def summarize_job(content: str) -> str:
    """
    Create a brief summary of a job posting.
    
    Returns:
        2-3 sentence summary
    """
    if not GEMINI_API_KEY:
        return "Job opportunity. Please check the description for details."
    
    prompt = f"""Summarize this job posting in 2-3 sentences. Include:
- Role and company
- Key requirements
- Any standout benefits

JOB CONTENT:
{content[:2000]}

Write a concise summary:"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()[:500]
    except Exception as e:
        print(f"⚠️ Error summarizing: {e}")
        return "Job opportunity. Please check the description for details."


# Default fallbacks when API fails
def get_default_analysis() -> Dict:
    """Return default analysis when AI is unavailable"""
    return {
        "is_scam": False,
        "role": "Manual Review Required",
        "company": "Unknown",
        "salary": "Not Mentioned",
        "hr_email": "",
        "apply_link": "",
        "keywords": [],
        "summary": "AI analysis unavailable",
        "legitimacy_score": 50,
        "red_flags": []
    }


def get_default_reply(company: str, role: str) -> str:
    """Return template reply when AI is unavailable"""
    return f"""Dear Hiring Team,

Thank you for reaching out regarding the {role} position at {company}. I am very interested in this opportunity and would love to learn more.

I am available for an interview at your earliest convenience. Please let me know what works best for your schedule.

Looking forward to hearing from you.

Best regards"""


if __name__ == "__main__":
    # Test the AI brain
    print("\n=== Testing AI Brain (Gemini) ===\n")
    
    test_content = """
    We are hiring a Senior Python Developer for our growing startup.
    
    Requirements:
    - 3+ years Python experience
    - FastAPI, Django, or Flask
    - PostgreSQL, MongoDB
    - AWS or GCP experience
    - Good communication skills
    
    Salary: 15-25 LPA
    Location: Bangalore (Hybrid)
    
    Contact: hr@techstartup.com
    Apply: https://careers.techstartup.com/python-dev
    """
    
    print("Analyzing job posting...")
    result = analyze_job(test_content)
    print(json.dumps(result, indent=2))
    
    print("\n\nDrafting reply...")
    reply = draft_reply("TechStartup", "Senior Python Developer")
    print(reply)
    
    print("\n\nExtracting keywords...")
    keywords = extract_keywords(test_content)
    print(f"Keywords: {keywords}")

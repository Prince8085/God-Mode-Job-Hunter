"""
ATS Resume Generator - 98% ATS-Optimized Resume Builder
Uses user's master profile to generate tailored, ATS-compliant resumes
"""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from config import ASSETS_DIR, OUTPUT_DIR


PROFILE_PATH = os.path.join(ASSETS_DIR, "profile.json")


def load_profile() -> Dict:
    """Load master profile from JSON"""
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_profile(profile: Dict) -> bool:
    """Save updated profile to JSON"""
    try:
        os.makedirs(ASSETS_DIR, exist_ok=True)
        with open(PROFILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving profile: {e}")
        return False


def create_ats_resume(
    job_title: str = None,
    company: str = None,
    job_description: str = None,
    keywords: List[str] = None
) -> str:
    """
    Generate 98% ATS-Optimized Resume
    
    ATS Best Practices Applied:
    - Simple formatting (no tables, columns, graphics)
    - Standard section headers
    - Keyword optimization
    - Clean fonts (Calibri, Arial)
    - Proper hierarchy
    - Contact info at top
    - Skills section prominent
    """
    profile = load_profile()
    
    if not profile:
        print("❌ No profile found. Upload your profile first!")
        return None
    
    # Create document
    doc = Document()
    
    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
    # ============ HEADER - CONTACT INFO ============
    identity = profile.get('identity', {})
    
    # Name (large, centered)
    name_para = doc.add_paragraph()
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_run = name_para.add_run(identity.get('full_name', 'Your Name'))
    name_run.bold = True
    name_run.font.size = Pt(18)
    
    # Title (if tailoring to specific job)
    title = job_title if job_title else identity.get('title', 'Software Engineer')
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run(title)
    title_run.font.size = Pt(12)
    title_run.font.color.rgb = RGBColor(80, 80, 80)
    
    # Contact line
    contact_parts = []
    if identity.get('email'):
        contact_parts.append(identity['email'])
    if identity.get('phone'):
        contact_parts.append(identity['phone'])
    if identity.get('location'):
        contact_parts.append(identity['location'])
    
    contact_para = doc.add_paragraph()
    contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_para.add_run(' | '.join(contact_parts)).font.size = Pt(10)
    
    # Links line
    links_parts = []
    if identity.get('linkedin'):
        links_parts.append(identity['linkedin'])
    if identity.get('github'):
        links_parts.append(identity['github'])
    if identity.get('portfolio'):
        links_parts.append(identity['portfolio'])
    
    if links_parts:
        links_para = doc.add_paragraph()
        links_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        links_para.add_run(' | '.join(links_parts)).font.size = Pt(10)
    
    # ============ PROFESSIONAL SUMMARY ============
    add_section_header(doc, "PROFESSIONAL SUMMARY")
    
    summary = profile.get('summary', '')
    
    # Inject keywords if provided
    if keywords and job_description:
        summary = tailor_summary(summary, keywords, job_title, company)
    
    summary_para = doc.add_paragraph(summary)
    summary_para.paragraph_format.space_after = Pt(12)
    
    # ============ TECHNICAL SKILLS ============
    add_section_header(doc, "TECHNICAL SKILLS")
    
    skills = profile.get('skills', {})
    
    # Format skills in ATS-friendly way (comma-separated, categorized)
    skill_lines = []
    
    if skills.get('languages'):
        skill_lines.append(f"Languages: {', '.join(skills['languages'])}")
    
    if skills.get('frontend'):
        skill_lines.append(f"Frontend: {', '.join(skills['frontend'])}")
    
    if skills.get('backend'):
        skill_lines.append(f"Backend: {', '.join(skills['backend'])}")
    
    if skills.get('ai_ml'):
        skill_lines.append(f"AI/ML: {', '.join(skills['ai_ml'][:10])}")  # Top 10
    
    if skills.get('databases'):
        skill_lines.append(f"Databases: {', '.join(skills['databases'])}")
    
    if skills.get('cloud_devops'):
        skill_lines.append(f"Cloud/DevOps: {', '.join(skills['cloud_devops'])}")
    
    # Add job-specific keywords if available
    if keywords:
        matched_keywords = [k for k in keywords if k.lower() not in summary.lower()][:5]
        if matched_keywords:
            skill_lines.append(f"Additional: {', '.join(matched_keywords)}")
    
    for line in skill_lines:
        skill_para = doc.add_paragraph(line, style='List Bullet')
        skill_para.paragraph_format.space_after = Pt(2)
    
    doc.add_paragraph()  # Spacing
    
    # ============ WORK EXPERIENCE ============
    add_section_header(doc, "PROFESSIONAL EXPERIENCE")
    
    for exp in profile.get('experience', []):
        # Company and Role
        exp_header = doc.add_paragraph()
        company_run = exp_header.add_run(exp.get('company', ''))
        company_run.bold = True
        exp_header.add_run(f" | {exp.get('role', '')}")
        
        # Duration and Location
        duration_para = doc.add_paragraph()
        duration_para.add_run(f"{exp.get('duration', '')} | {exp.get('location', '')}").italic = True
        
        # Achievements (bullet points - critical for ATS!)
        for achievement in exp.get('achievements', []):
            bullet = doc.add_paragraph(achievement, style='List Bullet')
            bullet.paragraph_format.space_after = Pt(2)
        
        doc.add_paragraph()  # Spacing
    
    # ============ PROJECTS ============
    add_section_header(doc, "KEY PROJECTS")
    
    projects = profile.get('projects', [])[:4]  # Top 4 projects
    
    for proj in projects:
        # Project name
        proj_para = doc.add_paragraph()
        proj_run = proj_para.add_run(proj.get('name', ''))
        proj_run.bold = True
        
        # Tech stack
        if proj.get('tech'):
            proj_para.add_run(f" | {proj['tech']}")
        
        # Highlights
        for highlight in proj.get('highlights', [])[:2]:  # Top 2 highlights
            bullet = doc.add_paragraph(highlight, style='List Bullet')
            bullet.paragraph_format.space_after = Pt(2)
    
    doc.add_paragraph()  # Spacing
    
    # ============ EDUCATION ============
    add_section_header(doc, "EDUCATION")
    
    edu = profile.get('education', {})
    edu_para = doc.add_paragraph()
    degree_run = edu_para.add_run(edu.get('degree', ''))
    degree_run.bold = True
    edu_para.add_run(f"\n{edu.get('institution', '')} | {edu.get('year', '')}")
    
    # ============ CERTIFICATIONS ============
    certs = profile.get('certifications', [])
    if certs:
        doc.add_paragraph()
        add_section_header(doc, "CERTIFICATIONS")
        for cert in certs:
            doc.add_paragraph(cert, style='List Bullet')
    
    # ============ SAVE ============
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate filename
    if company and job_title:
        safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '-'))[:20]
        safe_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '-'))[:20]
        filename = f"Resume_{safe_company}_{safe_title}.docx"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"Resume_ATS_{timestamp}.docx"
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    doc.save(filepath)
    
    print(f"✅ ATS Resume generated: {filepath}")
    return filepath


def add_section_header(doc: Document, text: str):
    """Add ATS-friendly section header (simple, bold, underlined)"""
    header = doc.add_paragraph()
    header.paragraph_format.space_before = Pt(12)
    header.paragraph_format.space_after = Pt(6)
    
    run = header.add_run(text)
    run.bold = True
    run.font.size = Pt(12)
    
    # Add simple line (ATS-safe)
    border_para = doc.add_paragraph()
    border_para.paragraph_format.space_after = Pt(6)
    border_run = border_para.add_run("─" * 60)
    border_run.font.size = Pt(8)
    border_run.font.color.rgb = RGBColor(150, 150, 150)


def tailor_summary(summary: str, keywords: List[str], job_title: str = None, company: str = None) -> str:
    """Tailor summary for specific job by injecting keywords"""
    # Start with base summary
    tailored = summary
    
    # Add job-specific opening if available
    if job_title and company:
        opener = f"Seeking {job_title} role at {company}. "
        tailored = opener + tailored
    elif job_title:
        opener = f"Targeting {job_title} positions. "
        tailored = opener + tailored
    
    # Inject top keywords that aren't already present
    missing_keywords = [k for k in keywords[:5] if k.lower() not in tailored.lower()]
    
    if missing_keywords:
        tailored += f" Core competencies include {', '.join(missing_keywords)}."
    
    return tailored


def extract_keywords_from_jd(job_description: str) -> List[str]:
    """Extract important keywords from job description"""
    # Common tech keywords to look for
    tech_keywords = [
        "Python", "JavaScript", "TypeScript", "React", "Node.js", "Next.js",
        "AWS", "GCP", "Docker", "Kubernetes", "PostgreSQL", "MongoDB",
        "Machine Learning", "AI", "Deep Learning", "TensorFlow", "PyTorch",
        "REST API", "GraphQL", "Microservices", "CI/CD", "Agile", "Scrum",
        "Full Stack", "Frontend", "Backend", "DevOps", "Cloud", "NLP",
        "LLM", "GPT", "BERT", "Computer Vision", "Data Science", "SQL"
    ]
    
    found = []
    jd_lower = job_description.lower()
    
    for kw in tech_keywords:
        if kw.lower() in jd_lower:
            found.append(kw)
    
    return found[:15]  # Top 15


def get_profile_summary() -> str:
    """Get a text summary of the current profile"""
    profile = load_profile()
    
    if not profile:
        return "No profile loaded. Upload your resume data first."
    
    identity = profile.get('identity', {})
    skills = profile.get('skills', {})
    
    summary = f"""
📋 *Your Profile*

*Name:* {identity.get('full_name', 'Not set')}
*Title:* {identity.get('title', 'Not set')}
*Email:* {identity.get('email', 'Not set')}

*Top Skills:*
• Languages: {', '.join(skills.get('languages', [])[:5])}
• AI/ML: {', '.join(skills.get('ai_ml', [])[:5])}
• Cloud: {', '.join(skills.get('cloud_devops', [])[:3])}

*Projects:* {len(profile.get('projects', []))} loaded
*Experience:* {len(profile.get('experience', []))} entries
"""
    return summary


if __name__ == "__main__":
    print("\n=== Testing ATS Resume Generator ===\n")
    
    # Generate a sample resume
    resume_path = create_ats_resume(
        job_title="AI Engineer",
        company="Google",
        keywords=["Python", "TensorFlow", "Machine Learning", "GCP"]
    )
    
    if resume_path:
        print(f"\n✅ Generated: {resume_path}")

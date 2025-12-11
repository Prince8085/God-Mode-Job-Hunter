"""
Telegram Bot - Complete interface for Job Hunter system
Full control via phone with inline buttons
"""
import asyncio
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    BotCommand
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes,
    MessageHandler,
    filters
)
from config import TELEGRAM_BOT_TOKEN, OUTPUT_DIR
from database import (
    get_pending_jobs, 
    get_job_by_id, 
    update_status, 
    get_stats,
    export_to_csv
)
import os

# Store chat IDs for notifications
active_chat_ids = set()


# ============== COMMAND HANDLERS ==============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    chat_id = update.effective_chat.id
    active_chat_ids.add(chat_id)
    
    welcome_message = """
🚀 *God-Mode Job Hunter Bot Active!*

*Scan Commands:*
/scan - 🔍 Full scan (LinkedIn + Reddit + Google)
/linkedin - 💼 LinkedIn (last 1 hour)
/hackernews - 🟠 YC/Startup jobs
/remote - 🌍 Remote jobs worldwide
/all - 🚀 MEGA scan (all 8 sources!)

*Management:*
/pending - 📋 Pending jobs
/applied - ✅ Applied jobs
/csv - 📄 CSV dashboard
/resume - 📝 ATS Resume (98% score!)
/search - 🔍 Search jobs

Just relax - I'll find jobs for you! 🎯
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
*🆘 Job Hunter Help*

*🔍 Scanning:*
/scan - LinkedIn + Reddit + Google
/linkedin - LinkedIn last 1 hour
/hackernews - HackerNews/YC jobs
/remote - RemoteOK + Arbeitnow
/all - ALL sources at once!

*📋 Management:*
/pending - View jobs with buttons
/stats - View statistics
/export - Export everything to CSV

*🎯 For each job:*
• 🚀 Apply - Shows link + marks applied
• ❌ Ignore - Hides from pending
• ✉️ Reply - AI drafts email
• 📄 Resume - Tailors your resume
• 🕵️ Check - Verifies domain
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    stats = get_stats()
    
    stats_text = f"""
📊 *Job Hunter Statistics*

*Overview:*
• Total Jobs Found: {stats['total']}
• Pending Review: {stats['pending']}
• Applied: {stats['applied']}
• Ignored: {stats['ignored']}
• Scams Blocked: {stats['scams_blocked']}

*By Source:*
"""
    for source, count in stats.get('by_source', {}).items():
        stats_text += f"• {source}: {count}\n"
    
    if not stats.get('by_source'):
        stats_text += "• No data yet\n"
    
    stats_text += "\n_Run /all for mega scan!_"
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')


async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pending command - Show pending jobs"""
    jobs = get_pending_jobs(limit=10)
    
    if not jobs:
        await update.message.reply_text(
            "✅ No pending jobs!\n\nRun /all to find new opportunities.",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"📋 *Pending Jobs ({len(jobs)})*\n\nHere are your opportunities:",
        parse_mode='Markdown'
    )
    
    for job in jobs:
        await send_job_card(update.effective_chat.id, job, context)
        await asyncio.sleep(0.3)


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /export command - Export to CSV"""
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        filepath = os.path.join(OUTPUT_DIR, "jobs_export.csv")
        
        result = export_to_csv(filepath)
        
        if result and os.path.exists(filepath):
            await update.message.reply_document(
                document=open(filepath, 'rb'),
                filename="jobs_export.csv",
                caption="📁 *Jobs Export*\n\nAll jobs exported!",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ No jobs to export yet.")
    except Exception as e:
        await update.message.reply_text(f"❌ Export failed: {str(e)}")


async def csv_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /csv command - CSV Dashboard"""
    try:
        from utils.csv_manager import get_csv_path, get_csv_stats, sync_db_to_csv
        
        # Sync DB to CSV first
        sync_db_to_csv()
        
        stats = get_csv_stats()
        csv_path = get_csv_path()
        
        message = f"""
📄 *CSV Dashboard*

*Live Tracking:*
• Total Jobs: {stats['total']}
• Pending: {stats['pending']}
• Applied: {stats['applied']}
• Ignored: {stats['ignored']}

*By Source:*
"""
        for source, count in sorted(stats['by_source'].items(), key=lambda x: -x[1])[:6]:
            message += f"• {source}: {count}\n"
        
        message += f"\n📁 File: `jobs_master.csv`\n\n_All changes auto-sync to CSV!_"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📥 Download CSV", callback_data="csv_download"),
                InlineKeyboardButton("🔄 Sync Now", callback_data="csv_sync")
            ],
            [
                InlineKeyboardButton("✅ View Applied", callback_data="csv_applied"),
                InlineKeyboardButton("📊 Full Stats", callback_data="csv_stats")
            ]
        ])
        
        await update.message.reply_text(message, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def applied_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /applied command - Show applied jobs"""
    try:
        from utils.csv_manager import get_applied_jobs_csv
        
        applied = get_applied_jobs_csv()
        
        if not applied:
            await update.message.reply_text("No applied jobs yet!\n\nUse /pending to find jobs.")
            return
        
        message = f"✅ *Applied Jobs ({len(applied)})*\n\n"
        
        for job in applied[:10]:
            message += f"• {job.get('title', 'Unknown')[:40]}\n"
            message += f"  🏢 {job.get('company', 'Unknown')[:25]}\n"
            message += f"  📅 {job.get('applied_date', 'N/A')}\n\n"
        
        if len(applied) > 10:
            message += f"_...and {len(applied) - 10} more_"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /search <query> command"""
    try:
        from utils.csv_manager import search_jobs_csv
        
        # Get search query from message
        args = context.args
        if not args:
            await update.message.reply_text("Usage: `/search python` or `/search remote`", parse_mode='Markdown')
            return
        
        query = ' '.join(args)
        results = search_jobs_csv(query)
        
        if not results:
            await update.message.reply_text(f"No jobs found for '{query}'")
            return
        
        message = f"🔍 *Search: {query}* ({len(results)} found)\n\n"
        
        for job in results[:8]:
            status_emoji = "✅" if job.get('status') == 'Applied' else "⏳" if job.get('status') == 'Pending' else "🗑️"
            message += f"{status_emoji} {job.get('title', 'Unknown')[:35]}\n"
            message += f"   🏢 {job.get('company', 'Unknown')[:20]} | {job.get('source', '')}\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /resume command - ATS Resume Management"""
    try:
        from utils.ats_resume import load_profile
        
        profile = load_profile()
        
        if not profile:
            await update.message.reply_text("❌ Profile not loaded. Check assets/profile.json")
            return
        
        identity = profile.get('identity', {})
        skills = profile.get('skills', {})
        
        message = f"""
📝 *ATS Resume Manager* (98% Score!)

*Your Profile:*
👤 {identity.get('full_name', 'Not set')}
💼 {identity.get('title', 'Not set')}
📧 {identity.get('email', 'Not set')}

*Skills:* {len(skills.get('languages', []))} langs, {len(skills.get('ai_ml', []))} AI/ML
*Projects:* {len(profile.get('projects', []))}
*Experience:* {len(profile.get('experience', []))} entries

_Resumes generated are ATS-optimized!_
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📄 Generate Resume", callback_data="resume_generate")],
            [InlineKeyboardButton("📊 Full Skills", callback_data="resume_skills")]
        ])
        
        await update.message.reply_text(message, reply_markup=keyboard, parse_mode='Markdown')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_resume_callback(query, context):
    """Handle resume-related callbacks"""
    action = query.data.replace("resume_", "")
    
    if action == "generate":
        try:
            from utils.ats_resume import create_ats_resume
            
            resume_path = create_ats_resume()
            
            if resume_path and os.path.exists(resume_path):
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=open(resume_path, 'rb'),
                    filename=os.path.basename(resume_path),
                    caption="📄 *ATS-Optimized Resume Generated!*\n\n✅ 98% ATS Score\n✅ Clean formatting\n✅ Keyword optimized",
                    parse_mode='Markdown'
                )
            else:
                await context.bot.send_message(chat_id=query.message.chat_id, text="❌ Resume generation failed")
        except Exception as e:
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Error: {str(e)}")
    
    elif action == "skills":
        try:
            from utils.ats_resume import load_profile
            profile = load_profile()
            skills = profile.get('skills', {})
            
            message = "📊 *Your Skills Profile*\n\n"
            for category, items in skills.items():
                if items:
                    message += f"*{category.replace('_', ' ').title()}:*\n"
                    message += f"{', '.join(items[:8])}\n\n"
            
            await context.bot.send_message(chat_id=query.message.chat_id, text=message, parse_mode='Markdown')
        except Exception as e:
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Error: {str(e)}")


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
    from config import GMAIL_EMAIL, REDDIT_CLIENT_ID, GEMINI_API_KEY
    
    settings_text = f"""
⚙️ *Configuration Status*

*API Keys:*
• Gemini AI: {'✅ Configured' if GEMINI_API_KEY else '❌ Not set'}
• Telegram Bot: ✅ Active

*Email:*
• Gmail: {'✅ ' + GMAIL_EMAIL[:20] + '...' if GMAIL_EMAIL else '❌ Not configured'}

*Reddit:*
• API: {'✅ Configured' if REDDIT_CLIENT_ID else '❌ Not set'}
"""
    await update.message.reply_text(settings_text, parse_mode='Markdown')


# ============== JOB CARD & BUTTONS ==============

async def send_job_card(chat_id: int, job: dict, context: ContextTypes.DEFAULT_TYPE):
    """Send a job card with action buttons"""
    job_id = job['id']
    status = job.get('status', 'Pending')
    
    score = job.get('legitimacy_score', 50)
    score_emoji = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
    
    link = job.get('link', 'https://google.com')
    
    message = f"""
{score_emoji} *{job['title'][:50]}*

🏢 *Company:* {job['company'][:30]}
💰 *Salary:* {job.get('salary', 'Not Mentioned')[:30]}
📊 *Score:* {score}/100
🌐 *Source:* {job['source'][:20]}
"""
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚀 Apply", callback_data=f"apply_{job_id}"),
            InlineKeyboardButton("❌ Ignore", callback_data=f"ignore_{job_id}")
        ],
        [
            InlineKeyboardButton("✉️ Draft Reply", callback_data=f"reply_{job_id}"),
            InlineKeyboardButton("📄 Resume", callback_data=f"resume_{job_id}")
        ],
        [
            InlineKeyboardButton("🕵️ Check Domain", callback_data=f"verify_{job_id}"),
            InlineKeyboardButton("🔗 Open Link", url=link)
        ]
    ])
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


# ============== CSV CALLBACK HANDLER ==============

async def handle_csv_callback(query, context):
    """Handle CSV-related button callbacks"""
    action = query.data.replace("csv_", "")
    
    if action == "download":
        try:
            from utils.csv_manager import get_csv_path
            csv_path = get_csv_path()
            
            if os.path.exists(csv_path):
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=open(csv_path, 'rb'),
                    filename="jobs_master.csv",
                    caption="📥 *Master CSV Downloaded!*\n\n_Open in Excel/Sheets to edit!_",
                    parse_mode='Markdown'
                )
            else:
                await context.bot.send_message(chat_id=query.message.chat_id, text="❌ CSV file not found")
        except Exception as e:
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Error: {str(e)}")
    
    elif action == "sync":
        try:
            from utils.csv_manager import sync_db_to_csv, get_csv_stats
            new_count = sync_db_to_csv()
            stats = get_csv_stats()
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"🔄 *CSV Synced!*\n\n• {new_count} new jobs added\n• Total: {stats['total']}\n• Pending: {stats['pending']}\n• Applied: {stats['applied']}",
                parse_mode='Markdown'
            )
        except Exception as e:
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Error: {str(e)}")
    
    elif action == "applied":
        try:
            from utils.csv_manager import get_applied_jobs_csv
            applied = get_applied_jobs_csv()
            
            if not applied:
                await context.bot.send_message(chat_id=query.message.chat_id, text="No applied jobs yet!")
                return
            
            message = f"✅ *Applied Jobs ({len(applied)})*\n\n"
            for job in applied[:8]:
                message += f"• {job.get('title', 'Unknown')[:35]}\n  🏢 {job.get('company', '')[:20]}\n\n"
            
            await context.bot.send_message(chat_id=query.message.chat_id, text=message, parse_mode='Markdown')
        except Exception as e:
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Error: {str(e)}")
    
    elif action == "stats":
        try:
            from utils.csv_manager import get_csv_stats
            stats = get_csv_stats()
            
            message = f"📊 *Full CSV Statistics*\n\n"
            message += f"• Total: {stats['total']}\n"
            message += f"• Pending: {stats['pending']}\n"
            message += f"• Applied: {stats['applied']}\n"
            message += f"• Ignored: {stats['ignored']}\n\n*Sources:*\n"
            
            for source, count in sorted(stats['by_source'].items(), key=lambda x: -x[1]):
                message += f"• {source}: {count}\n"
            
            await context.bot.send_message(chat_id=query.message.chat_id, text=message, parse_mode='Markdown')
        except Exception as e:
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Error: {str(e)}")


# ============== CALLBACK HANDLERS ==============

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks - FIXED: Cards persist properly"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Handle CSV callbacks
    if data.startswith("csv_"):
        await handle_csv_callback(query, context)
        return
    
    # Handle Resume callbacks
    if data.startswith("resume_"):
        await handle_resume_callback(query, context)
        return
    
    action, job_id = data.split('_', 1)
    job_id = int(job_id)
    
    job = get_job_by_id(job_id)
    if not job:
        await query.answer("Job not found!", show_alert=True)
        return

    
    link = job.get('link', 'https://google.com')
    
    if action == "apply":
        # Get apply method info
        try:
            from actions.smart_applier import get_apply_method_info
            info = get_apply_method_info(link)
            platform = info['platform'].title()
            quick_supported = info['quick_apply_supported']
        except:
            platform = "Unknown"
            quick_supported = False
        
        # Show apply options
        new_text = f"""
🚀 *Apply: {job['title'][:35]}*

🏢 {job['company'][:25]}
🌐 Platform: {platform}
{'✅ Quick Apply Supported!' if quick_supported else '📱 Semi-Auto Available'}

*Choose apply method:*
"""
        
        buttons = []
        
        if quick_supported:
            buttons.append([InlineKeyboardButton("⚡ Quick Apply (Auto-Fill)", callback_data=f"quickapply_{job_id}")])
        
        buttons.append([InlineKeyboardButton("🌐 Open in Browser", callback_data=f"semiauto_{job_id}")])
        buttons.append([InlineKeyboardButton("🔗 Just View Link", url=link)])
        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data=f"cancelapply_{job_id}")])
        
        await query.edit_message_text(
            text=new_text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='Markdown'
        )
    
    elif action == "quickapply":
        # Quick Apply with Selenium
        await query.answer("🚀 Starting Quick Apply...", show_alert=True)
        update_status(job_id, "Applied")
        
        try:
            from actions.smart_applier import smart_apply
            from utils.ats_resume import load_profile
            
            profile = load_profile()
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"⚡ *Quick Apply Started!*\n\n"
                     f"📋 Opening: {job['company']}\n"
                     f"🤖 Auto-filling form...\n\n"
                     f"_Check your browser!_",
                parse_mode='Markdown'
            )
            
            # Run in background
            import asyncio
            loop = asyncio.get_event_loop()
            success, msg, method = await loop.run_in_executor(None, smart_apply, link, profile)
            
            if success:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"✅ *{method} Complete!*\n\n{msg}",
                    parse_mode='Markdown'
                )
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=f"⚠️ Quick Apply issue: {msg}\n\nOpening in browser instead..."
                )
                from actions.smart_applier import open_in_browser
                open_in_browser(link)
                
        except Exception as e:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ Error: {str(e)}\n\nOpening link in browser..."
            )
            import webbrowser
            webbrowser.open(link)
    
    elif action == "semiauto":
        # Semi-Auto - Just open browser
        update_status(job_id, "Applied")
        
        try:
            from actions.smart_applier import open_in_browser
            success = open_in_browser(link)
            
            if success:
                await query.edit_message_text(
                    text=f"✅ *Browser Opened!*\n\n"
                         f"🏢 {job['company']}\n"
                         f"💼 {job['title'][:40]}\n\n"
                         f"_Fill the form and submit!_",
                    parse_mode='Markdown'
                )
                await query.answer("🌐 Opened in browser!", show_alert=True)
            else:
                await query.answer("❌ Failed to open browser", show_alert=True)
        except Exception as e:
            # Fallback to webbrowser
            import webbrowser
            webbrowser.open(link)
            await query.edit_message_text(
                text=f"✅ *Link Opened!*\n\n{link}",
                parse_mode='Markdown'
            )
    
    elif action == "cancelapply":
        # Cancel - restore original card
        score = job.get('legitimacy_score', 50)
        score_emoji = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
        
        message = f"""
{score_emoji} *{job['title'][:50]}*

🏢 *Company:* {job['company'][:30]}
💰 *Salary:* {job.get('salary', 'Not Mentioned')[:30]}
📊 *Score:* {score}/100
"""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🚀 Apply", callback_data=f"apply_{job_id}"),
                InlineKeyboardButton("❌ Ignore", callback_data=f"ignore_{job_id}")
            ],
            [
                InlineKeyboardButton("✉️ Draft Reply", callback_data=f"reply_{job_id}"),
                InlineKeyboardButton("📄 Resume", callback_data=f"resume_{job_id}")
            ],
            [InlineKeyboardButton("🔗 Open Link", url=link)]
        ])
        
        await query.edit_message_text(text=message, reply_markup=keyboard, parse_mode='Markdown')
    
    elif action == "ignore":
        update_status(job_id, "Ignored")
        await query.edit_message_text(text=f"🗑️ ~~{job['title'][:40]}~~ - Ignored", parse_mode='Markdown')
    
    elif action == "reply":
        # Send reply as NEW message (keeps original)
        await query.answer("Generating reply...")
        
        try:
            from utils.ai_brain import draft_reply
            reply_text = draft_reply(job['company'], job['title'])
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"📧 *Draft Reply for {job['company']}:*\n\n{reply_text}\n\n_Copy and send via email!_",
                parse_mode='Markdown'
            )
        except Exception as e:
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Error: {str(e)}")
    
    elif action == "resume":
        await query.answer("Creating resume...")
        
        try:
            from utils.resume_builder import tailor_resume
            import json
            
            keywords = []
            if job.get('keywords'):
                try:
                    keywords = json.loads(job['keywords'])
                except:
                    pass
            
            resume_path = tailor_resume(
                job_description=job.get('description', ''),
                company=job['company'],
                role=job['title'],
                keywords=keywords
            )
            
            if resume_path and os.path.exists(resume_path):
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=open(resume_path, 'rb'),
                    filename=os.path.basename(resume_path),
                    caption=f"📄 *Resume for {job['company']}*",
                    parse_mode='Markdown'
                )
            else:
                await context.bot.send_message(chat_id=query.message.chat_id, text="❌ Resume failed. Add master_resume.docx to assets/")
        except Exception as e:
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Error: {str(e)}")
    
    elif action == "verify":
        await query.answer("Checking domain...")
        
        try:
            from utils.validator import check_domain_age
            result = check_domain_age(link)
            
            risk_emoji = {"SAFE": "✅", "TRUSTED": "💯", "LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴", "WARNING": "⚠️"}.get(result['risk_level'], "❓")
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"🕵️ *Domain Check*\n\nDomain: `{result['domain']}`\nAge: {result['age_days']} days\nRisk: {risk_emoji} {result['risk_level']}\n\n_{result['details']}_",
                parse_mode='Markdown'
            )
        except Exception as e:
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Error: {str(e)}")


# ============== SCAN COMMANDS ==============

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /scan command"""
    await update.message.reply_text("🔍 *Scanning LinkedIn + Reddit + Google...*", parse_mode='Markdown')
    context.application.create_task(run_scan(update.effective_chat.id, context, ["linkedin", "reddit", "google"]))


async def linkedin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /linkedin command"""
    await update.message.reply_text("💼 *Scanning LinkedIn (Last 1 Hour)...*", parse_mode='Markdown')
    context.application.create_task(run_scan(update.effective_chat.id, context, ["linkedin"]))


async def hackernews_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /hackernews command"""
    await update.message.reply_text("🟠 *Scanning HackerNews/YC Jobs...*", parse_mode='Markdown')
    context.application.create_task(run_scan(update.effective_chat.id, context, ["hackernews"]))


async def remote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /remote command"""
    await update.message.reply_text("🌍 *Scanning Remote Jobs...*", parse_mode='Markdown')
    context.application.create_task(run_scan(update.effective_chat.id, context, ["remote"]))


async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /all command - MEGA SCAN"""
    await update.message.reply_text(
        "🚀 *MEGA SCAN!*\n\nScanning: LinkedIn, Reddit, Google, HackerNews, RemoteOK, Arbeitnow, SimplyHired\n\n_2-3 minutes..._",
        parse_mode='Markdown'
    )
    context.application.create_task(run_scan(update.effective_chat.id, context, ["all"]))


async def run_scan(chat_id: int, context: ContextTypes.DEFAULT_TYPE, sources: list):
    """Universal scan function"""
    try:
        from utils.ai_brain import analyze_job
        from utils.validator import check_domain_age
        from database import add_job
        
        all_jobs = []
        source_counts = {}
        
        # LinkedIn
        if "linkedin" in sources or "all" in sources:
            try:
                from scrapers.linkedin_scraper import scan_linkedin
                jobs = scan_linkedin(time_filter="1hour", max_results=25)
                for j in jobs:
                    j['source'] = 'LinkedIn'
                all_jobs.extend(jobs)
                source_counts['LinkedIn'] = len(jobs)
            except Exception as e:
                print(f"LinkedIn: {e}")
        
        # Reddit
        if "reddit" in sources or "all" in sources:
            try:
                from scrapers.reddit_scraper import scan_reddit
                jobs = scan_reddit(posts_per_sub=10)
                all_jobs.extend(jobs)
                source_counts['Reddit'] = len(jobs)
            except Exception as e:
                print(f"Reddit: {e}")
        
        # Google
        if "google" in sources or "all" in sources:
            try:
                from scrapers.google_scraper import scan_google
                jobs = scan_google(results_per_dork=3)
                all_jobs.extend(jobs)
                source_counts['Google'] = len(jobs)
            except Exception as e:
                print(f"Google: {e}")
        
        # HackerNews
        if "hackernews" in sources or "all" in sources:
            try:
                from scrapers.additional_scrapers import scan_hackernews_jobs
                jobs = scan_hackernews_jobs()
                all_jobs.extend(jobs)
                source_counts['HackerNews'] = len(jobs)
            except Exception as e:
                print(f"HackerNews: {e}")
        
        # Remote
        if "remote" in sources or "all" in sources:
            try:
                from scrapers.additional_scrapers import scan_remoteok, scan_arbeitnow
                jobs1 = scan_remoteok()
                jobs2 = scan_arbeitnow()
                all_jobs.extend(jobs1)
                all_jobs.extend(jobs2)
                source_counts['RemoteOK'] = len(jobs1)
                source_counts['Arbeitnow'] = len(jobs2)
            except Exception as e:
                print(f"Remote: {e}")
        
        # SimplyHired (mega only)
        if "all" in sources:
            try:
                from scrapers.additional_scrapers import scan_simplyhired
                jobs = scan_simplyhired()
                all_jobs.extend(jobs)
                source_counts['SimplyHired'] = len(jobs)
            except Exception as e:
                print(f"SimplyHired: {e}")
        
        # Process jobs
        new_count = 0
        scam_count = 0
        
        for job in all_jobs:
            try:
                content = job.get('description') or job.get('title', '')
                analysis = analyze_job(content)
                
                link = job.get('link', '')
                domain_check = check_domain_age(link) if link else {'risk_level': 'UNKNOWN', 'age_days': -1}
                
                is_scam = analysis.get('is_scam', False) or domain_check.get('risk_level') in ['HIGH', 'SCAM']
                
                if is_scam:
                    scam_count += 1
                    continue
                
                job_record = {
                    'source': job.get('source', 'Unknown'),
                    'title': analysis.get('role') or job.get('title', 'Unknown'),
                    'company': analysis.get('company') or job.get('company', 'Unknown'),
                    'link': link,
                    'description': content[:2000],
                    'salary': analysis.get('salary', 'Not Mentioned'),
                    'hr_email': analysis.get('hr_email', ''),
                    'keywords': str(analysis.get('keywords', [])),
                    'is_scam': False,
                    'domain_age_days': domain_check.get('age_days', -1),
                    'legitimacy_score': analysis.get('legitimacy_score', 60),
                    'status': 'Pending'
                }
                
                if add_job(job_record):
                    new_count += 1
            except:
                continue
        
        # Summary
        summary = f"✅ *Scan Complete!*\n\n"
        for src, cnt in source_counts.items():
            summary += f"• {src}: {cnt}\n"
        summary += f"\n*New Added:* {new_count}\n*Scams Blocked:* {scam_count}\n\n/pending to view!"
        
        await context.bot.send_message(chat_id=chat_id, text=summary, parse_mode='Markdown')
        
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(e)}")


async def run_full_scan(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    await run_scan(chat_id, context, ["linkedin", "reddit", "google"])


# ============== BOT INIT ==============

def start_bot():
    """Start the Telegram bot"""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ No token!")
        return None
    
    print("🤖 Starting Telegram Bot...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("pending", pending_command))
    app.add_handler(CommandHandler("export", export_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(CommandHandler("linkedin", linkedin_command))
    app.add_handler(CommandHandler("hackernews", hackernews_command))
    app.add_handler(CommandHandler("remote", remote_command))
    app.add_handler(CommandHandler("all", all_command))
    # CSV management
    app.add_handler(CommandHandler("csv", csv_command))
    app.add_handler(CommandHandler("applied", applied_command))
    app.add_handler(CommandHandler("search", search_command))
    # Resume management
    app.add_handler(CommandHandler("resume", resume_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ Bot ready!")
    return app


async def set_bot_commands(app):
    """Set bot commands for popup menu when user types /"""
    commands = [
        BotCommand("start", "🚀 Start the bot"),
        BotCommand("all", "🔥 MEGA scan (all sources!)"),
        BotCommand("scan", "🔍 Scan LinkedIn+Reddit+Google"),
        BotCommand("linkedin", "💼 LinkedIn jobs (1 hour)"),
        BotCommand("hackernews", "🟠 YC/Startup jobs"),
        BotCommand("remote", "🌍 Remote jobs"),
        BotCommand("pending", "📋 View pending jobs"),
        BotCommand("applied", "✅ View applied jobs"),
        BotCommand("csv", "📄 CSV dashboard"),
        BotCommand("resume", "📝 ATS Resume (98%)"),
        BotCommand("search", "🔍 Search jobs"),
        BotCommand("stats", "📊 Statistics"),
        BotCommand("export", "📁 Export CSV file"),
        BotCommand("settings", "⚙️ View settings"),
        BotCommand("help", "ℹ️ Help & commands"),
    ]
    await app.bot.set_my_commands(commands)
    print("✅ Command menu registered!")


async def run_bot():
    app = start_bot()
    if app:
        # Set commands for popup menu
        await set_bot_commands(app)
        await app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(run_bot())


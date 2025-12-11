"""
Job Hunter - Main Entry Point
Runs the Telegram bot with scheduled background scans
"""
import sys
import os

# Initialize database first
from database import init_db, export_to_csv
from config import SCAN_INTERVAL_MINUTES, OUTPUT_DIR, ASSETS_DIR
from config import GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, GMAIL_EMAIL, REDDIT_CLIENT_ID


def main():
    """Main entry point"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🚀 GOD-MODE JOB HUNTER v1.0                                ║
║                                                               ║
║   Your AI-powered job hunting assistant                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize database
    print("📦 Initializing database...")
    init_db()
    
    # Ensure directories exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    # Check configuration
    print("\n⚙️ Checking configuration...")
    
    config_status = {
        "Gemini API": "✅" if GEMINI_API_KEY else "❌",
        "Telegram Bot": "✅" if TELEGRAM_BOT_TOKEN else "❌",
        "Gmail": "✅" if GMAIL_EMAIL else "⚠️ Optional",
        "Reddit API": "✅" if REDDIT_CLIENT_ID else "⚠️ Optional"
    }
    
    for key, status in config_status.items():
        print(f"   {status} {key}")
    
    if not TELEGRAM_BOT_TOKEN:
        print("\n❌ Telegram Bot Token is required!")
        print("   Add TELEGRAM_BOT_TOKEN to your .env file")
        return
    
    # Import and start bot
    print("\n🤖 Starting Telegram Bot...")
    from bot.telegram_bot import start_bot
    
    app = start_bot()
    
    if not app:
        print("❌ Failed to start bot")
        return
    
    print("\n" + "="*60)
    print("✅ Job Hunter is LIVE!")
    print("="*60)
    print(f"\n📱 Open Telegram and message your bot: @JobHunter7_bot")
    print("   Send /start to begin\n")
    print("   Press Ctrl+C to stop\n")
    
    # Run bot polling (this handles its own event loop)
    try:
        app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Job Hunter...")
        print("✅ Goodbye!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user")
        sys.exit(0)

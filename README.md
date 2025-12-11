# 🚀 God-Mode Job Hunter Bot

An AI-powered Telegram bot designed to automate your job search, tailored specifically for your profile. It integrates with job platforms, filters listings using AI, and helps manage your application process seamlessly.

## ✨ Features

- **🤖 AI-Powered Filtering**: Uses Google Gemini to analyze job descriptions against your resume and preferences.
- **📱 Telegram Interface**: Control everything from a Telegram bot found at `@JobHunter7_bot` (or your own instance).
- **🔄 Automated Scanning**: Periodically scans for new jobs (interval configurable).
- **📂 Resume Tailoring**: (Implied Feature) Can generate tailored content based on your master resume.
- **🔔 Real-time Alerts**: Get notified immediately when a high-match job is found.

## 🛠️ Prerequisites

- **Python 3.8+**
- **Telegram Bot Token**: Get one from [@BotFather](https://t.me/BotFather).
- **Gemini API Key**: Get one from Google AI Studio.
- **Gmail Account (Optional)**: For email-based job alerts parsing.
- **Reddit API (Optional)**: For finding jobs on subreddits.

## 🚀 Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/YourUsername/job-hunter-bot.git
    cd job-hunter-bot
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configuration**:

    *   Create a `.env` file in the root directory:
        ```ini
        GEMINI_API_KEY=your_gemini_api_key
        TELEGRAM_BOT_TOKEN=your_telegram_bot_token
        TELEGRAM_CHAT_ID=your_chat_id
        
        # Optional
        GMAIL_EMAIL=your_email@gmail.com
        GMAIL_APP_PASSWORD=your_app_password
        REDDIT_CLIENT_ID=your_reddit_id
        REDDIT_CLIENT_SECRET=your_reddit_secret
        SCAN_INTERVAL_MINUTES=60
        ```

    *   **CRITICAL: Set up your Profile**
        The bot needs your professional details to function. Create a file named `assets/profile.json`. 
        
        **Copy and paste the structure below into `assets/profile.json` and fill in your details:**

        ```json
        {
          "identity": {
            "full_name": "Your Name",
            "title": "Your Job Title",
            "email": "your.email@example.com",
            "phone": "+1 234 567 8900",
            "location": "City, Country",
            "linkedin": "linkedin.com/in/yourprofile",
            "github": "github.com/yourusername",
            "portfolio": "yourportfolio.com"
          },
          "summary": "Your professional summary...",
          "skills": {
            "languages": ["Python", "JavaScript"],
            "frontend": ["React", "HTML/CSS"],
            "backend": ["Node.js", "FastAPI"],
            "ai_ml": ["TensorFlow", "LangChain"],
            "databases": ["PostgreSQL", "MongoDB"],
            "tools": ["Git", "Docker"]
          },
          "experience": [
            {
              "company": "Company Name",
              "role": "Role Title",
              "duration": "Start - End",
              "location": "Remote/City",
              "achievements": [
                "Achievement 1",
                "Achievement 2"
              ]
            }
          ],
          "projects": [
            {
              "name": "Project Name",
              "tech": "Tech Stack",
              "highlights": ["Highlight 1", "Highlight 2"]
            }
          ],
          "education": {
            "degree": "Degree Name",
            "institution": "University Name",
            "year": "2024"
          },
          "certifications": ["Cert 1", "Cert 2"],
          "achievements": ["Achievement 1"],
          "ats_keywords": ["Keyword1", "Keyword2"]
        }
        ```

5.  **Add your Resume**:
    Place your master resume in `assets/master_resume.docx`.

## 🏃 Run the Bot

```bash
python main.py
```

The bot will start, initialize the database, and begin listening for Telegram commands.

## 📝 Usage

- `/start`: Check if the bot is alive.
- (Add other commands here as you develop them)

## 🛡️ License

MIT

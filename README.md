🧠 Memory-Enhanced Email Agent
An AI-Powered Email Assistant With Long-Term Memory & Autonomous Drafting
<div align="center">








A smart email assistant that learns your preferences, understands context, and drafts intelligent replies using AI and memory-augmented reasoning.

Features
 • Installation
 • Setup
 • Usage
 • Tech Overview

</div>
🌟 Features
🤖 AI Email Classification

Automatically filters newsletters, promotions, system notifications, job alerts, etc.

Learns from your behavior using LangMem (memory-augmented embeddings)

Prioritizes personal and work emails for response

✉️ Context-Aware Reply Generation

Reads the entire conversation history (incoming & sent emails)

Generates concise, contextually accurate drafts

Saves drafts directly to Gmail (never auto-sends)

⚡ Real-Time Live Mode

Checks inbox every 60 seconds

Uses timestamp-based checkpointing

Early-stop scanning for high efficiency

Processes new emails within seconds

🧠 Long-Term Memory

Embeddings stored via LangMem InMemoryStore

HuggingFace transformer model: all-mpnet-base-v2

Semantic search improves email understanding over time

🔒 Security Focused

Local OAuth 2.0 Gmail authentication

.env-based API key handling

Credentials never uploaded to the cloud

📋 Prerequisites

Python 3.12+ or 3.13+

Gmail Account

Google Cloud Project (for Gmail API)

Groq API Key (LLM inference)

🚀 Installation
1. Clone the Repository
git clone https://github.com/poojanpadhiyar/Memory-Enhanced-Email-Agent.git
cd Memory-Enhanced-Email-Agent

2. Create a Virtual Environment
python -m venv myenv


Activate:

Windows PowerShell:

.\myenv\Scripts\Activate.ps1


Mac/Linux:

source myenv/bin/activate

3. Install Dependencies
pip install -r requirements.txt

🔧 Setup
✅ Step 1 — Get Gmail API Credentials

Open Google Cloud Console

Create a new project

Enable Gmail API

Configure OAuth consent screen

Add yourself as a test user

Create Desktop App OAuth Client

Download the JSON and rename to:

credentials.json


Place it in your project root.

✅ Step 2 — Understand token.json

Auto-generated on first run

Stores your OAuth tokens

Required for accessing Gmail without repeated login

Never commit it to GitHub

✅ Step 3 — Get Your Groq API Key

Go to: https://console.groq.com

Create API Key

Copy it

✅ Step 4 — Create .env File

Create a .env file:

GROQ_API_KEY=your_groq_key_here

🎯 Usage
▶️ First Run (Authentication)
python email_agent.py


What happens:

Browser opens

You log in to Gmail

Grant permissions

token.json is created

Agent processes last 5 unread emails

▶️ Live Monitoring Mode

Runs automatically after first run:

Checks inbox every 60 seconds

Classifies new emails

Generates drafts for priority emails

Press CTRL + C to stop

📖 How It Works
1️⃣ Timestamp-Based Email Detection

Fast early-stop scanning:

if internal_date <= self.last_check_time:
    break

2️⃣ AI Classification

Learns what to ignore VS what to reply to.

Filters out:

LinkedIn alerts

Promotional emails

System notifications

Transactional mails

3️⃣ Conversation History Analysis

Bidirectional search:

query = f"({sender_email})"


Reads last 20 emails (incoming + sent) for deep context.

4️⃣ LLM-Based Draft Generation

Uses Groq LLM (Llama/GPT-OSS models) to draft replies.

Results:

Short

Professional

Context-aware

5️⃣ Memory Learning

Adds patterns to LangMem store automatically.

📂 Project Structure
Memory-Enhanced-Email-Agent/
├── email_agent.py  
├── credentials.json     # (User-provided, ignored from Git)
├── token.json           # Auto-generated
├── .env                 # API keys
├── .gitignore
├── requirements.txt
└── README.md

🔐 Security Best Practices

Files never to commit:

.env

credentials.json

token.json

Virtual environment folders

Logs

Already covered in .gitignore.

🛠️ Troubleshooting
❗ "Google hasn't verified this app"

Normal for testing mode.
Click:

Advanced → Go to app (unsafe)

❗ "Access blocked"

You forgot to add yourself as a test user.

❗ Invalid credentials

Delete token.json and re-run.

🤝 Contributing

Fork

Create feature branch

Commit changes

Open Pull Request

Contributions welcome!

📄 License

Apache License 2.0
See LICENSE for details.

🙏 Acknowledgments

LangChain

LangGraph

LangMem

Gmail API

Groq

HuggingFace

<div align="center">

Made with ❤️ by Poojan Padhiyar

⭐ Feel free to star the repo if you find it useful!

</div>
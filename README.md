# 🧠 Memory-Enhanced Email Agent# Memory-Enhanced-Email-Agent

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-Powered-green.svg)
![Gmail API](https://img.shields.io/badge/Gmail-API-red.svg)
![License](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)

**An intelligent email assistant that learns your preferences and automatically drafts replies using AI and memory-augmented learning.**

[Features](#-features) • [Installation](#-installation) • [Setup](#-setup) • [Usage](#-usage) • [How It Works](#-how-it-works)

</div>

---

## 🌟 Features

### 🤖 **AI-Powered Email Classification**
- Automatically identifies which emails to ignore (promotions, spam, newsletters)
- Learns from your patterns using **LangMem** memory tools
- Smart categorization: personal emails get responses, junk gets ignored

### ✉️ **Intelligent Draft Generation**
- Creates contextual email replies based on conversation history
- Analyzes **both incoming AND sent emails** for full context
- Drafts saved directly to Gmail for your review before sending

### ⚡ **Lightning-Fast Live Mode**
- Real-time email monitoring with 60-second check intervals
- **Timestamp-based checkpoint system** with early-stop optimization
- Stops scanning immediately when reaching previously processed emails
- Typically processes new emails in under 5 seconds

### 🧠 **Memory-Augmented Learning**
- Uses **LangMem InMemoryStore** with HuggingFace embeddings
- Remembers email patterns and improves over time
- Semantic search with `sentence-transformers/all-mpnet-base-v2`

### 🔒 **Secure & Private**
- OAuth 2.0 authentication with Gmail API
- Credentials stored locally - never shared
- Full control over what emails are processed

---

## 📋 Prerequisites

- **Python 3.13+**
- **Gmail Account**
- **Google Cloud Project** (for Gmail API access)
- **Groq API Key** (for LLM)

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/poojanpadhiyar/Memory-Enhanced-Email-Agent.git
cd Memory-Enhanced-Email-Agent
```

### 2. Create Virtual Environment
```bash
python -m venv myenv
```

**Activate the environment:**
- **Windows (PowerShell):**
  ```powershell
  .\myenv\Scripts\Activate.ps1
  ```
- **Windows (CMD):**
  ```cmd
  myenv\Scripts\activate.bat
  ```
- **macOS/Linux:**
  ```bash
  source myenv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔧 Setup

### Step 1: Get Gmail API Credentials

#### 1.1 Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Create Project"**
3. Name it (e.g., "Email Agent") and click **Create**

#### 1.2 Enable Gmail API
1. In your project, go to **APIs & Services** > **Library**
2. Search for **"Gmail API"**
3. Click on it and press **Enable**

#### 1.3 Create OAuth 2.0 Credentials
1. Go to **APIs & Services** > **Credentials**
2. Click **"+ CREATE CREDENTIALS"** > **OAuth client ID**
3. If prompted, configure the **OAuth consent screen**:
   - Choose **External** (if not a workspace user)
   - Fill in:
     - App name: `Email Agent`
     - User support email: Your email
     - Developer contact: Your email
   - Click **Save and Continue**
   - **Scopes**: Skip this step (click **Save and Continue**)
   - **Test users**: Click **"+ ADD USERS"** and add your Gmail address
     - ⚠️ **IMPORTANT**: Only test users can use the app while it's in testing mode
     - You must add your own email address here to authenticate
   - Click **Save and Continue** > **Back to Dashboard**

4. Back in **Credentials** > **Create OAuth client ID**:
   - Application type: **Desktop app**
   - Name: `Email Agent Client`
   - Click **Create**

5. **Download the credentials**:
   - Click the **Download** button (⬇️) next to your OAuth 2.0 Client ID
   - Save the file as **`credentials.json`**
   - Move `credentials.json` to your project root directory

#### 📝 What is `credentials.json`?
This file contains:
- **Client ID**: Identifies your application
- **Client Secret**: Secret key for OAuth authentication
- **Redirect URIs**: Where Google sends authentication responses

**🔒 Security Note**: Never commit `credentials.json` to GitHub! It's already in `.gitignore`.

---

### Step 2: Understanding `token.json`

**What is `token.json`?**
- Generated **automatically** on first run
- Contains your **access token** and **refresh token**
- Stores your authenticated session with Gmail
- Allows the app to access Gmail without repeated login prompts

**When is it created?**
- First time you run `python email_agent.py`
- A browser window opens asking you to log in and grant permissions
- After authorization, `token.json` is saved locally

**🔒 Security Note**: `token.json` contains sensitive access tokens. Never share it or commit to Git!

---

### Step 3: Get Groq API Key

1. Go to [Groq Console](https://console.groq.com/)
2. Sign up or log in
3. Navigate to **API Keys**
4. Click **Create API Key**
5. Copy the key

---

### Step 4: Create `.env` File

Create a file named `.env` in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Replace `your_groq_api_key_here` with your actual Groq API key.

---

## 🎯 Usage

### First Run (Authentication)

```bash
python email_agent.py
```

**What happens:**
1. Browser opens asking you to sign in to Gmail
2. You'll see a warning: **"Google hasn't verified this app"**
   - Click **"Advanced"** > **"Go to Email Agent (unsafe)"**
   - This is normal for testing mode - your app is safe!
3. Grant permissions to read, compose, and send emails
4. `token.json` is created automatically
5. Agent processes last 5 unread emails

### Live Mode (Continuous Monitoring)

After first run, the agent enters **Live Mode**:
- Checks for new emails every **60 seconds**
- Uses **timestamp-based checkpointing** with early-stop optimization
- Automatically classifies and drafts replies
- Press **Ctrl+C** to stop

---

## 📖 How It Works

### 1. **Email Detection**
```python
# Timestamp-based checkpoint with early-stop
if internal_date <= self.last_check_time:
    break  # Stop immediately when hitting old emails
```
- **First Run**: Processes last 5 unread emails, sets checkpoint to newest timestamp
- **Live Mode**: Fetches unread emails, filters by timestamp
- **Early Stop**: Stops scanning when it hits an email older than checkpoint
- Gmail returns emails newest-first, so this is very fast!

### 2. **AI Classification**
```python
classify_email(email) → "process" or "ignore"
```
- Uses **LangMem memory tools** to learn patterns
- Automatically ignores:
  - Gaming promotions (Steam, Epic Games, etc.)
  - LinkedIn job alerts
  - System notifications
  - Newsletters
- Processes personal/work emails for drafting

### 3. **Conversation History**
```python
# Bidirectional search (incoming + sent)
query = f'({sender_email})'
```
- Searches **ALL emails** with the sender (not just from them)
- Includes your previous replies for full context
- Last 20 emails analyzed for conversation flow

### 4. **Draft Generation**
```python
generate_response_with_context(email, history)
```
- Uses **ChatGroq** (openai/gpt-oss-120b model)
- Considers conversation history
- Creates professional, contextual replies
- Saves as Gmail draft (not sent automatically)

### 5. **Memory Learning**
```python
# Memory tools integrated
create_manage_memory_tool()
create_search_memory_tool()
```
- InMemoryStore with HuggingFace embeddings
- 768-dimension vectors for semantic search
- Agent learns email patterns over time

---

## 🧪 Test Users

### Why Test Users?

When your app is in **Testing** mode (not published), only **test users** can authenticate:
- You must add email addresses in Google Cloud Console
- Maximum 100 test users allowed
- Required until you verify and publish the app

### How to Add Test Users

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. **APIs & Services** > **OAuth consent screen**
4. Scroll to **Test users** section
5. Click **"+ ADD USERS"**
6. Enter email addresses (one per line)
7. Click **Save**

### Who Should Be a Test User?
- **Yourself** (your Gmail account using the agent)
- Team members testing the agent
- Anyone who needs to run the application

⚠️ **Without adding test users, authentication will fail with "Access blocked" error!**

---

## 📂 Project Structure

```
Memory-Enhanced-Email-Agent/
├── email_agent.py          # Main agent script
├── credentials.json        # Gmail API credentials (you create)
├── token.json             # Auto-generated auth token
├── .env                   # API keys
├── .gitignore            # Protects sensitive files
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

---

## 🔐 Security Best Practices

### Files to NEVER Commit:
- ✅ Already in `.gitignore`:
  - `credentials.json` - OAuth client secrets
  - `token.json` - Access/refresh tokens
  - `.env` - API keys
  - `myenv/` - Virtual environment

### Sharing Your Code:
1. **Fork/Clone**: Others can use your code structure
2. **Credentials**: Each user creates their own `credentials.json`
3. **API Keys**: Each user gets their own Groq API key
4. **Test Users**: Add collaborators in Google Cloud Console

---

## 🛠️ Troubleshooting

### "Google hasn't verified this app"
- **Normal** for testing mode
- Click **Advanced** > **Go to [App Name] (unsafe)**
- Your app is safe - Google shows this for all testing apps

### "Access blocked: This app's request is invalid"
- You're not added as a **test user**
- Go to OAuth consent screen > Add your email to test users

### "Error: invalid_grant"
- Delete `token.json`
- Run the agent again to re-authenticate

### Agent Processes Old Emails After Restart
- **First run** processes last 5 unread emails and sets checkpoint
- All older emails are automatically ignored in subsequent checks
- If you have many old unread emails, mark them as read before first run

### Slow Email Detection
- Agent uses timestamp-based filtering with early-stop optimization
- Should detect new emails in under 5 seconds
- Check that `self.last_check_time` is being updated

### No Conversation History
- Verify bidirectional search: `query = f'({sender_email})'`
- Check that sent emails are included in results
- Last 20 emails (both directions) should be analyzed

---

## 🎨 Example Output

```
==================================================
SMART EMAIL AGENT - LIVE MODE
==================================================
🔴 Live monitoring enabled!
🧠 Learning email patterns automatically
⏱️ Checking every 60 seconds...

FIRST RUN: Getting last 5 unread emails...
Checkpoint set: 1760256746000

Processing 5 NEW emails...
[... processes 5 emails ...]

Checkpoint updated: 1760256746000
⏳ Waiting 60 seconds...

==================================================
CHECKING NEW EMAILS...
==================================================

LIVE MODE: Checking for new arrivals...
Checkpoint: 1760256746000
Scanning 20 unread emails...
Reached checkpoint at email 2/20  ← Early stop!
Found 1 new emails

Processing 1 NEW emails...

──────────────────────────────────────────────────
EMAIL 1/1
──────────────────────────────────────────────────

1. Fetching email...
  From: colleague@company.com
  Subject: Project Update
2. Classifying email...
  Classification: process
3. Getting conversation history...
  🔍 Getting FULL conversation history with colleague@company.com...
  ✓ Found 8 emails (incoming + sent)
4. Generating response...
  🤖 Generating response (considering 8 past emails)...
5. Creating draft...
  ✉️ Creating draft...
  ✓ Draft created in Gmail!

EMAIL 1 PROCESSED!

Checkpoint updated: 1760256850000
⏳ Waiting 60 seconds...
```

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **Apache 2.0 License**.  
See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LangChain** - AI framework
- **LangGraph** - Agent orchestration
- **LangMem** - Memory management
- **Groq** - Fast LLM inference
- **Gmail API** - Email access
- **HuggingFace** - Embeddings

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/poojanpadhiyar/Memory-Enhanced-Email-Agent/issues)
- **Email**: poojan_pp@mt.iitr.ac.in

---

<div align="center">

**Made with ❤️ by [PoojanPadhiyar](https://github.com/poojanpadhiyar)**

⭐ Star this repo if you find it useful!

</div>

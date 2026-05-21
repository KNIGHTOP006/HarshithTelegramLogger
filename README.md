# 🏋️ Fitness AI Tracker – Telegram Bot

A fully free, AI-powered Telegram bot that tracks your calories, macros, weight,
and progress photos — all stored in Google Sheets as your database.

---

## ✨ Features

| Feature | How it works |
|---|---|
| 🍽 Text food logging | Type your meal → AI estimates nutrition |
| 🎤 Voice food logging | Send a voice note → Whisper transcribes → AI estimates |
| ⚖️ Weight tracking | `/weight 82.4` → logged to Sheets |
| 📸 Progress photos | Send photo with `/photo` → uploaded to Drive |
| 📊 Daily summary | `/today` → calories, macros, remaining |
| 📅 Weekly summary | `/week` → avg calories, consistency %, weekly trasformation video |
| 🗓 Monthly summary | `/month` → weight change, highest/lowest day , monthly trasformation video |
| 🏆 Yearly summary | `/year` → streaks, best month, total stats, yearly trasformation video|
| 🔥 Streak system | Tracks consecutive days of logging |
| 🎯 Calorie goals | `/goal 1800` → remaining shown in `/today` |

---

## 🏗 Project Structure

```
fitness-bot/
│
├── bot.py          # Main bot – all Telegram handlers
├── config.py       # Environment variable loading
├── ai.py           # Gemini API calorie estimation (Layer 2)
├── speech.py       # Whisper voice transcription
├── sheets.py       # All Google Sheets read/write
├── drive.py        # Google Drive photo uploads
├── analytics.py    # Summary calculations (/today, /week, etc.)
├── streaks.py      # Streak tracking logic
├── food_db.py      # Local food database (Layer 1)
├── utils.py        # Shared helpers & message formatters
│
├── requirements.txt
├── .env.example    # Template for environment variables
├── .gitignore
├── credentials.json  ← You create this (NOT committed to git)
└── README.md
```

---

## 🚀 Quick Setup (Local)

### Step 1: Clone & Install

```bash
git clone https://github.com/yourusername/fitness-bot.git
cd fitness-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows

# Install Python packages
pip install -r requirements.txt

# Install PyTorch (CPU-only – lighter, works everywhere)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install ffmpeg (required by Whisper for audio processing)
# Ubuntu/Debian:
sudo apt install ffmpeg
# macOS:
brew install ffmpeg
```

---

### Step 2: Get a Telegram Bot Token

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name: `Fitness AI Tracker`
4. Choose a username: `myfitness_ai_bot` (must end in `bot`)
5. Copy the token BotFather gives you

---

### Step 3: Get a Gemini API Key (Free)

1. Go to https://aistudio.google.com/app/apikey
2. Click **Create API Key**
3. Copy the key

The free tier allows ~1,500 requests/day — more than enough for personal use.

---

### Step 4: Set Up Google Cloud Project

#### 4a. Create a Project

1. Go to https://console.cloud.google.com/
2. Click the project dropdown → **New Project**
3. Name it: `fitness-bot`

#### 4b. Enable APIs

In the Google Cloud Console, go to **APIs & Services → Library** and enable:
- ✅ **Google Sheets API**
- ✅ **Google Drive API**

#### 4c. Create a Service Account

1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → Service Account**
3. Name it: `fitness-bot-service`
4. Click **Done** (skip optional steps)
5. Click on the service account you just created
6. Go to **Keys** tab → **Add Key → Create New Key → JSON**
7. Download the file → rename it to **`credentials.json`**
8. Place `credentials.json` in your `fitness-bot/` folder

#### 4d. Create a Google Sheet

1. Go to https://sheets.google.com → create a new blank spreadsheet
2. Name it: `Fitness Tracker`
3. Copy the Sheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/  →COPY_THIS←  /edit
   ```
4. Share the sheet with your service account email:
   - Open the Sheet → Share
   - Paste the service account email (looks like `fitness-bot-service@fitness-bot-xxxxx.iam.gserviceaccount.com`)
   - Give **Editor** access

#### 4e. Create a Google Drive Folder (for photos)

1. Go to https://drive.google.com → create a new folder
2. Name it: `Fitness Progress Photos`
3. Share the folder with the same service account email (Editor access)
4. Copy the folder ID from the URL:
   ```
   https://drive.google.com/drive/folders/  →COPY_THIS←
   ```

---

### Step 5: Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in all values:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABC-your-token-here
GEMINI_API_KEY=AIzaSy-your-gemini-key-here
GOOGLE_SHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_DRIVE_FOLDER_ID=1abc2def3ghi4jkl
WHISPER_MODEL_SIZE=base
DEFAULT_CALORIE_GOAL=2000
TEMP_DIR=/tmp/fitness_bot
```

---

### Step 6: Run the Bot

```bash
python bot.py
```

You should see:
```
Setting up Google Sheets…
Google Sheets ready.
🤖 Fitness AI Tracker bot is running…
```

Open Telegram, find your bot, send `/start` — you're live! 🎉

---

## 📱 Commands Reference

| Command | Description | Example |
|---|---|---|
| `/start` | Welcome message | `/start` |
| `/help` | List all commands | `/help` |
| *(just type)* | Log food by text | `3 eggs and 2 dosa` |
| `/log` | Log food (alternative) | `/log grilled chicken and rice` |
| `/weight` | Log body weight | `/weight 82.4` |
| `/photo` | Save progress photo | Send a photo with this caption |
| `/today` | Today's summary | `/today` |
| `/week` | 7-day summary | `/week` |
| `/month` | Monthly summary | `/month` |
| `/year` | Yearly summary | `/year` |
| `/streak` | View streak | `/streak` |
| `/goal` | Set/view calorie goal | `/goal 1800` |

---

## 🤖 How the AI Works

### Two-Layer Food Estimation

```
User: "3 eggs and 2 dosa and sugarcane juice"
         │                         │
         ▼                         ▼
   Layer 1: Local DB         Layer 2: Gemini
   (instant, free)           (API call, only for unknowns)
   ─────────────────         ─────────────────────────────
   3 eggs → known ✓          sugarcane juice → ask Gemini
   2 dosa → known ✓          ← returns JSON with nutrition
         │                         │
         └──────────┬──────────────┘
                    ▼
              Sum totals
              Log to Sheets
              Respond to user
```

This design minimises Gemini API calls for common Indian foods.

---

## ☁️ Deployment

### Option A: Railway (Recommended – Free Tier)

1. Push your code to GitHub (don't commit `.env` or `credentials.json`)
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Select your repo
4. Go to **Variables** and add all your `.env` variables one by one
5. Add `credentials.json` content as a variable:
   - Add `GOOGLE_CREDENTIALS_JSON` = *(paste the entire JSON content)*
   - Then modify `config.py` to write this to a file at startup (see note below)
6. Set the start command: `python bot.py`

**Handling credentials.json on Railway:**

Add this to the top of `bot.py`'s `main()` function:
```python
import json, os
creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
if creds_json:
    with open("credentials.json", "w") as f:
        json.dump(json.loads(creds_json), f)
```

---

### Option B: Render (Free Tier)

1. Push to GitHub
2. Go to https://render.com → New → Background Worker
3. Connect your GitHub repo
4. Set the start command: `python bot.py`
5. Add environment variables in the Render dashboard
6. Use the same `GOOGLE_CREDENTIALS_JSON` trick as Railway

---

### Option C: Local / VPS (Simplest)

On a Linux VPS (DigitalOcean, Hetzner, etc.):

```bash
# Keep bot running after logout using screen or nohup
screen -S fitness-bot
python bot.py
# Ctrl+A then D to detach

# Or use nohup:
nohup python bot.py > bot.log 2>&1 &
```

For production VPS use, consider setting up a **systemd service**:

```ini
# /etc/systemd/system/fitness-bot.service
[Unit]
Description=Fitness AI Tracker Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/fitness-bot
ExecStart=/home/ubuntu/fitness-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable fitness-bot
sudo systemctl start fitness-bot
sudo systemctl status fitness-bot
```

---

## 💡 Architecture Notes

### Why Google Sheets as a database?
- **Free forever** (no database hosting costs)
- **Visual** – you can see and edit your data directly
- **Simple** – no SQL, no migrations
- Scales easily to years of personal data

### Why local Whisper instead of cloud STT?
- **Zero cost** – runs on your CPU
- **Privacy** – audio never leaves your server
- Supports Indian English, Hindi, Tamil, and 90+ languages automatically

### Why Gemini instead of GPT-4?
- **Free tier** is generous (1,500 requests/day)
- Flash model is very fast for structured JSON responses
- The two-layer system means most users rarely hit Gemini anyway

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| `TELEGRAM_BOT_TOKEN not set` | Check your `.env` file exists and is filled |
| `Worksheet not found` | Run `sheets.setup_sheets()` once, or restart bot |
| `credentials.json not found` | Download from GCP and place in project root |
| `ffmpeg not found` | Install with `sudo apt install ffmpeg` |
| Whisper takes too long | Switch to `WHISPER_MODEL_SIZE=tiny` in `.env` |
| Gemini returns invalid JSON | Usually a network error – try again |
| Photos not uploading | Check Drive folder ID and service account permissions |

---

## 🔐 Security Notes

- **Never** commit `.env` or `credentials.json` to git
- The `.gitignore` file already excludes them
- On Railway/Render, use environment variables for all secrets
- The service account only has access to your specific Sheet and Drive folder

---

## 📈 Future Improvements

- [ ] Barcode scanner integration
- [ ] Meal photo analysis (Gemini Vision)
- [ ] Weekly PDF report export
- [ ] Multi-user support with per-user Sheets
- [ ] Water intake tracking
- [ ] Exercise logging
- [ ] BMI and TDEE calculator

---

## 📄 License

MIT – use freely for personal and commercial projects.

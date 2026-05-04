# Zoom → Google Calendar → Notion Sync

Automatically syncs your Zoom meetings from Google Calendar into Notion,
then enriches each entry after the call with transcript, recording link,
attendees, and duration.

---

## How It Works

```
Google Calendar ──► finds Zoom meetings ──► saves to Notion (Scheduled)
                                                      │
Zoom API ────────► after call: recording + ──► updates Notion (Completed)
                   transcript + participants
```

---

## Project Structure

```
zoom_notion_sync/
├── main.py                   # Entry point
├── requirements.txt
├── .env.example              # Copy to .env and fill in
├── NOTION_SETUP.md           # Step-by-step Notion DB creation
├── config/
│   └── settings.py           # Loads .env variables
├── services/
│   ├── calendar_service.py   # Google Calendar OAuth + Zoom link extraction
│   ├── zoom_service.py       # Zoom API: recordings, transcripts, participants
│   └── notion_service.py     # Notion API: create/update meeting pages
└── utils/
    └── logger.py             # Console + file logging
```

---

## Setup (One-Time)

### 1. Install Python dependencies

```bash
cd zoom_notion_sync
pip install -r requirements.txt
```

### 2. Set up Google Calendar API

1. Go to https://console.cloud.google.com
2. Create a project (or select an existing one)
3. Enable **Google Calendar API**
4. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**
5. App type: **Desktop app**
6. Download the JSON → save it as `credentials.json` in this folder
7. On first run, a browser window opens for you to authorize access

### 3. Set up Zoom Server-to-Server OAuth App

1. Go to https://marketplace.zoom.us → **Develop → Build App**
2. Choose **Server-to-Server OAuth**
3. Name it `zoom-sync` → Create
4. Under **Scopes**, add:
   - `meeting:read:admin`
   - `recording:read:admin`
   - `report:read:admin`
5. Copy **Account ID**, **Client ID**, **Client Secret**

### 4. Set up Notion

Follow the detailed guide in **NOTION_SETUP.md**.

### 5. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in all values.

---

## Running the App

```bash
# Sync upcoming Zoom meetings from Google Calendar → Notion
python main.py --sync

# Process completed calls (fetch recordings, transcripts, participants)
python main.py --post-call

# Do both at once (recommended for daily use)
python main.py --all
```

### Automate with a daily schedule (optional)

**Mac/Linux — cron:**
```bash
crontab -e
# Add this line to run every morning at 8am:
0 8 * * * cd /path/to/zoom_notion_sync && python main.py --all
```

**Windows — Task Scheduler:**
- Program: `python`
- Arguments: `main.py --all`
- Start in: `C:\path\to\zoom_notion_sync`

---

## What Gets Saved to Notion

| Field            | Source            | When         |
|------------------|-------------------|--------------|
| Meeting Title    | Google Calendar   | On sync      |
| Zoom Meeting ID  | Calendar event    | On sync      |
| Start/End Time   | Calendar event    | On sync      |
| Duration         | Calendar event    | On sync      |
| Join URL         | Calendar event    | On sync      |
| Attendees        | Zoom API          | Post-call    |
| Recording URL    | Zoom API          | Post-call    |
| Transcript       | Zoom API          | Post-call    |
| Status           | App logic         | Both         |

---

## Logs

Daily log files are saved to `logs/sync_YYYYMMDD.log`.

---

## Notes

- Zoom transcripts require **Cloud Recording** + **Audio Transcript** enabled in your Zoom account settings
- Zoom keeps recordings for 30 days by default
- The app never deletes Notion pages — it only creates and updates

# Create Your Notion Database

Follow these steps to create the Notion database that this app will sync into.

---

## Step 1 — Create a New Page in Notion

1. Open Notion → click **"+ New page"** in the sidebar
2. Give it a title, e.g. **"Zoom Call Tracker"**
3. Type `/database` → choose **"Table - Full page"**

---

## Step 2 — Add These Properties (Columns)

Delete the default columns and create these exact ones:

| Property Name       | Type        | Notes                          |
|---------------------|-------------|--------------------------------|
| Meeting Title       | **Title**   | (rename the default "Name")    |
| Zoom Meeting ID     | Text        |                                |
| Status              | Select      | Options: Scheduled, Completed  |
| Start Time          | Date        | Enable end date too            |
| Duration (min)      | Number      |                                |
| Join URL            | URL         |                                |
| Recording URL       | URL         |                                |
| Organizer           | Email       |                                |
| Attendees           | Text        |                                |
| Transcript          | Text        |                                |
| Notes               | Text        |                                |
| Google Event ID     | Text        |                                |

---

## Step 3 — Create a Notion Integration

1. Go to → https://www.notion.so/my-integrations
2. Click **"+ New integration"**
3. Name it `zoom-sync` → select your workspace → Save
4. Copy the **"Internal Integration Secret"** — this is your `NOTION_TOKEN`

---

## Step 4 — Connect Integration to Your Database

1. Open your new database page in Notion
2. Click **"..."** (top right) → **"Connections"** → **"Connect to"**
3. Search for `zoom-sync` → click **Connect**

---

## Step 5 — Get Your Database ID

Your database URL looks like:
```
https://www.notion.so/your-workspace/abc123def456...?v=...
```
The long ID between the last `/` and `?v=` is your `NOTION_DATABASE_ID`.

Example:
```
https://notion.so/myworkspace/1a2b3c4d5e6f7890abcd1234567890ef?v=xyz
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                               This part is your NOTION_DATABASE_ID
```

---

## Done!

Paste both values into your `.env` file:
```
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=1a2b3c4d5e6f7890abcd1234567890ef
```

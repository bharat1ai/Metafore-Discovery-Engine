# Metafore Works — Discovery Engine
## Setup Guide for New Machine

> Give this file to Claude Code (the AI assistant in your terminal). It will do everything for you.
> You only need to do **two things** manually — they are marked **[YOU DO THIS]** below.

---

## Step 1 — Unzip the package

**[YOU DO THIS]**

Place this unzipped folder anywhere inside your root working folder.

**On Windows:**
```
MWorks\
  Metafore Discovery Engine\
    START.bat
    STOP.bat
    ...
```

**On Mac:**
```
MWorks/
  Metafore Discovery Engine/
    START.command
    STOP.command
    ...
```

---

## Step 2 — Let Claude Code set up the app

Open Claude Code inside the **`Metafore Discovery Engine`** folder and paste this message:

**On Windows:**
```
I have just unzipped the Metafore Discovery Engine into this folder.
The API key is already configured in discovery-engine/.env.
Please set up the app completely:
1. Install all Python packages from discovery-engine/backend/requirements.txt
2. Verify the server starts correctly on port 8083
3. Tell me when it is ready
```

**On Mac — paste this instead:**
```
I have just unzipped the Metafore Discovery Engine into this folder.
The API key is already configured in discovery-engine/.env.
Please set up the app completely:
1. Install all Python packages from discovery-engine/backend/requirements.txt
2. Make START.command and STOP.command executable by running: chmod +x START.command STOP.command
3. Verify the server starts correctly on port 8083
4. Tell me when it is ready
```

Claude Code will handle everything — installing packages, fixing permissions, and verifying the server.

---

## Step 3 — Merge the CLAUDE.md file (optional — only if you use Claude Code for other projects)

Open Claude Code at your **root working folder** and paste this:

```
I have a new file called ROOT_CLAUDE_METAFOREWORKS.md in my "Metafore Discovery Engine" subfolder.
Please read it, then read my existing root CLAUDE.md.
Merge the two files — keep all my existing content exactly as it is, only add sections
that are new and do not duplicate anything already there. Save back to root CLAUDE.md.
```

---

## Day-to-day use

| | Windows | Mac |
|--|---------|-----|
| Start the app | Double-click `START.bat` | Double-click `START.command` |
| Stop the app | Double-click `STOP.bat` | Double-click `STOP.command` |

The browser opens automatically at **http://localhost:8083**

Sample documents to try are in `discovery-engine/sample_docs/`

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Browser does not open | Go to http://localhost:8083 manually |
| "Port already in use" | Double-click STOP first, then START |
| "API key invalid" | Check `discovery-engine/.env` — key must start with `sk-ant-` |
| Python not found (Windows) | Install from python.org — tick "Add Python to PATH" |
| Python not found (Mac) | Install from python.org — standard install, no extra steps |
| Mac says "cannot be opened" on START.command | Open Claude Code in this folder and paste: `chmod +x START.command STOP.command` |

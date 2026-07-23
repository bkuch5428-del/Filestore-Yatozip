# File Store Pro Bot

A Telegram file-storage bot built with Python using Pyrogram (pyrofork) and MongoDB.

## Stack
- **Language:** Python 3
- **Telegram library:** pyrofork 2.3.50 (Pyrogram fork)
- **Database:** MongoDB (via Motor async driver)
- **Key features:** Force-subscribe channels, file link generation, auto-delete, URL shortener, multi-admin support, broadcast

## Project Structure
- `bot.py` — Bot entry point, client initialization
- `main.py` — App runner
- `config.py` — All configuration (tokens, IDs, messages, settings)
- `plugins/` — Feature handlers (start, admins, broadcast, force_sub, link_generator, etc.)
- `helper/` — Utility modules (database, db_channels, helper functions)

## Configuration (`config.py`)
Key values that must be set before running:
- `TOKEN` — Telegram Bot Token (from @BotFather)
- `API_ID` / `API_HASH` — Telegram API credentials (from my.telegram.org)
- `DB_URI` — MongoDB connection string
- `DB_NAME` — MongoDB database name
- `DB_CHANNEL` — Telegram channel ID used as file storage
- `FSUBS` — Force-subscribe channel list
- `ADMINS` — List of admin Telegram user IDs
- `OWNER_ID` — Bot owner Telegram user ID

## Running
```bash
pip install -r requirements.txt
python main.py
```

## User Preferences
<!-- Preferences noted here as the user shares them -->

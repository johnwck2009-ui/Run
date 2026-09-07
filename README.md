# G168 Run Bot

A simple Telegram running utility for logging runs and checking progress.

## Features
- Log distance and time for each run
- Calculate average pace
- View total runs, distance and time
- View recent runs
- Inline menu for quick access

## Setup

Set the following environment variable:

- `BOT_TOKEN` — your Telegram bot token

No sports API key is required.

## Run

```bash
pip install -r requirements.txt
python bot.py
```

## Render

Use `pip install -r requirements.txt` as the build command and `python bot.py` as the start command. Add `BOT_TOKEN` under Environment Variables.

Note: run history is stored in memory, so it resets if the service restarts. A database can be added later if permanent history is needed.

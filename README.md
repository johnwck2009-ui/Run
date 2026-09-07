# G168 Run Bot

A simple Telegram running tracker for recording runs and checking progress.

## Features

- Log distance and time for each run
- Calculate average pace automatically
- View total runs, distance, time, and overall pace
- View up to 10 recent runs
- Simple inline menu for quick access
- No external API or sports service required

## Setup

Set the following environment variable:

- `BOT_TOKEN` — your Telegram bot token

## Run locally

```bash
pip install -r requirements.txt
python bot.py
```

## Render

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
python bot.py
```

Add `BOT_TOKEN` under Environment Variables.

## Data storage

Run history is stored in memory while the bot is running. It resets if the service restarts or is redeployed. The bot does not require a database or external API key.

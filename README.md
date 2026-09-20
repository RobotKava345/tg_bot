# Telegram Admin Bot Template

Reusable Telegram administration bot template based on the latest working structure of `tg_bot` (Aiogram + Telethon + PostgreSQL).

The template is intended to be copied into a new repository and configured only through environment variables. It contains no tokens, database passwords, Telegram sessions, chat IDs, or local database files.

## What is included

- Aiogram 3 bot with long polling.
- PostgreSQL connection pool through `asyncpg`.
- Automatic `seen_users` table creation.
- Passive tracking of users who write messages or join a group.
- `/stats` command.
- `/sync` command that imports group members through Telethon.
- Telethon StringSession support, suitable for local use and cloud deployment.
- Forum-topic discovery through Telegram MTProto.
- Optional destructive bulk cleanup command, disabled by default.
- Flood-wait throttling for bulk Telegram actions.
- `.env.example`.
- Dockerfile.
- Render Blueprint (`render.yaml`).
- GitHub Actions syntax check.

## Project structure

```text
.
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml
├── database/
│   ├── __init__.py
│   ├── db.py
│   └── pool.py
├── handlers/
│   ├── __init__.py
│   ├── ext.py
│   ├── info.py
│   ├── stats.py
│   └── tracking.py
├── scripts/
│   └── generate_telethon_session.py
├── .gitignore
├── bot.py
├── config.py
├── Dockerfile
├── forum_topics.py
├── mtproto.py
├── render.yaml
├── requirements.txt
└── utils.py
```

## 1. Requirements

Recommended:

- Python 3.12.
- PostgreSQL 14+ or a managed PostgreSQL service.
- A Telegram bot token from BotFather.
- Telegram API ID and API hash from `my.telegram.org`.
- A Telegram user account for Telethon authorization.

## 2. Create the Telegram bot

1. Open BotFather in Telegram.
2. Run `/newbot`.
3. Follow BotFather's prompts.
4. Copy the bot token.
5. Do not paste the token into source code or commit it to Git.

The token will later be stored as `BOT_TOKEN`.

## 3. Get Telegram API ID and API hash

Telethon uses Telegram's MTProto API under a normal Telegram account.

1. Sign in at `https://my.telegram.org`.
2. Open **API development tools**.
3. Create an application.
4. Copy:
   - `api_id` -> `TELEGRAM_API_ID`
   - `api_hash` -> `TELEGRAM_API_HASH`

Treat the API hash as a secret.

## 4. Clone the template

```bash
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_REPOSITORY_DIRECTORY>
```

On Windows PowerShell the commands are the same.

## 5. Create a virtual environment

Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 6. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 7. Create the local environment file

Copy `.env.example` to `.env`.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Initially fill in:

```env
BOT_TOKEN=...
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
DATABASE_URL=...
DATABASE_SSL=true
ENABLE_DESTRUCTIVE_COMMANDS=false
```

Leave `TELETHON_SESSION_STRING` for the next step.

## 8. Create PostgreSQL

You can use local PostgreSQL or a managed provider such as Render.

The bot needs one database URL:

```text
postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

Put it into:

```env
DATABASE_URL=postgresql://...
```

For managed databases that require TLS, keep:

```env
DATABASE_SSL=true
```

For a local PostgreSQL instance without TLS you can use:

```env
DATABASE_SSL=false
```

You do not need to create tables manually. On startup the bot creates the `seen_users` table and its index if they do not exist.

## 9. Generate the Telethon session

The deployed bot should not rely on a local `telegram_session.session` file because many cloud containers have ephemeral disks. This template uses a Telethon StringSession stored in an environment variable.

Make sure `.env` already contains `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`, then run:

```bash
python scripts/generate_telethon_session.py
```

Telethon will ask for the Telegram account phone number, login code, and two-factor password if enabled.

At the end it prints:

```text
TELETHON_SESSION_STRING=...
```

Copy the full value into `.env`.

Important: a Telethon session string is highly sensitive. Do not send it to other people, put it in screenshots, logs, issues, or Git commits.

## 10. Run locally

```bash
python bot.py
```

A successful startup should initialize PostgreSQL, connect Telethon, and start Aiogram polling.

Stop the bot with `Ctrl+C`.

## 11. Add the bot to a Telegram group

1. Add the bot to the group.
2. Promote it to administrator.
3. Give only the permissions required by the features you intend to use.

For user tracking and statistics, fewer permissions are required.

For moderation or forum-topic deletion, Telegram must grant the bot the corresponding administrator permissions.

The Telethon user account represented by `TELETHON_SESSION_STRING` must also be able to access the target group. Otherwise `/sync` and forum-topic discovery cannot work.

## 12. Commands

### `/start`

Checks that the bot is responding.

### `/commands`

Shows the command list.

### `/stats`

Shows:

- the current member count reported by Telegram;
- how many unique users the bot has stored in PostgreSQL.

### `/sync`

Imports group members through Telethon into `seen_users`.

Only Telegram administrators can run this command.

This is useful because a bot cannot automatically enumerate every group member through the Bot API.

### `/fire_exterminatus confirm`

Optional destructive bulk cleanup inherited from the source project.

It can:

- ban tracked non-admin users;
- preserve Telegram admins and the bot itself;
- delete forum topics except General and the topic from which the command was run.

For safety it is disabled by default:

```env
ENABLE_DESTRUCTIVE_COMMANDS=false
```

To intentionally enable it:

```env
ENABLE_DESTRUCTIVE_COMMANDS=true
```

Even when enabled, the command checks that the caller is a Telegram administrator.

Do not enable it unless you actually need this behavior and understand the effect on the group.

## 13. How tracking works

The bot stores `(chat_id, user_id)` in PostgreSQL when:

- a non-bot user sends a non-command message;
- Telegram sends a chat-member update for a joining member;
- an administrator runs `/sync`.

The database uses a composite primary key, so the same user is not duplicated inside one chat.

## 14. Deploy to Render

### Option A: Blueprint

This repository contains `render.yaml`.

1. Push the project to GitHub.
2. In Render create a new Blueprint from the repository.
3. Render will create a background worker using `render.yaml`.
4. Set the secret environment variables in the Render dashboard:
   - `BOT_TOKEN`
   - `TELEGRAM_API_ID`
   - `TELEGRAM_API_HASH`
   - `TELETHON_SESSION_STRING`
   - `DATABASE_URL`
5. Keep `DATABASE_SSL=true` for Render PostgreSQL.
6. Leave `ENABLE_DESTRUCTIVE_COMMANDS=false` unless explicitly required.
7. Deploy.

The worker start command is:

```bash
python bot.py
```

### Option B: create the worker manually

Create a Python background worker and use:

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
python bot.py
```

Then add the same environment variables manually.

## 15. Deploy with Docker

Build:

```bash
docker build -t telegram-admin-bot .
```

Run using a local `.env`:

```bash
docker run --rm --env-file .env telegram-admin-bot
```

Do not bake `.env` into the image.

## 16. GitHub workflow

`.github/workflows/ci.yml` installs dependencies and runs:

```bash
python -m compileall -q .
```

on pushes and pull requests.

It is intentionally minimal so the template can be expanded with tests later.

## 17. Common errors

### `BOT_TOKEN is not configured`

The variable is missing from `.env` or the hosting environment.

### `TELETHON_SESSION_STRING is not configured`

Generate a session with:

```bash
python scripts/generate_telethon_session.py
```

### Telethon session is not authorized

The session is invalid, revoked, or was generated incorrectly. Generate a new StringSession.

### `TelegramConflictError`

Another process is polling with the same bot token. Stop the duplicate instance.

### PostgreSQL connection fails with an SSL/TLS error

For a managed PostgreSQL provider, verify:

```env
DATABASE_SSL=true
```

For a local database that does not use TLS:

```env
DATABASE_SSL=false
```

### `/sync` cannot find the group

The Telethon user account must have access to that group. Make sure the same Telegram account used to generate the session is a member of the target group.

### Bot cannot delete topics or ban users

Check the bot's administrator permissions in Telegram.

## 18. Security checklist

Before every public push:

- `.env` is not tracked;
- there are no `*.session` files;
- there are no `*.db` files;
- no database URL with a password is hardcoded;
- no bot token is hardcoded;
- no Telegram API hash is hardcoded;
- no Telethon StringSession is hardcoded;
- destructive commands are disabled unless intentionally required.

If a secret has ever been committed, deleting it in a later commit is not enough. Rotate/revoke the secret because it remains in Git history.

## 19. Creating a new repository from this template

The clean branch is designed to become a standalone repository.

If the repository is marked as a GitHub Template Repository, use **Use this template** in GitHub.

Otherwise create an empty repository and push this branch:

```bash
git clone --branch template --single-branch https://github.com/RobotKava345/tg_bot.git telegram-admin-bot-template
cd telegram-admin-bot-template

git remote remove origin
git remote add origin <NEW_REPOSITORY_URL>

git branch -M main
git push -u origin main
```

After that, configure secrets and deploy using the steps above.

# Discord Social Bot

Project: Discord bot that manages Facebook, Instagram, LinkedIn and TikTok using official APIs.  
Goal: Provide account linking, posting, scheduling and basic analytics from Discord.

## Quick start
1. Install deps:
   ```
   pip install -r requirements.txt
   ```
2. Copy `.env.example` → `.env` and fill values (Discord token, API keys, DB URL).
3. Run the bot:
   ```
   python src/bot.py
   ```

## Project overview
- Language: Python 3.11+
- Libraries: discord.py, requests, aiohttp, APScheduler, python-dotenv, sqlalchemy/your DB driver, cryptography
- Scheduler: APScheduler (schedules posts stored in DB)
- DB: choose MongoDB or PostgreSQL (current code uses config.py — replace with real DB settings)

## Repo structure
- src/
  - bot.py                — Entry point, loads cogs
  - config.py             — Environment and app constants
  - cogs/
    - facebook.py         — Facebook commands (connect, disconnect, post, recent, etc.)
    - instagram.py        — Instagram commands
    - linkedin.py         — LinkedIn commands
    - tiktok.py           — TikTok commands
  - services/
    - facebook.py         — Low-level FB Graph API wrappers
    - instagram.py
    - linkedin.py
    - tiktok.py
  - utils/
    - database.py         — DB helpers / models
    - oauth.py            — OAuth helpers, token storage
    - scheduler.py        — APScheduler setup and job runner
  - tests/                — Unit tests
- .env.example
- requirements.txt
- README.md

## Important files to edit
- src/config.py — add CLIENT IDs/SECRETS and DISCORD_TOKEN
- src/utils/oauth.py — implement real token storage (DB + encryption)
- src/utils/database.py — swap file token storage for DB
- src/cogs/* — implement platform-specific command flows

## Commands (examples)
- Account management
  - `!connect_facebook` — send OAuth URL (DM)
  - `!disconnect_facebook`
  - `!accounts` — list connected accounts
- Posting
  - `!post_facebook <message>`
  - `!post_instagram <caption>` (image upload flows require multipart)
  - `!schedule <platform> <ISO-datetime> <content>`
  - `!crosspost <content>`
- Monitoring
  - `!recent <platform>`
  - `!stats <platform>`

(Actual prefixes/command names live in `src/cogs/*`.)

## Developer workflow
- Branch per feature (e.g., feature/facebook-oauth)
- Run bot locally, test OAuth flows using local redirect URIs or ngrok
- Add unit tests under `src/tests/`
- Use env vars for secrets, never commit them

## OAuth & callback
- Provide a small web server (Flask or aiohttp) to handle provider callbacks:
  - Exchange `code` for tokens
  - Persist tokens with expiry and refresh_token
  - Save mapping: discord_guild_id ↔ platform_account (store page_id if applicable)

## Scheduler
- APScheduler checks DB every minute for ready posts
- Jobs must handle retries and rate-limit backoff

## Security & best practices
- Encrypt tokens at rest (cryptography)
- Keep secrets in `.env` or secret manager
- Rate-limit bot commands (discord.py cooldowns)
- Log errors to file, not to console with secrets

## Testing & CI
- Unit-test API wrappers with mocked HTTP (responses / pytest-mock)
- Integration tests use staging tokens and test accounts

## Notes for team
- Person 1 (Facebook): implement OAuth callback server, token storage, and post endpoints first.
- Use `src/config.py` as development defaults, but prefer `.env` and secret management in production.
- Document API quotas used by each command to avoid hitting provider limits.

## Contributing
- Open an issue for major changes
- Submit PRs to `main` with clear description and tests

## Contacts
- Project lead / task owners: update this file with your Discord handles and responsibilities.

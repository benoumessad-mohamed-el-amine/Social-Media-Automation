...existing code...
# Discord Social Media Manager

Lightweight Discord bot + FastAPI service to manage Facebook, Instagram, LinkedIn and TikTok accounts (OAuth, posting, scheduling, basic analytics). Uses MongoDB for storage.

---

## Quick start

1. Create and activate virtualenv
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Copy env example and edit
   ```bash
   cp .env.example .env
   # fill values: DISCORD_TOKEN, MONGODB_URL, platform client ids/secrets
   ```

4. Start MongoDB (local) or ensure remote DB is available
   ```bash
   sudo systemctl start mongod
   ```

5. Run FastAPI (handles OAuth callbacks)
   ```bash
   uvicorn src.api.main:app --reload --port 8080
   ```

6. Run Discord bot
   ```bash
   python src/bot.py
   ```

---

## Project layout

- src/
  - api/                    FastAPI server for OAuth callbacks and light APIs
    - routes/                platform-specific OAuth routes (facebook, instagram, linkedin, tiktok)
    - main.py                FastAPI app entry
    - models/                Pydantic schemas for requests/responses
  - bot/                    Discord bot entry and cogs
    - cogs/                 Commands per platform (facebook, instagram, linkedin, tiktok, helpers)
    - main.py               Bot startup wrapper (loads cogs, scheduler)
  - core/                   shared configuration and logging
    - config.py
    - logger.py
  - db/                     MongoDB models & repositories (motor)
    - models.py
    - repositories/
  - services/               Platform API clients (Graph API, LinkedIn, TikTok)
  - utils/                  Encryption, scheduler (APScheduler), validators, helpers
- tests/                    Unit and integration tests
- .env
- requirements.txt
- docker-compose.yml
- README.md

---

## Environment variables (required in .env)

- DISCORD_TOKEN - Discord bot token
- MONGODB_URL - MongoDB connection URI (eg. mongodb://localhost:27017)
- DB_NAME - Database name (default: discord_social)
- FACEBOOK_CLIENT_ID / FACEBOOK_CLIENT_SECRET
- INSTAGRAM_CLIENT_ID / INSTAGRAM_CLIENT_SECRET
- LINKEDIN_CLIENT_ID / LINKEDIN_CLIENT_SECRET
- TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET
- API_HOST / API_PORT (FastAPI)

---

## Important workflows

- OAuth flow:
  - User runs `/connect <platform>` in Discord
  - Bot sends OAuth URL (FastAPI handles callback)
  - FastAPI exchanges code → tokens, stores encrypted tokens in MongoDB under platform_accounts

- Scheduling:
  - Posts saved in `scheduled_posts` collection
  - APScheduler (bot or separate worker) checks DB periodically and publishes due posts
  - Status updates and retries recorded in DB

- Token safety:
  - Tokens encrypted (cryptography/Fernet) before writing to DB
  - Refresh tokens used to renew expired access tokens

---

## Commands (examples)

- Account management
  - /connect <platform>
  - /disconnect <platform>
  - /accounts

- Publishing
  - /post <platform> <content>
  - /schedule <platform> <ISO-datetime> <content>
  - /crosspost <content>

- Monitoring
  - /recent <platform>
  - /stats <platform>
  - /post-insights <post_id>

---

## Development & testing

- Run unit tests:
  ```bash
  pytest
  ```

- Run dev servers
  - FastAPI: `uvicorn src.api.main:app --reload --port 8080`
  - Bot: `python src/bot.py`

- Use ngrok when testing OAuth callbacks locally:
  ```bash
  ngrok http 8080
  ```

- Branching: feature/<platform>-<task>, open PR to `main`, include tests

---

## Team tasks (short)

- Person 1 — infra + Facebook OAuth & posting
- Person 2 — Instagram integration + analytics
- Person 3 — LinkedIn + scheduler
- Person 4 — TikTok + bulk ops & tests
- Person 5 — Discord UX, commands, embeds and polish

---

## Notes

- Keep secrets out of Git. Use `.env` and CI secrets.
- Measure API usage and add rate-limit handling per platform.
- Start with Facebook posting + OAuth and a working scheduler — then add analytics.
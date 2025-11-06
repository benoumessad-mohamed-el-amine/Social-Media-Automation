...existing code...
# Discord Social Media Manager

The Discord Social Media Automation Bot is a centralized management tool that allows teams and individuals to control multiple social media accounts (Facebook, Instagram) directly from a Discord server.
It transforms Discord into a command center for social media operations, enabling real-time posting, cross-posting, moderation, and account oversight — all without leaving the chat.


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

4. Run Discord bot
   ```bash
   python src/bot.py
   ```

---

## Project layout

- src/
    - cogs/                 Commands per platform (facebook, instagram, linkedin, tiktok, helpers)

  - services/               Platform API clients (Graph API,facebookservices ,scheduler services)
  - utils/                  Encryption, scheduler (APScheduler)
       - db/                MongoDB models & repositories (motor)
    - models.py
    - mongodb_handler.py
    - encryption.py          
- tests/                    Unit and integration tests
- bot.py                  Discord bot entry 
- .env
- requirements.txt
- docker-compose.yml
- README.md

---

## Environment variables (required in .env)

- DISCORD_TOKEN - Discord bot token
- MONGODB_URL - MongoDB connection URI (eg. mongodb://localhost:27017)
- DB_NAME - Database name (default: discord_social)
- ENCRYPTION_KEY="you can generate your key using key generator function  (exemple : JAWGd_tuF-vm8yXv3BdHSSkzgXKLHWvm_MRSzOfQgbk=)
- ENCRYPTION_SALT=(exemple: kxNcx2szYIICKHQG-lI1QbvwKWxeWNt2r_lgIXvXpRo=)
- ENCRYPTION_METHOD=aes-gcm (encryption method)
- FACEBOOK_CLIENT_ID / FACEBOOK_CLIENT_SECRET
- INSTAGRAM_CLIENT_ID / INSTAGRAM_CLIENT_SECRET
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
  - /reply [platform] [post_id] [comment]
  - /delete [platform] [post_id]
  - /help

---


## Notes

- Keep secrets out of Git. Use `.env` and CI secrets.
- Measure API usage and add rate-limit handling per platform.
- Start with Facebook posting + OAuth and a working scheduler — then add analytics.

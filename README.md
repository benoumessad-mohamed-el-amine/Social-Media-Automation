# Discord Social Bot

Project: Discord bot that manages Facebook, Instagram, LinkedIn and TikTok using official APIs.  
Goal: Provide account linking, posting, scheduling and basic analytics from Discord.

## Quick start
1. Install deps:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` → `.env` and fill values (Discord token, API keys, MongoDB URL).
3. Start MongoDB:
   ```bash
   sudo systemctl start mongod
   ```
4. Start FastAPI server (handles OAuth callbacks):
   ```bash
   uvicorn src.api.main:app --reload --port 8080
   ```
5. Run the bot:
   ```bash
   python src/bot.py
   ```

## Project overview
- Language: Python 3.11+
- Core Libraries: 
  - discord.py - Bot framework
  - FastAPI - OAuth callback server
  - motor - Async MongoDB driver
  - APScheduler - Post scheduling
  - python-dotenv - Environment management
  - pydantic - Data validation
  - cryptography - Token encryption

## Repo structure
```
src/
├── api/                   # FastAPI OAuth callback server
│   ├── main.py           # API entry point
│   ├── routes/           # Platform-specific OAuth routes
│   └── models.py         # Pydantic models
├── bot.py                # Discord bot entry point
├── config.py             # Environment and app constants
├── cogs/                 # Discord bot commands
├── services/             # Platform API wrappers
├── utils/
│   ├── database.py       # MongoDB helpers
│   ├── oauth.py          # OAuth helpers
│   └── scheduler.py      # APScheduler setup
└── tests/                # Unit tests
```

## MongoDB Collections
- `guilds` - Discord server settings
- `platform_accounts` - OAuth tokens and account info
- `scheduled_posts` - Pending scheduled posts
- `post_analytics` - Historical post performance

## Important files to edit
- src/api/main.py - FastAPI OAuth callback handlers
- src/utils/database.py - MongoDB operations
- src/cogs/* - Platform-specific commands

## Commands (examples)
[Previous commands section remains the same]

## Developer workflow
- Branch per feature (e.g., feature/facebook-oauth)
- Run both FastAPI server and Discord bot locally
- Test OAuth flows using ngrok for public callbacks
- Add unit tests under `src/tests/`
- Use `.env` for secrets

## OAuth & callback (FastAPI)
- FastAPI endpoints handle provider callbacks:
  - GET `/oauth/{platform}/callback` - Handle initial OAuth code
  - POST `/oauth/{platform}/refresh` - Refresh expired tokens
- Tokens stored in MongoDB with:
  - AES encryption at rest
  - Automatic refresh handling
  - Guild ID ↔ platform account mapping

## Scheduler
- APScheduler + MongoDB for reliable scheduling
- Atomic updates prevent double-posting
- Retries with exponential backoff

## Security & best practices
- Encrypt tokens using Fernet (cryptography)
- MongoDB authentication required
- Rate-limit bot commands using discord.py
- Structured logging with rotation

## Testing & CI
- Unit tests with pytest and motor-asyncio
- Mock MongoDB operations for testing
- Integration tests use staging credentials

## Environment Variables
```bash
# Discord
DISCORD_TOKEN=your_token

# MongoDB
MONGODB_URL=mongodb://localhost:27017
DB_NAME=discord_social

# OAuth
FACEBOOK_CLIENT_ID=xxx
FACEBOOK_CLIENT_SECRET=xxx
# [Other platform credentials]

# FastAPI
API_HOST=localhost
API_PORT=8080
```

## Notes for team
- Person 1 (Facebook): Implement FastAPI OAuth routes and MongoDB storage first
- Use motor for async MongoDB operations
- Document API rate limits in comments

## Contributing
- Open an issue for major changes
- Submit PRs to `main` with tests
- Follow Black code formatting

## Contacts
[Previous contacts section remains the same]
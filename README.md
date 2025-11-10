# Discord Social Media Bot

A Discord bot that enables managing multiple social media accounts (Facebook, Instagram, LinkedIn, TikTok) through Discord commands. Built with Python, Discord.py, and MongoDB.

## Features

- 🔑 OAuth2 authentication for social media platforms
- 📝 Post content to multiple platforms
- ⏰ Schedule posts for later publication
- 📊 View basic analytics and insights
- 🔄 Cross-post to multiple platforms
- 🗑️ Delete posts across platforms
- 💬 Reply to comments/interactions
- 📈 Track engagement metrics

## Technology Stack

- **Python 3.12+**
- **Discord.py** - Bot framework
- **MongoDB** - Data storage
- **Motor** - Async MongoDB driver
- **APScheduler** - Post scheduling
- **Pydantic** - Data validation
- **aiohttp** - Async HTTP client
- **cryptography** - Token encryption

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd discord-social-bot
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

Create a `.env` file with the following variables:

```env
# Discord
DISCORD_TOKEN=your_discord_bot_token

# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=social_bot

# Encryption
ENCRYPTION_KEY=your_encryption_key

# Facebook/Instagram
FACEBOOK_APP_ID=your_fb_app_id
FACEBOOK_APP_SECRET=your_fb_app_secret
INSTAGRAM_REDIRECT_URI=http://localhost:8000/oauth/callback

# Other platforms...
LINKEDIN_CLIENT_ID=your_linkedin_client_id
TIKTOK_CLIENT_KEY=your_tiktok_client_key
```

## Usage

1. Start MongoDB:
```bash
mongod
```

2. Run the OAuth server:
```bash
python -m src.utils.oauth_server
```

3. Start the bot:
```bash
python -m src.bot
```

## Discord Commands

### Account Management
- `/connect <platform>` - Connect social media account
- `/disconnect <platform>` - Disconnect account
- `/accounts` - List connected accounts

### Posting
- `/post <platform> <content>` - Post to platform
- `/crosspost <content>` - Post to all platforms
- `/schedule <platform> <datetime> <content>` - Schedule post

### Moderation
- `/reply <platform> <post_id> <comment>` - Reply to post
- `/delete <platform> <post_id>` - Delete post

### Analytics
- `/stats <platform>` - View platform stats
- `/recent <platform>` - Show recent posts

## Development

### Project Structure
```
discord-social-bot/
├── src/
│   ├── bot.py            # Bot entry point
│   ├── cogs/            # Command groups
│   ├── services/        # Platform APIs
│   └── utils/           # Helpers & utilities
├── tests/               # Test files
└── docker-compose.yml   # Docker configuration
```

### Running Tests
```bash
python -m pytest tests/
```

### Docker Deployment
```bash
docker-compose up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

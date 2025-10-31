# Discord Social Bot

This project is a Discord bot that manages social media interactions across Facebook, Instagram, LinkedIn, and TikTok using their official APIs.

## Features

- Basic "Hello World" command to demonstrate bot functionality.
- Integration with Facebook Graph API for posting content and retrieving analytics.
- Integration with Instagram Graph API for posting media and fetching insights.
- Integration with LinkedIn API for posting updates and retrieving statistics.
- Integration with TikTok Business API for uploading videos and fetching analytics.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/discord-social-bot.git
   cd discord-social-bot
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables by copying `.env.example` to `.env` and filling in the necessary API keys and tokens.

## Usage

To run the bot, execute the following command:
```
python src/bot.py
```

## Commands

- `!hello`: Responds with a greeting.

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
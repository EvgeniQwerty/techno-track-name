# Techno Track Name Generator Bot

A Telegram bot that generates creative names for techno tracks using AI.

## Features

- **Random Generation**: Get random track names in different styles
- **Keyword-Based Generation**: Generate names based on keywords you provide
- **Example-Based Generation**: Create names similar to an example you provide
- **Style Options**: Choose between serious and non-serious track names

## Prerequisites

- Python 3.7+
- Telegram Bot Token (from [BotFather](https://t.me/BotFather))
- OpenRouter API Key (from [OpenRouter](https://openrouter.ai/))

## Setup

1. **Clone the repository**

2. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

3. **Create a .env file in the project root with the following variables:**
   ```
   BOT_TOKEN=your_telegram_bot_token
   OPENROUTER_API_KEY=your_openrouter_api_key
   ```

4. **Run the bot**
   ```
   python main.py
   ```

## How It Works

The bot uses the aiogram framework to handle Telegram interactions and the OpenRouter API to generate creative track names. It offers three generation modes:

1. **Random Generation**: Creates track names based only on the selected style
2. **Keyword-Based Generation**: Uses your keywords to influence the generated names
3. **Example-Based Generation**: Creates names similar to an example you provide

Each mode can generate serious names (related to science, technology, philosophy, etc.) or non-serious names (humorous, absurd, playful).

## Commands

- `/start` - Start the bot and show the main menu
- `/help` - Show help information

## Troubleshooting

- If the bot doesn't respond, check that your environment variables are correctly set
- Ensure you have a stable internet connection
- Verify that your OpenRouter API key has sufficient credits
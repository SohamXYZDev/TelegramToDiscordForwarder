# Telegram to Discord Forwarder

A Python selfbot that monitors specific Telegram channels and forwards messages to Discord via webhooks.

## ⚠️ Important Disclaimer

This is a **selfbot** that uses your personal Telegram account. Please note:
- Selfbots are against Telegram's Terms of Service if used for automation
- Use this at your own risk
- This is meant for personal use and educational purposes only
- Your account could be banned if Telegram detects unusual activity

## Features

- 🔄 Real-time message forwarding from Telegram to Discord
- 📢 Monitor multiple Telegram channels simultaneously
- 🎨 Formatted Discord embeds with source information
- 🔗 Direct links to original Telegram messages (when available)
- 🛡️ Error handling and logging

## Prerequisites

- Python 3.8 or higher
- A Telegram account
- Telegram API credentials (API ID and API Hash)
- A Discord webhook URL

## Installation

1. **Clone or download this repository**

2. **Install required packages**
   ```bash
   pip install -r requirements.txt
   ```

3. **Get Telegram API credentials**
   - Go to https://my.telegram.org/apps
   - Log in with your phone number
   - Create a new application
   - Copy your `API ID` and `API Hash`

4. **Create a Discord webhook**
   - Open Discord and go to Server Settings
   - Navigate to Integrations → Webhooks
   - Click "New Webhook"
   - Copy the Webhook URL

5. **Configure environment variables**
   - Copy `.env.example` to `.env`
   - Fill in your credentials:
     ```env
     TELEGRAM_API_ID=your_api_id
     TELEGRAM_API_HASH=your_api_hash
     TELEGRAM_PHONE=+1234567890
     DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
     MONITORED_CHANNELS=@channel1,@channel2,Channel Name
     ```

## Configuration

### Environment Variables

- `TELEGRAM_API_ID`: Your Telegram API ID from my.telegram.org
- `TELEGRAM_API_HASH`: Your Telegram API Hash from my.telegram.org
- `TELEGRAM_PHONE`: Your phone number with country code (e.g., +1234567890)
- `DISCORD_WEBHOOK_URL`: Your Discord webhook URL
- `MONITORED_CHANNELS`: Comma-separated list of channels to monitor

### Channel Specification

You can specify channels in multiple ways:
- By username: `@channelname`
- By title: `Channel Title`

Example:
```env
MONITORED_CHANNELS=@example_channel,News Channel,@another_channel
```

## Usage

1. **First run** - Authentication
   ```bash
   python main.py
   ```
   On first run, you'll be prompted to:
   - Enter the verification code sent to your Telegram
   - Enter 2FA password if you have it enabled

2. **Subsequent runs**
   ```bash
   python main.py
   ```
   The bot will start monitoring and forwarding messages automatically.

3. **Stop the bot**
   - Press `Ctrl+C` to stop the bot gracefully

## How It Works

1. The bot connects to Telegram using your account (selfbot)
2. It listens for new messages in all chats
3. When a message is received, it checks if it's from a monitored channel
4. If yes, it formats the message and sends it to Discord via webhook
5. Discord receives the message as an embed with the channel name and original message link

## File Structure

```
TelegramToDiscordForwarder/
├── main.py                 # Main bot script
├── requirements.txt        # Python dependencies
├── .env                    # Your configuration (create from .env.example)
├── .env.example           # Example configuration
├── .gitignore             # Git ignore rules
├── README.md              # This file
└── telegram_selfbot.session  # Generated after first run (don't share!)
```

## Troubleshooting

### "Missing required environment variables"
- Make sure your `.env` file exists and contains all required variables
- Check that there are no typos in variable names

### "No channels specified"
- Add at least one channel to `MONITORED_CHANNELS` in your `.env` file

### Messages not being forwarded
- Verify the channel name/username is correct
- Make sure you're subscribed to the channel in Telegram
- Check the console logs for any errors

### Authentication issues
- Delete the `.session` file and run again to re-authenticate
- Make sure your phone number includes the country code

### Discord webhook not working
- Verify your webhook URL is correct
- Check that the webhook hasn't been deleted in Discord

## Security Notes

- Never commit your `.env` file or `.session` files to version control
- Keep your API credentials and session files private
- Use a separate Discord webhook for testing

## License

This project is provided as-is for educational purposes. Use responsibly and at your own risk.

## Contributing

Feel free to submit issues or pull requests if you have suggestions for improvements.

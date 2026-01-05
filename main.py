import os
import asyncio
import logging
import re
import json
from telethon import TelegramClient, events
from telethon.tl.types import Channel
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Telegram API credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')

# Discord webhook URL
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Telegram channels to monitor (comma-separated)
MONITORED_CHANNELS = os.getenv('MONITORED_CHANNELS', '').split(',')
MONITORED_CHANNELS = [ch.strip() for ch in MONITORED_CHANNELS if ch.strip()]

# Session name
SESSION_NAME = 'telegram_selfbot'


def parse_channel_identifier(channel_input):
    """
    Parse various Telegram channel formats and extract identifier.
    
    Supported formats:
    - @username
    - username
    - t.me/username
    - https://t.me/username
    - https://t.me/+invitehash (private channel invite)
    - https://t.me/c/1234567890/123 (private channel message link)
    - 1234567890 (direct channel ID)
    - -1001234567890 (full channel ID with prefix)
    
    Returns: dict with 'type' ('username', 'id', or 'invite') and 'value'
    """
    channel_input = channel_input.strip()
    
    # Direct channel ID (starts with - or is just numbers)
    if re.match(r'^-?\d+$', channel_input):
        channel_id = int(channel_input)
        # Convert to proper format if needed
        if channel_id > 0 and len(str(channel_id)) > 10:
            channel_id = -1000000000000 - channel_id
        return {'type': 'id', 'value': channel_id}
    
    # Private channel message link: t.me/c/1234567890/123
    match = re.search(r't\.me/c/(\d+)', channel_input)
    if match:
        channel_id = int(match.group(1))
        # Convert to full channel ID format
        full_id = -1000000000000 - channel_id
        return {'type': 'id', 'value': full_id}
    
    # Private invite link: t.me/+hash or t.me/joinchat/hash
    if re.search(r't\.me/\+|t\.me/joinchat/', channel_input):
        return {'type': 'invite', 'value': channel_input}
    
    # Public channel username: t.me/username or @username or just username
    match = re.search(r't\.me/([a-zA-Z0-9_]+)', channel_input)
    if match:
        return {'type': 'username', 'value': match.group(1).lower()}
    
    # Just @username or username
    username = channel_input.lstrip('@').lower()
    if username:
        return {'type': 'username', 'value': username}
    
    return None


async def send_to_discord(message_text, channel_name, message_url=None, image_url=None):
    """Send a message to Discord webhook"""
    try:
        async with aiohttp.ClientSession() as session:
            embed = {
                "title": f"New message from {channel_name}",
                "description": message_text[:4096] if message_text else "No text content",
                "color": 5814783,  # Blue color
                "footer": {
                    "text": f"Source: {channel_name}"
                }
            }
            
            if message_url:
                embed["url"] = message_url
            
            # Add image to embed if present
            if image_url:
                embed["image"] = {"url": image_url}
            
            payload = {
                "embeds": [embed]
            }
            
            async with session.post(DISCORD_WEBHOOK_URL, json=payload) as response:
                if response.status == 204:
                    logger.info(f"Successfully forwarded message to Discord from {channel_name}")
                else:
                    logger.error(f"Failed to send to Discord. Status: {response.status}")
                    
    except Exception as e:
        logger.error(f"Error sending to Discord: {e}")


async def main():
    """Main function to run the selfbot"""
    
    # Validate environment variables
    if not all([API_ID, API_HASH, PHONE, DISCORD_WEBHOOK_URL]):
        logger.error("Missing required environment variables. Please check your .env file.")
        return
    
    if not MONITORED_CHANNELS:
        logger.error("No channels specified in MONITORED_CHANNELS. Please add at least one channel.")
        return
    
    # Create the client and connect
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start(phone=PHONE)
    
    # Parse monitored channels and resolve them
    monitored_chat_ids = set()
    monitored_usernames = set()
    
    logger.info("Resolving monitored channels...")
    for channel_input in MONITORED_CHANNELS:
        parsed = parse_channel_identifier(channel_input)
        if not parsed:
            logger.warning(f"Could not parse channel identifier: {channel_input}")
            continue
        
        try:
            if parsed['type'] == 'id':
                # Direct channel ID
                monitored_chat_ids.add(parsed['value'])
                logger.info(f"Monitoring channel ID: {parsed['value']}")
                
            elif parsed['type'] == 'username':
                # Public channel username
                monitored_usernames.add(parsed['value'])
                logger.info(f"Monitoring channel: @{parsed['value']}")
                
            elif parsed['type'] == 'invite':
                # Private invite link - need to join and get entity
                try:
                    entity = await client.get_entity(channel_input)
                    chat_id = entity.id
                    monitored_chat_ids.add(chat_id)
                    logger.info(f"Monitoring private channel (ID: {chat_id}) from invite link")
                except Exception as e:
                    logger.error(f"Could not resolve invite link {channel_input}: {e}")
                    logger.error("Make sure you've joined this channel in Telegram first")
                    
        except Exception as e:
            logger.error(f"Error resolving channel {channel_input}: {e}")
    
    if not monitored_chat_ids and not monitored_usernames:
        logger.error("No valid channels could be resolved. Please check your channel links.")
        return
    
    logger.info(f"Monitoring {len(monitored_chat_ids) + len(monitored_usernames)} channel(s)")
    
    @client.on(events.NewMessage())
    async def handler(event):
        """Handle new messages from monitored channels, groups, and DMs"""
        try:
            # Get the chat entity
            chat = await event.get_chat()
            chat_id = event.chat_id
            
            # Get chat details
            if hasattr(chat, 'username'):
                chat_username = chat.username
            else:
                chat_username = None
            
            if hasattr(chat, 'title'):
                chat_title = chat.title
            elif hasattr(chat, 'first_name'):
                # DM - use person's name
                chat_title = chat.first_name
                if hasattr(chat, 'last_name') and chat.last_name:
                    chat_title += f" {chat.last_name}"
            else:
                chat_title = 'Unknown'
            
            # Check if this chat is in our monitored list
            is_monitored = False
            
            # Check by ID
            if chat_id in monitored_chat_ids:
                is_monitored = True
            
            # Check by username
            if chat_username and chat_username.lower() in monitored_usernames:
                is_monitored = True
            
            if is_monitored:
                message_text = event.message.message or "[No text content]"
                
                # Check for photo/image
                image_url = None
                if event.message.photo:
                    try:
                        # Download photo to memory
                        photo_bytes = await client.download_media(event.message.photo, file=bytes)
                        
                        # Upload to a temporary hosting service or use Telegram's CDN
                        # For now, we'll try to get the file URL directly
                        # Telegram CDN URLs can be constructed but require file access hash
                        # Simpler approach: Download and re-upload to Discord
                        
                        # Get the largest photo size
                        largest_photo = max(event.message.photo.sizes, key=lambda s: s.size if hasattr(s, 'size') else 0)
                        
                        # Construct Telegram CDN URL (may not always work for private chats)
                        # Alternative: We'll attach the photo directly
                        logger.info(f"Message contains a photo")
                        
                    except Exception as e:
                        logger.error(f"Error processing photo: {e}")
                
                # Try to construct message URL
                message_url = None
                if isinstance(chat, Channel):
                    # Channel
                    if chat_username:
                        # Public channel
                        message_url = f"https://t.me/{chat_username}/{event.message.id}"
                    else:
                        # Private channel - use c/ format
                        short_id = abs(chat_id) - 1000000000000
                        message_url = f"https://t.me/c/{short_id}/{event.message.id}"
                # For DMs/groups, we can't create a direct link easily
                
                chat_type = "Channel" if isinstance(chat, Channel) else "DM/Group"
                logger.info(f"New message from {chat_title} ({chat_type}, ID: {chat_id}): {message_text[:50]}...")
                
                # Forward to Discord (with or without image)
                if event.message.photo:
                    # Download and send photo separately
                    try:
                        photo_bytes = await client.download_media(event.message.photo, file=bytes)
                        
                        # Send to Discord with file upload
                        async with aiohttp.ClientSession() as session:
                            form = aiohttp.FormData()
                            form.add_field('file', photo_bytes, filename='image.jpg', content_type='image/jpeg')
                            
                            # Create embed
                            embed = {
                                "title": f"New message from {chat_title}",
                                "description": message_text[:4096] if message_text else "📷 Image",
                                "color": 5814783,
                                "footer": {"text": f"Source: {chat_title}"}
                            }
                            if message_url:
                                embed["url"] = message_url
                            
                            payload = {
                                "embeds": [embed]
                            }
                            form.add_field('payload_json', json.dumps(payload))
                            
                            async with session.post(DISCORD_WEBHOOK_URL, data=form) as response:
                                if response.status == 200 or response.status == 204:
                                    logger.info(f"Successfully forwarded message with image to Discord from {chat_title}")
                                else:
                                    logger.error(f"Failed to send to Discord. Status: {response.status}")
                    except Exception as e:
                        logger.error(f"Error sending photo to Discord: {e}")
                        # Fallback to text only
                        await send_to_discord(
                            message_text,
                            chat_title or chat_username or f"Chat {chat_id}",
                            message_url
                        )
                else:
                    # Text only message
                    await send_to_discord(
                        message_text,
                        chat_title or chat_username or f"Chat {chat_id}",
                        message_url
                    )
                    
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    logger.info("Selfbot started successfully! Listening for messages...")
    logger.info("Press Ctrl+C to stop")
    
    # Keep the client running
    await client.run_until_disconnected()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Selfbot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

import requests
import time
import os
from pyrogram import filters, Client
from pyrogram.enums import ChatAction, ChatMemberStatus
from datetime import datetime, timedelta

# Store user warnings and mute history
user_warnings = {}
mute_history = {}

# Adult content keywords (add more as needed)
ADULT_KEYWORDS = [
    "nude", "naked", "porn", "sex", "nsfw", "xxx", "adult", "18+", 
    "explicit", "erotic", "pornographic", "sexual"
]

async def check_adult_content(text):
    """Check if text contains adult content keywords"""
    text = text.lower()
    return any(keyword in text for keyword in ADULT_KEYWORDS)

async def get_mute_duration(user_id):
    """Calculate mute duration based on user's history"""
    if user_id not in mute_history:
        return 60  # First mute: 1 hour
    
    last_duration = mute_history[user_id]['last_duration']
    return last_duration * 2  # Double the previous duration

async def mute_user(client, chat_id, user_id, duration_minutes):
    """Mute a user for specified duration"""
    try:
        until_date = datetime.now() + timedelta(minutes=duration_minutes)
        await client.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions={},  # Empty permissions = mute
            until_date=until_date
        )
        
        # Update mute history
        mute_history[user_id] = {
            'last_mute': datetime.now(),
            'last_duration': duration_minutes
        }
        
        return True, duration_minutes
    except Exception as e:
        return False, str(e)

# Add proper timeout and error handling for API requests
def generate_image(prompt):
    try:
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "prompt": prompt,
            "model": "stable-diffusion-xl-v1-0",
            "negative_prompt": "",
            "width": 1024,
            "height": 1024,
            "steps": 50,
            "n_samples": 1,
            "safety_check": True
        }

        # Add timeout and proper error handling
        response = requests.post(
            "https://api.lexica.art/v2/generate",
            headers=headers,
            json=data,
            timeout=30  # 30 seconds timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API returned status code {response.status_code}")
            
    except requests.exceptions.Timeout:
        raise Exception("Request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise Exception("Connection error. Please check your internet connection.")
    except Exception as e:
        raise Exception(f"Error generating image: {str(e)}")

@Client.on_message(filters.command(["imagine", "generate"]))
async def imagine_image(client, message):
    try:
        # Get the prompt
        if len(message.command) < 2:
            await message.reply_text("Please provide a prompt after the command.")
            return
            
        prompt = " ".join(message.command[1:])
        
        # Check for adult content
        if await check_adult_content(prompt):
            await message.reply_text("❌ Adult/NSFW content is not allowed.")
            return

        # Send "generating" message
        status_message = await message.reply_text("🎨 Generating your image, please wait...")
        
        try:
            # Show typing action
            await client.send_chat_action(message.chat.id, ChatAction.TYPING)
            
            # Generate image
            result = generate_image(prompt)
            
            if not result or 'images' not in result:
                raise Exception("Failed to generate image")
                
            # Get the image URL
            image_url = result['images'][0]['url']
            
            # Download and send image
            await client.send_chat_action(message.chat.id, ChatAction.UPLOAD_PHOTO)
            await message.reply_photo(
                photo=image_url,
                caption=f"🎨 Generated image for: {prompt}"
            )
            
        except Exception as e:
            await message.reply_text(f"Failed to generate image: {str(e)}")
        finally:
            # Delete the status message
            await status_message.delete()
            
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")

# Command to check user's warning status
@Client.on_message(filters.command(['warnings']))
async def check_warnings(client, message):
    user_id = message.from_user.id
    if user_id in user_warnings:
        warning_info = user_warnings[user_id]
        mute_info = mute_history.get(user_id, {})
        
        response = (
            f"**Warning Status for {message.from_user.mention}**\n"
            f"Warnings: {warning_info['count']}\n"
            f"Last Warning: {warning_info['last_warning'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        
        if mute_info:
            response += (
                f"Last Mute Duration: {mute_info['last_duration']} minutes\n"
                f"Last Mute: {mute_info['last_mute'].strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        await message.reply_text(response)
    else:
        await message.reply_text(f"No warnings found for {message.from_user.mention}")

__mod_name__ = "Image Generation"

__help__ = """
*Image Generation Commands:*
❍ /imagine or /generate: Generate AI art from text description
❍ /warnings: Check your warning status

Example: `/imagine a beautiful sunset over mountains`

Note: 
- Generation usually takes 10-30 seconds
- Adult content is not allowed
- First violation: Warning
- Subsequent violations: Mute with increasing duration or permanent ban
"""

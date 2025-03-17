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

@Client.on_message(filters.command(['imagine', 'generate']))
async def generate_image(client, message):
    try:
        # Check if prompt is provided
        if len(message.command) < 2:
            await message.reply_text("Please provide a prompt!\nExample: `/imagine a beautiful sunset`")
            return

        # Get the prompt and user info
        prompt = ' '.join(message.command[1:])
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Check for adult content
        if await check_adult_content(prompt):
            # Check user's warning status
            if user_id not in user_warnings:
                user_warnings[user_id] = {
                    'count': 1,
                    'last_warning': datetime.now()
                }
                await message.reply_text(
                    "⚠️ **WARNING:** Adult content is not allowed!\n"
                    "This is your first warning. Next violation will result in a mute."
                )
                return
            else:
                # Calculate mute duration
                duration = await get_mute_duration(user_id)
                
                # Mute the user
                success, result = await mute_user(client, chat_id, user_id, duration)
                
                if success:
                    await message.reply_text(
                        f"🚫 **MUTED:** User has been muted for {result} minutes for "
                        "repeatedly attempting to generate adult content."
                    )
                else:
                    await message.reply_text(f"Failed to mute user: {result}")
                return

        # Send typing action
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        
        # Send a message to inform the user to wait
        wait_message = await message.reply_text("🎨 Generating your image, please wait...")
        StartTime = time.time()

        # Updated Lexica API endpoint and headers
        url = "https://api.lexica.art/v2/generate"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        data = {
            "prompt": prompt,
            "model": "lexica",  # or "stable-diffusion"
            "width": 512,
            "height": 512,
            "guidance_scale": 7.5,
            "num_inference_steps": 50,
            "seed": int(time.time())  # Random seed
        }

        # Send request to the API
        response = requests.post(url, headers=headers, json=data, timeout=60)

        if response.status_code == 200:
            try:
                result = response.json()
                if 'images' in result and len(result['images']) > 0:
                    image_url = result['images'][0]['url']
                    
                    # Download the image
                    img_response = requests.get(image_url)
                    if img_response.status_code == 200:
                        # Save temporarily
                        with open('generated_image.jpg', 'wb') as f:
                            f.write(img_response.content)
                        
                        # Send the image
                        await message.reply_photo(
                            'generated_image.jpg',
                            caption=f"🎨 **Prompt:** {prompt}\n⏱️ **Time Taken:** {round(time.time() - StartTime, 1)}s"
                        )
                        
                        # Clean up
                        os.remove('generated_image.jpg')
                    else:
                        await wait_message.edit_text("❌ Failed to download the generated image.")
                else:
                    await wait_message.edit_text("❌ No image was generated.")
            except Exception as e:
                await wait_message.edit_text(f"❌ Error processing the image: {str(e)}")
        else:
            await wait_message.edit_text(f"❌ API Error: {response.status_code} - {response.text}")
        
        # Delete wait message if it still exists
        try:
            await wait_message.delete()
        except:
            pass

    except Exception as e:
        await message.reply_text(f"❌ An error occurred: {str(e)}")

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

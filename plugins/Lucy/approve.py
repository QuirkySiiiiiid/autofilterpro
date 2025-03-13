import os
import asyncio
from info import *
from pyrogram import Client, filters
from pyrogram.types import Message, User, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton
import random

# Default time before approving the request
APPROVAL_WAIT_TIME = 10  # seconds

@Client.on_chat_join_request((filters.group | filters.channel) & filters.chat(CHAT_ID) if CHAT_ID else (filters.group | filters.channel))
async def autoapprove(client, message: ChatJoinRequest):
    chat = message.chat
    user = message.from_user
    print(f"{user.first_name} requested to join {chat.title}")
    
    # Wait for the specified time before approving the request
    await asyncio.sleep(APPROVAL_WAIT_TIME)
    
    # Approve the join request
    await client.approve_chat_join_request(chat_id=chat.id, user_id=user.id)
    
    if APPROVED == "on":
        # Create a private invite link for the channel
        invite_link = await client.export_chat_invite_link(chat.id)
        
        # Create buttons with the invite link and updates channel link
        buttons = [
            [InlineKeyboardButton('• join Support •', url='https://t.me/+orrQTtRXjAgzNzQ1')],
            [InlineKeyboardButton(f'• ᴊᴏɪɴ {chat.title} •', url=invite_link)]
        ]
        markup = InlineKeyboardMarkup(buttons)
        caption = f"<b>ʜᴇʏ {user.mention()},\n\nʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {chat.title} ʜᴀs ʙᴇᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ.</b>"
        
        # Send a message with an image and buttons after approval
        await client.send_photo(
            chat_id=user.id,
            photo=random.choice(PICS),
            caption=caption,
            reply_markup=markup
        )

@Client.on_message(filters.command("reqtime") & filters.user(ADMINS))
async def set_reqtime(client, message: Message):
    global APPROVAL_WAIT_TIME
    
    # Check if the command has the right format and arguments
    if len(message.command) != 2 or not message.command[1].isdigit():
        await message.reply_text("Usage: /reqtime {seconds}")
        return
    
    # Update the approval wait time
    APPROVAL_WAIT_TIME = int(message.command[1])
    await message.reply_text(f"Request approval time has been set to {APPROVAL_WAIT_TIME} seconds.")

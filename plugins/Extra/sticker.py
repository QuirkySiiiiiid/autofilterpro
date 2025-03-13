from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio 
from bot import Bot

ANIMATION_FRAMES = ["● ○ ○", "● ● ○", "● ● ●"]
ANIMATION_INTERVAL = 0.05  # 100ms
AUTO_DELETE_TIME = 600  # 10 minutes

async def show_loading_animation(message: Message):
    """Shows an animated loading message and deletes it after completion."""
    try:
        loading_msg = await message.reply("○ ○ ○")
        await asyncio.sleep(2)  # Wait for 2 seconds
        await message.delete()  # Delete the /stickerid command message
        
        for _ in range(2):  # Run animation twice
            for frame in ANIMATION_FRAMES:
                await asyncio.sleep(ANIMATION_INTERVAL)
                await loading_msg.edit(frame)
        
        await asyncio.sleep(ANIMATION_INTERVAL)
        await loading_msg.delete()  # Delete animation message
    except Exception as e:
        print(f"Error in animation: {e}")
    
@Bot.on_message(filters.command("stickerid") & filters.private)
async def sticker_id(client: Bot, message: Message):
    """Handle /stickerid command with animation and sticker request."""
    await show_loading_animation(message)
    
    ask_msg = await client.send_message(
        chat_id=message.from_user.id,
        text="• ɴᴏᴡ ꜱᴇɴᴅ ᴍᴇ ʏᴏᴜʀ ꜱᴛɪᴄᴋᴇʀ!"
    )
    
    try:
        s_msg = await client.listen(message.chat.id, timeout=30)  # Wait for sticker
        if s_msg.sticker:
            info_text = (
                f"<b><i>❖ Sᴛɪᴄᴋᴇʀ Iɴғᴏʀᴍᴀᴛɪᴏɴ</b></i>\n\n"
                f"<blockquote expandable><b><i>⤷ Fɪʟᴇ ID:</b></i>\n<code>{s_msg.sticker.file_id}</code>\n\n"
                f"<b><i>⤷ Uɴɪᴏ̨ᴜᴇ ID:</b></i>\n<code>{s_msg.sticker.file_unique_id}</code>\n\n"
                f"<b><i>⤷ Dɪᴍᴇɴsɪᴏɴs:</b></i> {s_msg.sticker.width}x{s_msg.sticker.height}\n"
                f"<b><i>⤷ Fɪʟᴇ Sɪᴢᴇ:</b></i> {s_msg.sticker.file_size} bytes\n"
                f"<b><i>⤷ Aɴɪᴍᴀᴛᴇᴅ:</b></i> {'Yes' if s_msg.sticker.is_animated else 'No'}\n"
                f"<b><i>⤷ Vɪᴅᴇᴏ:</b></i> {'Yes' if s_msg.sticker.is_video else 'No'}<blockquote>"
            )
            
            buttons = [[InlineKeyboardButton("• ᴄʟᴏꜱᴇ •", callback_data="close_data")]]
            await s_msg.reply_text(info_text, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await s_msg.reply_text("<b><i>ᴏᴏᴘꜱ! ᴛʜᴀᴛ'ꜱ ɴᴏᴛ ᴀ ꜱᴛɪᴄᴋᴇʀ ꜰɪʟᴇ.</i></b>")
    except asyncio.TimeoutError:
        await ask_msg.edit("⏳<b><i>ᴛɪᴍᴇᴏᴜᴛ! ʏᴏᴜ ᴅɪᴅɴ'ᴛ ꜱᴇɴᴅ ᴀ ꜱᴛɪᴄᴋᴇʀ ɪɴ ᴛɪᴍᴇ.</i></b>")

@Bot.on_callback_query(filters.regex("^close_sticker$"))
async def close_callback(client, callback_query: CallbackQuery):
    try:
        await callback_query.message.delete()
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)


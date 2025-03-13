import os
import requests
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from bot import Bot
from helper_func import send_telegraph_log, check_user_ban
from telegraph import upload_file

def upload_image_requests(image_path):
    upload_url = "https://envs.sh"

    try:
        with open(image_path, 'rb') as file:
            files = {'file': file} 
            response = requests.post(upload_url, files=files)

            if response.status_code == 200:
                return response.text.strip() 
            else:
                return print(f"• Uᴘʟᴏᴀᴅ ғᴀɪʟᴇᴅ ᴡɪᴛʜ sᴛᴀᴛᴜs ᴄᴏᴅᴇ {response.status_code}")

    except Exception as e:
        print(f"Error during upload: {e}")
        return None

@Bot.on_message(filters.command("telegraph") & filters.private)
@check_user_ban
async def telegraph_upload(client: Bot, message: Message):
    try:
        # Send instruction message
        instruction = await message.reply_text(
            "• Pʟᴇᴀsᴇ sᴇɴᴅ ᴍᴇ ᴀ ᴘʜᴏᴛᴏ ᴏʀ ᴠɪᴅᴇᴏ ᴜɴᴅᴇʀ <b>5MB</b>.\n"
            "<i>Nᴏᴛᴇ: Vɪᴅᴇᴏ ᴛʜᴜᴍʙɴᴀɪʟs ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏ-ɢᴇɴᴇʀᴀᴛᴇᴅ</i>"
        )

        # Define media filter
        def media_filter(_, __, m):
            return bool(
                (m.photo or m.video) and 
                (not m.video or m.video.file_size < 5242880)
            )
            
        try:
            # Wait for media message
            media_msg = await client.listen(
                chat_id=message.chat.id,
                filters=filters.create(media_filter),
                timeout=30
            )

            if not media_msg:
                await instruction.edit_text("• Nᴏ ᴍᴇᴅɪᴀ ʀᴇᴄᴇɪᴠᴇᴅ. Pʀᴏᴄᴇss ᴄᴀɴᴄᴇʟʟᴇᴅ.")
                return

            # Show processing message
            processing_msg = await media_msg.reply_text("• Pʀᴏᴄᴇssɪɴɢ...")

            try:
                # Download and upload to telegraph
                if media_msg.photo or media_msg.video:
                    media_path = await media_msg.download()
                    try:
                        telegraph_url = upload_image_requests(media_path)
                        
                        # Send success message
                        await processing_msg.edit_text(
                            f"<b>Sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘʟᴏᴀᴅᴇᴅ!</b>\n\n"
                            f"<b>𝄽 Uʀʟ:</b> {telegraph_url}",
                            disable_web_page_preview=True
                        )
                        
                        # Send log
                        await send_telegraph_log(client, message.from_user, telegraph_url)
                        
                    except Exception as e:
                        await processing_msg.edit_text(f"Fᴀɪʟᴇᴅ ᴛᴏ ᴜᴘʟᴏᴀᴅ: {str(e)}")
                    finally:
                        try:
                            os.remove(media_path)
                        except:
                            pass
                else:
                    await processing_msg.edit_text("ツ Pʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ᴘʜᴏᴛᴏ ᴏʀ ᴠɪᴅᴇᴏ ғɪʟᴇ.")
            except Exception as e:
                await processing_msg.edit_text(f"An error occurred: {str(e)}")

        except TimeoutError:
            await instruction.edit_text("••Tɪᴍᴇᴏᴜᴛ! Pʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.••")
        except Exception as e:
            await instruction.edit_text(f"An error occurred: {str(e)}")

    except Exception as e:
        print(f"Telegraph command error: {e}")

@Bot.on_callback_query(filters.regex("^close$"))
async def close_callback(client, callback_query: CallbackQuery):
    try:
        await callback_query.message.delete()
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)
import requests
from pyrogram import Client, filters
import time
from pyrogram.enums import ChatAction, ParseMode
from pyrogram import filters
from MukeshAPI import api
@Client.on_message(filters.command(["chatgpt"],  prefixes=["+", ".", "/", "-", "?", "$","#","&"]))
async def chat_gpt(bot, message):

    try:
        await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        if len(message.command) < 2:
            await message.reply_text(
            "Example:**\n\n`/chatgpt How To Set Gf`")
        else:
            a = message.text.split(' ', 1)[1]
            r=api.gemini(a)["results"]
            await message.reply_text(f" {r} \n\n<blockquote>🎉ᴘᴏᴡᴇʀᴇᴅ ʙʏ @WilsonVerse </blockquote>", parse_mode=ParseMode.MARKDOWN)     
    except Exception as e:
        await message.reply_text(f"**ᴇʀʀᴏʀ: {e} ")
   
    
    # try:
    #     await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    #     if len(message.command) < 2:
    #         await message.reply_text(
    #         "<b>Example:</b>\n\n<code>/chatgpt How To Set Gf</code>")
    #     else:
    #         a = message.text.split(' ', 1)[1]
    #         response = api.gemini(a)
    #         if response is None:
    #             await message.reply_text("Sorry, I couldn't process your request. Please try again later.")
    #             return
    #         r = response.get("results", "No results found")
    #         await message.reply_text(f" {r} \n\n🎉ᴘᴏᴡᴇʀᴇᴅ ʙʏ @MoviessOk ", parse_mode=ParseMode.HTML)     
    # except Exception as e:
    #     await message.reply_text(f"<b>ᴇʀʀᴏʀ:</b> {e} ")

__mod_name__ = "Cʜᴀᴛɢᴘᴛ"
__help__ = """
 Cʜᴀᴛɢᴘᴛ ᴄᴀɴ ᴀɴsᴡᴇʀ ʏᴏᴜʀ ǫᴜᴇsᴛɪᴏɴ  ᴀɴᴅ sʜᴏᴡs ʏᴏᴜ ᴛʜᴇ ʀᴇsᴜʟᴛ

 ❍ /chatgpt  *:* ʀᴇᴘʟʏ ᴛo ᴍᴇssᴀɢᴇ ᴏʀ ɢɪᴠᴇ sᴏᴍᴇ ᴛᴇxᴛ
 
 """





# import requests
# from pyrogram import Client, filters
# import time
# from pyrogram.enums import ChatAction, ParseMode
# from pyrogram import filters
# from MukeshAPI import api
# @Client.on_message(filters.command(["chatgpt"],  prefixes=["+", ".", "/", "-", "?", "$","#","&"]))
# async def chat_gpt(bot, message):
    
#     try:
#         await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
#         if len(message.command) < 2:
#             await message.reply_text(
#             "Example:**\n\n`/chatgpt How To Set Gf`")
#         else:
#             a = message.text.split(' ', 1)[1]
#             r=api.gemini(a)["results"]
#             await message.reply_text(f" {r} \n\n🎉ᴘᴏᴡᴇʀᴇᴅ ʙʏ @Codeflix_Bots ", parse_mode=ParseMode.MARKDOWN)     
#     except Exception as e:
#         await message.reply_text(f"**ᴇʀʀᴏʀ: {e} ")

# __mod_name__ = "Cʜᴀᴛɢᴘᴛ"
# __help__ = """
#  Cʜᴀᴛɢᴘᴛ ᴄᴀɴ ᴀɴsᴡᴇʀ ʏᴏᴜʀ ǫᴜᴇsᴛɪᴏɴ  ᴀɴᴅ sʜᴏᴡs ʏᴏᴜ ᴛʜᴇ ʀᴇsᴜʟᴛ

#  ❍ /chatgpt  *:* ʀᴇᴘʟʏ ᴛo ᴍᴇssᴀɢᴇ ᴏʀ ɢɪᴠᴇ sᴏᴍᴇ ᴛᴇxᴛ
 
#  """

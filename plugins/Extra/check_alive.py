import time
import random
import asyncio
from pyrogram import Client, filters

CMD = ["/", "."]

# Funny stickers
STICKERS = [
    "CAACAgUAAxkBAAENwYVnqY6UNEdBZAk3KXRYPUCWl4qkegACdwUAAvQkqFdCRAQr6z-8oDYE",
    "CAACAgUAAxkBAAENwYNnqY6QsLz_PqRqo3RJVcm2yFsXiQACbAUAAlQ-MVW4EFTRYj1IwTYE",
    "CAACAgUAAxkBAAENwYFnqY6NDVHAx1XGSZ-0lqDRUkMGXQACSgYAAoL9MFWsh_VdlYxc8jYE",
    "CAACAgUAAxkBAAENwX9nqY6If2PK0y9Zi8Zlt43nvktrOQACNwIAAgRbQVXBqZwj9uwtTjYE",
    "CAACAgUAAxkBAAENwX1nqY2wtMmpwC8nVNR4Fsknd_nHfwACLggAAqNaIFSTNRxwL22HDzYE",
    "CAACAgUAAxkBAAENwXtnqY2k72zMSly_pcGN2OnNYHCDZwACcgYAAmIAAdFUtL9LS4LGuYA2BA",
    "CAACAgUAAxkBAAENwXlnqY2bZxMAAf4-s-mFR9bA4okbiX0AAucFAAJs3ClVei4OZ4pkcPI2BA",
    "CAACAgUAAxkBAAENwXdnqY2Sjkh6L4fU9NH2v8aEcmzdDQAC-QQAApBHyFSXVOscSiCvNjYE",
    "CAACAgUAAxkBAAENwXVnqY2Pw3WdAndjFQWQGG56tW4GUgAClAQAA7fRVF0YcA9ZmqHfNgQ",
    "CAACAgUAAxkBAAENwXFnqY1vEAAB4O_o2_mRPUA1Sr99CE4AAp4RAALTnqFW-xM0uS2Rf7g2BA",
    "CAACAgEAAxkBAAENwW9nqY1Vo0Az_klylY5sLtALfH6AdgACOQUAAge1yUUjLnzCznHWJTYE",
    "CAACAgEAAxkBAAENwWVnqY080pmx0wcHRnBlYD3GUttAhwACgwQAAmNkCEZvyl5GYnjL0TYE",
    "CAACAgEAAxkBAAENwWFnqY0s75lU7rrRY2nsm4NzPnx5VgACOgQAAhRN6EWFEmuNdV60kTYE",
    "CAACAgUAAxkBAAENn6Nnk2IQrwjfUy8nrq70WzqKbmD1XQAC6RAAAhMWCVehT6TBy7AMqzYE"
]

# Translations for /alive
ALIVE_CAPTIONS = [

"🔥 i'ᴍ ᴀʟɪᴠᴇ ᴀɴᴅ ʀᴇᴀᴅʏ ᴛᴏ ʀᴏʟʟ! 🚀",
"💀 tʜᴏᴜɢʜᴛ i ᴡᴀs ᴅᴇᴀᴅ? tʀʏ ʜᴀʀᴅᴇʀ! 😆",
"😎 sᴛɪʟʟ ʙʀᴇᴀᴋɪɴɢ, sᴛɪʟʟ ᴏᴘ!",
"🥳 i'ᴍ ᴜᴘ ᴀɴᴅ ᴋɪᴄᴋɪɴɢ! wʜᴀᴛ's ɴᴇxᴛ?",
"👀 cᴀɴ'ᴛ ʙᴇʟɪᴇᴠᴇ ɪᴛ? pɪɴᴄʜ ʏᴏᴜʀsᴇʟꜰ!",
"⚡ bᴀᴄᴋ ꜰʀᴏᴍ ᴛʜᴇ ᴅᴇᴀᴅ, ᴀɴᴅ sᴛʀᴏɴɢᴇʀ ᴛʜᴀɴ ᴇᴠᴇʀ! 💪",
"🎉 wʜᴏ sᴀɪᴅ i'ᴍ ɢᴏɴᴇ? i'ᴍ ᴊᴜsᴛ ɢᴇᴛᴛɪɴɢ sᴛᴀʀᴛᴇᴅ! 🚀",
"💥 tʜᴏᴜɢʜᴛ ʏᴏᴜ ᴄᴏᴜʟᴅ sᴛᴏᴘ ᴍᴇ? nɪᴄᴇ ᴛʀʏ! 😈",
"💡 lɪꜰᴇ's ᴛᴏᴏ sʜᴏʀᴛ ᴛᴏ sᴛᴀʏ ᴅᴏᴡɴ. Lᴇᴛ's ɢᴏ! 🌟",
"🔥 yᴏᴜ ᴄᴀɴ'ᴛ ʙʀᴇᴀᴋ ᴡʜᴀᴛ's ᴀʟʀᴇᴀᴅʏ ᴏɴ ꜰɪʀᴇ! 💯" 
]

# Translations for /ping
PING_CAPTIONS = [
"⚡ sᴘᴇᴇᴅ ᴛᴇsᴛ ɪɴɪᴛɪᴀᴛᴇᴅ...",
"🐌 is ᴛʜɪs ᴀ sɴᴀɪʟ ʀᴀᴄᴇ?",
"🚀 sᴇɴᴅɪɴɢ sɪɢɴᴀʟs ᴛᴏ ᴛʜᴇ ᴍᴏᴏɴ...",
"⌛ cᴀʟᴄᴜʟᴀᴛɪɴɢ... Wᴀɪᴛ, ᴅɪᴅ i ᴊᴜsᴛ ʟᴀɢ?",
"🔍 tᴇsᴛɪɴɢ ᴍʏ ʀᴇꜰʟᴇxᴇs!"
]

@Client.on_message(filters.command("alive", CMD) & filters.private)
@check_user_ban
async def check_alive(_, message):
    # Delete the command message
    try:
        await asyncio.sleep(1)
        await message.delete()
    except:
        pass

    # Send sticker and text
    sticker = random.choice(STICKERS)
    caption = random.choice(ALIVE_CAPTIONS)
    
    # Send sticker and text
    sticker_msg = await message.reply_sticker(sticker)
    text_msg = await message.reply_text(f"<b><i><blockquote>{caption}</b></i></blockquote>\n\nʙʏ @Moviess_Ok")
    
    # Wait for 10 seconds
    await asyncio.sleep(10)
    
    # Delete both messages
    try:
        await sticker_msg.delete()
        await text_msg.delete()
    except Exception as e:
        print(f"Error deleting messages: {e}")
        pass

@Client.on_message(filters.command("ping", CMD))
@check_user_ban
async def ping(_, message):
    start_t = time.time()
    rm = await message.reply_text("🏓 ᴘɪɴɢɪɴɢ...")
    end_t = time.time()
    
    time_taken_s = (end_t - start_t) * 1000
    caption = random.choice(PING_CAPTIONS)
    
    await rm.edit(f"🏓 ᴘᴏɴɢ!\n⏳ `{time_taken_s:.3f} ms`\n\n{caption}")
    
    # Wait for 10 seconds and delete both messages
    await asyncio.sleep(10)
    try:
        await asyncio.sleep(1)
        await message.delete()
        await rm.delete()
    except Exception as e:
        print(f"ᴇʀʀᴏʀ ᴅᴇʟᴇᴛɪɴɢ ᴘɪɴɢ ᴍᴇꜱꜱᴀɢᴇꜱ: {e}")
        pass

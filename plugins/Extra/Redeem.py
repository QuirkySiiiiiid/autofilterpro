from datetime import timedelta, datetime
import pytz
import string
import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.users_chats_db import db
from info import ADMINS, PREMIUM_LOGS
from utils import get_seconds, temp

# Store codes in MongoDB instead of memory
async def store_redeem_code(code, time):
    await db.redeem_codes.insert_one({
        "code": code,
        "time": time,
        "created_at": datetime.now(pytz.utc)
    })

async def get_redeem_code(code):
    return await db.redeem_codes.find_one_and_delete({"code": code})

def generate_code(length=10):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for _ in range(length))

@Client.on_message(filters.command("add_redeem") & filters.user(ADMINS))
async def add_redeem_code(client, message):
    if len(message.command) == 3:
        try:
            time = message.command[1]
            num_codes = int(message.command[2])
        except ValueError:
            await message.reply_text("Please provide a valid number of codes to generate.")
            return

        codes = []
        for _ in range(num_codes):
            code = generate_code()
            await store_redeem_code(code, time)  # Store in MongoDB
            codes.append(code)

        codes_text = '\n'.join(f"➔ <code>/redeem {code}</code>" for code in codes)
        text = f"""
            <b>🎉 <u>Gɪғᴛᴄᴏᴅᴇ Gᴇɴᴇʀᴀᴛᴇᴅ ✅</u></b>

            <b> <u>Tᴏᴛᴀʟ ᴄᴏᴅᴇ:</u></b> {num_codes}

            {codes_text}

            <b>⏳ <u>Duration:</u></b> {time}

            🌟<u>𝗥𝗲𝗱𝗲𝗲𝗺 𝗖𝗼𝗱𝗲 𝗜𝗻𝘀𝘁𝗿𝘂𝗰𝘁𝗶𝗼𝗻</u>🌟

            <b> <u>Click on the code above</u> to copy it instantly!</b>
            <b> <u>Send the copied code to the bot</u>\n to unlock your premium features!</b>

            <b>🚀 Enjoy your premium access! 🔥</u></b>
            """
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔑 Redeem Now 🔥", url=f"https://t.me/{temp.U_NAME}")]])
        await message.reply_text(text, reply_markup=keyboard)
    else:
        await message.reply_text("<b>♻ Usage:\n\n➩ <code>/add_redeem 1min 1</code>,\n➩ <code>/add_redeem 1hour 10</code>,\n➩ <code>/add_redeem 1day 5</code></b>")

@Client.on_message(filters.command("redeem"))
async def redeem_code(client, message):
    user_id = message.from_user.id
    if len(message.command) != 2:
        await message.reply_text("Usage: /redeem <code>")
        return

    redeem_code = message.command[1]
    code_data = await get_redeem_code(redeem_code)
    
    if not code_data:
        await message.reply_text("Invalid Redeem Code or Expired.")
        return

    try:
        time = code_data["time"]
        user = await client.get_users(user_id)
        seconds = await get_seconds(time)
        
        if seconds <= 0:
            await message.reply_text("Invalid time format in redeem code.")
            return

        data = await db.get_user(user_id)
        current_expiry = data.get("expiry_time") if data else None
        now_aware = datetime.now(pytz.utc)

        if current_expiry:
            current_expiry = current_expiry.replace(tzinfo=pytz.utc)
            if current_expiry > now_aware:
                expiry_str_in_ist = current_expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ Expiry Time: %I:%M:%S %p")
                await message.reply_text(
                    f"🚫 <b>You already have active premium access!</b>\n\n"
                    f"⏳ <b>Current Premium Expiry:</b> {expiry_str_in_ist}\n\n"
                    f"<i>You cannot redeem another code until your current premium access expires.</i>"
                )
                return

        expiry_time = now_aware + timedelta(seconds=seconds)
        await db.update_user({"id": user_id, "expiry_time": expiry_time})

        expiry_str_in_ist = expiry_time.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ Expiry Time: %I:%M:%S %p")
        success_text = f"""
🎉 <b>Premium activated successfully! 🚀</b>

👤 <b>User:</b> {user.mention}
⚡ <b>User ID:</b> <code>{user_id}</code>
⏳ <b>Premium Access Duration:</b> <code>{time}</code>
⌛️ <b>Expiry Date:</b> {expiry_str_in_ist}
"""
        await message.reply_text(success_text)

        if PREMIUM_LOGS:
            await client.send_message(PREMIUM_LOGS, f"#Redeem_Premium 🔓\n\n{success_text}")

    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")

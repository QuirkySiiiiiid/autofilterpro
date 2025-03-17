from datetime import timedelta, datetime
import pytz
import string
import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.users_chats_db import db
from info import ADMINS, PREMIUM_LOGS
from utils import get_seconds, temp


REDEEM_CODE = {}

def generate_code(length=10):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for _ in range(length))

# Store redeem code in MongoDB
async def store_redeem_code(code, time):
    await db.redeem_codes.insert_one({
        "code": code,
        "time": time,
        "created_at": datetime.now(pytz.utc)
    })

async def get_redeem_code(code):
    return await db.redeem_codes.find_one_and_delete({"code": code})

@Client.on_message(filters.command("add_redeem"))
async def add_redeem_code(client, message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.reply_text("🚫 This command is restricted to admins only.")
        return
        
    if len(message.command) == 3:
        try:
            time = message.command[1]
            num_codes = int(message.command[2])
        except ValueError:
            await message.reply_text("❌ Invalid input! Please provide a number of codes.")
            return

        codes = []
        for _ in range(num_codes):
            code = generate_code()
            await store_redeem_code(code, time)  # Store in MongoDB
            codes.append(code)

        codes_text = '\n'.join(f"➔ <code>/redeem {code}</code>" for code in codes)
        text = f"""
        <b>🎉 <u>Gift Codes Generated ✅</u></b>
        <b>🔢 Total Codes:</b> {num_codes}

        ⤷ {codes_text}

        <b>⏳ Duration:</b> {time}

        🌟 <b>Redeem Instructions:</b>
        ➤ Click the code to copy it.
        ➤ Send the copied code to the bot to unlock premium!

        🚀 Enjoy your premium access! 🔥    """
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔑 Redeem Now 🔥", url=f"https://t.me/{temp.U_NAME}")]])
        await message.reply_text(text, reply_markup=keyboard)
    else:
        await message.reply_text("<b>♻ Usage:\n\n⤷ <code>/add_redeem 1min 1</code>,\n⤷ <code>/add_redeem 1hour 10</code>,\n⤷ <code>/add_redeem 1day 5</code></b>")

@Client.on_message(filters.command("redeem"))
async def redeem_code(client, message):
    user_id = message.from_user.id
    if len(message.command) == 2:
        redeem_code = message.command[1]

        code_data = await get_redeem_code(redeem_code)
        if code_data:
            try:
                time = code_data["time"]
                user = await client.get_users(user_id)
                try:
                    seconds = await get_seconds(time)
                except Exception:
                    await message.reply_text("Invalid time format in redeem code.")
                    return
                if seconds > 0:
                    data = await db.get_user(user_id)
                    current_expiry = data.get("expiry_time") if data else None
                    now_aware = datetime.now(pytz.utc)

                    if current_expiry:
                        current_expiry = current_expiry.replace(tzinfo=pytz.utc)
                    if current_expiry and current_expiry > now_aware:
                        expiry_str_in_ist = current_expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ Expiry Time: %I:%M:%S %p")
                        await message.reply_text(
                            f"🚫 <b>You already have an active premium subscription!</b>\n\n"
                            f"⏳ <b>Current Premium Expiry:</b> {expiry_str_in_ist}\n\n"
                            f"<i>You cannot redeem another code until your current premium access expires.</i>\n\n"
                            f"<b>Thank you for using our service! 🔥</b>",
                            disable_web_page_preview=True
                        )
                        return
                    expiry_time = now_aware + timedelta(seconds=seconds)
                    user_data = {"id": user_id, "expiry_time": expiry_time}
                    await db.update_user(user_data)

                    expiry_str_in_ist = expiry_time.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ Expiry Time: %I:%M:%S %p")
                    await message.reply_photo(
                        photo="https://i.ibb.co/BVLLb42X/Black-and-White-Simple-Minimalist-Special-Gift-Voucher-Certificate.jpg",  # Replace with actual image URL
                        caption=f"<blockquote expandable>🎉 <b>Premium activated successfully! 🚀</b>\n\n"
                                f"👤 <b>User:</b> {user.mention}\n"
                                f"⚡ <b>User ID:</b> <code>{user_id}</code>\n"
                                f"⏳ <b>Premium Access Duration:</b> <code>{time}</code>\n"
                                f"⌛️ <b>Expiry Date:</b> {expiry_str_in_ist}</blockquote>",
                        disable_web_page_preview=True
                    )
                    log_message = f"""#Redeem_Premium 🔓
                    👤 <b>User:</b> {user.mention}
                    ⚡ <b>User ID:</b> <code>{user_id}</code>
                    ⏳ <b>Premium Access Duration:</b> <code>{time}</code>
                    ⌛️ <b>Expiry Date:</b> {expiry_str_in_ist}

                    <blockquote>🎉 Premium activated successfully! 🚀</blockquote>"""
                    await client.send_message(
                        PREMIUM_LOGS,
                        text=log_message,
                        disable_web_page_preview=True
                    )
                else:
                    await message.reply_text("Invalid time format in redeem code.")
            except Exception as e:
                await message.reply_text(f"An error occurred while redeeming the code: {e}")
        else:
            await message.reply_text("❌ Invalid Redeem Code or Expired.")
    else:
        await message.reply_text("Usage: /redeem <code>")

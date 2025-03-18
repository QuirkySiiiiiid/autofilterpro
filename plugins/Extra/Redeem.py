from datetime import timedelta, datetime
import pytz
import string
import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.users_chats_db import db
from info import ADMINS, PREMIUM_LOGS
from utils import get_seconds, temp

PREMIUM_IMAGE = "https://i.ibb.co/BVLLb42X/Black-and-White-Simple-Minimalist-Special-Gift-Voucher-Certificate.jpg"


# MongoDB collections
async def store_redeem_code(code, time, admin_id):
    await db.redeem_codes.insert_one({
        "code": code,
        "time": time,
        "used_by": [],  # Track who used the code
        "created_by": admin_id,
        "created_at": datetime.now(pytz.utc),
        "active": True
    })

async def get_redeem_code(code):
    return await db.redeem_codes.find_one({"code": code, "active": True})

async def mark_code_used(code, user_id):
    await db.redeem_codes.update_one(
        {"code": code},
        {"$push": {"used_by": user_id}}
    )

async def get_user_cooldown(user_id):
    return await db.redeem_cooldown.find_one({"user_id": user_id})

async def set_user_cooldown(user_id):
    cooldown_time = datetime.now(pytz.utc) + timedelta(minutes=10)
    await db.redeem_cooldown.update_one(
        {"user_id": user_id},
        {"$set": {"cooldown_until": cooldown_time}},
        upsert=True
    )

def generate_code(length=10):
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if not (set('0O1I') & set(code)):  # Avoid confusing characters
            return code

@Client.on_message(filters.command("add_redeem") & filters.user(ADMINS))
async def add_redeem_code(client, message):
    if len(message.command) == 3:
        try:
            time = message.command[1]
            num_codes = int(message.command[2])
            if num_codes > 100:  # Limit number of codes
                await message.reply_text("Maximum 100 codes can be generated at once.")
                return
        except ValueError:
            await message.reply_text("Please provide a valid number of codes.")
            return

        codes = []
        for _ in range(num_codes):
            code = generate_code()
            await store_redeem_code(code, time, message.from_user.id)
            codes.append(code)

        codes_text = '\n'.join(f"┃  🎟️ <code>/redeem {code}</code>" for code in codes)
        text = f"""
┏━━━━━ PREMIUM CODES ━━━━━┓
┃                         ┃
{codes_text}
┃                         ┃
┃  ⏳ Duration: {time}    ┃
┃  📊 Total: {num_codes}  ┃
┃                         ┃
┗━━━━━━━━━━━━━━━━━━━━━━━┛

🔰 Instructions:
• Each code can be used once
• 10 minute cooldown between redeems
• Codes are case-sensitive
"""
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔑 Redeem Now", url=f"https://t.me/{temp.U_NAME}")
        ]])
        
        await message.reply_text(text, reply_markup=keyboard)
        
        # Log code generation
        if PREMIUM_LOGS:
            await client.send_message(PREMIUM_LOGS, 
                f"#NEW_CODES_GENERATED\n\n"
                f"Admin: {message.from_user.mention}\n"
                f"Count: {num_codes}\n"
                f"Duration: {time}\n\n"
                f"{text}"
            )
    else:
        await message.reply_text(
            "<b>♻️ Usage:</b>\n\n"
            "➜ <code>/add_redeem 1min 1</code>\n"
            "➜ <code>/add_redeem 1hour 10</code>\n"
            "➜ <code>/add_redeem 1day 5</code>"
        )

@Client.on_message(filters.command("redeem"))
async def redeem_code(client, message):
    user_id = message.from_user.id
    
    if len(message.command) != 2:
        await message.reply_text("Usage: /redeem <code>")
        return

    # Check cooldown
    cooldown = await get_user_cooldown(user_id)
    if cooldown and cooldown["cooldown_until"] > datetime.now(pytz.utc):
        remaining = (cooldown["cooldown_until"] - datetime.now(pytz.utc)).seconds
        await message.reply_text(f"Please wait {remaining//60}m {remaining%60}s before trying again.")
        return

    redeem_code = message.command[1].strip()
    code_data = await get_redeem_code(redeem_code)
    
    if not code_data:
        await message.reply_text("❌ Invalid or expired code.")
        return
        
    if user_id in code_data["used_by"]:
        await message.reply_text("❌ You have already used this code.")
        return

    try:
        time = code_data["time"]
        user = await client.get_users(user_id)
        seconds = await get_seconds(time)
        
        if seconds <= 0:
            await message.reply_text("❌ Invalid time format in code.")
            return

        # Check current premium status
        data = await db.get_user(user_id)
        current_expiry = data.get("expiry_time") if data else None
        now_aware = datetime.now(pytz.utc)

        if current_expiry and current_expiry.replace(tzinfo=pytz.utc) > now_aware:
            expiry_str = current_expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M:%S %p")
            await message.reply_text(
                "┏━━━ PREMIUM ACTIVE ━━━┓\n"
                f"┃ Current expiry: {expiry_str} ┃\n"
                "┗━━━━━━━━━━━━━━━━━━━┛\n\n"
                "❌ Cannot redeem while premium is active."
            )
            return

        # Activate premium
        expiry_time = now_aware + timedelta(seconds=seconds)
        await db.update_user({"id": user_id, "expiry_time": expiry_time})
        await mark_code_used(redeem_code, user_id)
        await set_user_cooldown(user_id)

        expiry_str = expiry_time.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M:%S %p")
        success_text = f"""
┏━━━━ PREMIUM ACTIVATED ━━━━┓
┃                           ┃
┃  👤 User: {user.mention}  ┃
┃  🆔 ID: {user_id}         ┃
┃  ⏳ Duration: {time}      ┃
┃  📅 Expires: {expiry_str} ┃
┃                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""
        # Send success message with image
        if PREMIUM_IMAGE:  # Add PREMIUM_IMAGE to your config
            await message.reply_photo(
                photo=PREMIUM_IMAGE,
                caption=success_text
            )
        else:
            await message.reply_text(success_text)

        # Log redemption
        if PREMIUM_LOGS:
            await client.send_message(
                PREMIUM_LOGS,
                f"#PREMIUM_ACTIVATED\n\n{success_text}"
            )

    except Exception as e:
        await message.reply_text(f"❌ An error occurred: {str(e)}")

# Admin commands
@Client.on_message(filters.command("list_codes") & filters.user(ADMINS))
async def list_codes(client, message):
    codes = await db.redeem_codes.find({"active": True}).to_list(None)
    if not codes:
        await message.reply_text("No active codes found.")
        return
    
    text = "┏━━━ ACTIVE CODES ━━━┓\n"
    for code in codes:
        used = len(code["used_by"])
        text += f"┃ Code: {code['code']}\n┃ Used: {used} time(s)\n┃ Duration: {code['time']}\n┃ ─────────────── ┃\n"
    text += "┗━━━━━━━━━━━━━━━━━┛"
    
    await message.reply_text(text)

@Client.on_message(filters.command("revoke_code") & filters.user(ADMINS))
async def revoke_code(client, message):
    if len(message.command) != 2:
        await message.reply_text("Usage: /revoke_code <code>")
        return
        
    code = message.command[1]
    result = await db.redeem_codes.update_one(
        {"code": code, "active": True},
        {"$set": {"active": False}}
    )
    
    if result.modified_count > 0:
        await message.reply_text(f"✅ Code {code} has been revoked.")
    else:
        await message.reply_text("❌ Code not found or already revoked.")

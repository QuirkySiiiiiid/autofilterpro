from motor.motor_asyncio import AsyncIOMotorCollection
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

# Database Collections
redeem_codes: AsyncIOMotorCollection = db["redeem_codes"]
redeem_cooldown: AsyncIOMotorCollection = db["redeem_cooldown"]
users: AsyncIOMotorCollection = db["users"]

async def init_database():
    """Initialize database indexes"""
    try:
        # Create indexes
        await redeem_codes.create_index("code", unique=True)
        await redeem_codes.create_index("created_at", expireAfterSeconds=7*24*60*60)
        await redeem_cooldown.create_index("user_id", unique=True)
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

async def store_redeem_code(code: str, time: str, admin_id: int) -> bool:
    """Store a new redeem code"""
    try:
        await redeem_codes.insert_one({
            "code": code,
            "time": time,
            "used_by": [],
            "created_by": admin_id,
            "created_at": datetime.now(pytz.utc),
            "active": True
        })
        return True
    except Exception as e:
        print(f"Error storing code: {e}")
        return False

async def get_redeem_code(code: str):
    """Get redeem code details"""
    try:
        return await redeem_codes.find_one({"code": code, "active": True})
    except Exception as e:
        print(f"Error getting code: {e}")
        return None

async def mark_code_used(code: str, user_id: int) -> bool:
    """Mark a code as used by a user"""
    try:
        result = await redeem_codes.update_one(
            {"code": code, "active": True},
            {"$addToSet": {"used_by": user_id}}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"Error marking code used: {e}")
        return False

async def get_user_cooldown(user_id: int):
    """Get user's cooldown status"""
    try:
        return await redeem_cooldown.find_one({"user_id": user_id})
    except Exception as e:
        print(f"Error getting cooldown: {e}")
        return None

async def set_user_cooldown(user_id: int) -> bool:
    """Set cooldown for a user"""
    try:
        cooldown_time = datetime.now(pytz.utc) + timedelta(minutes=10)
        await redeem_cooldown.update_one(
            {"user_id": user_id},
            {"$set": {"cooldown_until": cooldown_time}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error setting cooldown: {e}")
        return False

def generate_code(length=12):
    """Generate a unique redeem code"""
    chars = string.ascii_uppercase + string.digits
    while True:
        random_part = ''.join(random.choice(chars) for _ in range(length))
        if not (set('0O1I') & set(random_part)):
            return f"ROBIN-{random_part}"

# Add these database verification functions
async def verify_db_collections():
    try:
        collections = await db.list_collection_names()
        required = ['redeem_codes', 'redeem_cooldown']
        for collection in required:
            if collection not in collections:
                await db[collection].create_index("created_at", expireAfterSeconds=7*24*60*60)  # 7 days TTL
        return True
    except Exception as e:
        print(f"Database verification failed: {e}")
        return False

async def verify_code_storage(code, time, admin_id):
    try:
        await store_redeem_code(code, time, admin_id)
        # Verify storage
        stored_code = await redeem_codes.find_one({"code": code})
        if not stored_code:
            raise Exception("Code storage verification failed")
        return True
    except Exception as e:
        print(f"Code storage failed: {e}")
        return False

@Client.on_message(filters.command("add_redeem") & filters.user(ADMINS))
async def add_redeem_code(client, message):
    try:
        # Initialize database first
        if not await init_database():
            await message.reply_text("❌ Database initialization failed. Please contact administrator.")
            return

        if len(message.command) != 3:
            await message.reply_text(
                "<b>♻️ Usage:</b>\n\n"
                "➜ <code>/add_redeem 1min 1</code>\n"
                "➜ <code>/add_redeem 1hour 10</code>\n"
                "➜ <code>/add_redeem 1day 5</code>"
            )
            return

        time = message.command[1]
        try:
            num_codes = int(message.command[2])
            if num_codes > 100:
                await message.reply_text("❌ Maximum 100 codes can be generated at once.")
                return
            if num_codes < 1:
                await message.reply_text("❌ Number of codes must be at least 1.")
                return
        except ValueError:
            await message.reply_text("❌ Please provide a valid number of codes.")
            return

        # Validate time format
        try:
            seconds = await get_seconds(time)
            if seconds <= 0:
                await message.reply_text("❌ Invalid time format.")
                return
        except Exception:
            await message.reply_text("❌ Invalid time format. Use format like: 1hour, 1day, etc.")
            return

        status_msg = await message.reply_text("⏳ Generating premium codes...")
        
        try:
            codes = []
            failed_codes = []
            for _ in range(num_codes):
                code = generate_code()
                if await verify_code_storage(code, time, message.from_user.id):
                    codes.append(code)
                else:
                    failed_codes.append(code)

            if not codes:
                await status_msg.edit_text("❌ Failed to generate any valid codes. Database error.")
                return

            if failed_codes:
                print(f"Failed to store codes: {failed_codes}")

            codes_text = '\n'.join(f"┃  🎟️ <code>/redeem {code}</code>" for code in codes)
            text = f"""
┏━━━━━ PREMIUM CODES ━━━━━┓
┃                         ┃
{codes_text}
┃                         ┃
┃  ⏳ Duration: {time}    ┃
┃  📊 Generated: {len(codes)}/{num_codes}  ┃
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
            
            await status_msg.edit_text(text, reply_markup=keyboard)
            
            # Log code generation
            if PREMIUM_LOGS:
                try:
                    await client.send_message(
                        PREMIUM_LOGS,
                        f"#NEW_CODES_GENERATED\n\n"
                        f"Admin: {message.from_user.mention}\n"
                        f"Count: {num_codes}\n"
                        f"Duration: {time}\n\n"
                        f"{text}"
                    )
                except Exception as e:
                    print(f"Failed to log to PREMIUM_LOGS: {str(e)}")
                    
        except Exception as e:
            await status_msg.edit_text(f"❌ Error generating codes: {str(e)}")
            
    except Exception as e:
        await message.reply_text(f"❌ An unexpected error occurred: {str(e)}")

@Client.on_message(filters.command("redeem"))
async def redeem_code(client, message):
    try:
        # Verify database first
        if not await verify_db_collections():
            await message.reply_text("❌ Database verification failed. Please contact administrator.")
            return

        user_id = message.from_user.id
        
        if len(message.command) != 2:
            await message.reply_text("❌ Usage: /redeem <code>")
            return

        status_msg = await message.reply_text("⏳ Processing your redeem request...")

        # Check cooldown with verification
        try:
            cooldown = await get_user_cooldown(user_id)
            if cooldown:
                # Verify cooldown data
                if not isinstance(cooldown.get("cooldown_until"), datetime):
                    await redeem_cooldown.delete_one({"user_id": user_id})
                    cooldown = None
                
            if cooldown and cooldown["cooldown_until"] > datetime.now(pytz.utc):
                remaining = (cooldown["cooldown_until"] - datetime.now(pytz.utc)).seconds
                await status_msg.edit_text(f"⏳ Please wait {remaining//60}m {remaining%60}s before trying again.")
                return
        except Exception as e:
            print(f"Cooldown check error: {str(e)}")

        redeem_code = message.command[1].strip().upper()
        try:
            code_data = await get_redeem_code(redeem_code)
        except Exception as e:
            await status_msg.edit_text(f"❌ Database error: {str(e)}")
            return
        
        if not code_data:
            await status_msg.edit_text("❌ Invalid or expired code.")
            return
            
        if user_id in code_data["used_by"]:
            await status_msg.edit_text("❌ You have already used this code.")
            return

        try:
            time = code_data["time"]
            user = await client.get_users(user_id)
            seconds = await get_seconds(time)
            
            if seconds <= 0:
                await status_msg.edit_text("❌ Invalid time format in code.")
                return

            # Check current premium status
            data = await users.find_one({"id": user_id})
            current_expiry = data.get("expiry_time") if data else None
            now_aware = datetime.now(pytz.utc)

            if current_expiry and current_expiry.replace(tzinfo=pytz.utc) > now_aware:
                expiry_str = current_expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y %I:%M:%S %p")
                await status_msg.edit_text(
                    "┏━━━ PREMIUM ACTIVE ━━━┓\n"
                    f"┃ Current expiry: {expiry_str} ┃\n"
                    "┗━━━━━━━━━━━━━━━━━━━┛\n\n"
                    "❌ Cannot redeem while premium is active."
                )
                return

            # Activate premium
            expiry_time = now_aware + timedelta(seconds=seconds)
            await users.update_one({"id": user_id}, {"$set": {"expiry_time": expiry_time}})
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
            try:
                # Send success message with image
                if PREMIUM_IMAGE:
                    await message.reply_photo(
                        photo=PREMIUM_IMAGE,
                        caption=success_text
                    )
                else:
                    await message.reply_text(success_text)
                
                await status_msg.delete()
            except Exception as e:
                await status_msg.edit_text(f"Premium activated but failed to send confirmation: {str(e)}")

            # Log redemption
            if PREMIUM_LOGS:
                try:
                    await client.send_message(
                        PREMIUM_LOGS,
                        f"#PREMIUM_ACTIVATED\n\n{success_text}"
                    )
                except Exception as e:
                    print(f"Failed to log to PREMIUM_LOGS: {str(e)}")

            # Add verification for premium activation
            try:
                # Verify user update
                await users.update_one({"id": user_id}, {"$set": {"expiry_time": expiry_time}})
                verify_update = await users.find_one({"id": user_id})
                if not verify_update or not verify_update.get("expiry_time"):
                    raise Exception("Failed to verify premium activation")

                # Verify code usage marking
                await mark_code_used(redeem_code, user_id)
                verify_code = await get_redeem_code(redeem_code)
                if user_id not in verify_code.get("used_by", []):
                    raise Exception("Failed to verify code usage marking")

                # Verify cooldown setting
                await set_user_cooldown(user_id)
                verify_cooldown = await get_user_cooldown(user_id)
                if not verify_cooldown:
                    raise Exception("Failed to verify cooldown setting")

            except Exception as e:
                await status_msg.edit_text(f"❌ Error verifying premium activation: {str(e)}")
                return

        except Exception as e:
            await status_msg.edit_text(f"❌ Error processing redemption: {str(e)}")

    except Exception as e:
        await message.reply_text(f"❌ An unexpected error occurred: {str(e)}")

# Admin commands
@Client.on_message(filters.command("list_codes") & filters.user(ADMINS))
async def list_codes(client, message):
    codes = await redeem_codes.find({"active": True}).to_list(None)
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
    result = await redeem_codes.update_one(
        {"code": code, "active": True},
        {"$set": {"active": False}}
    )
    
    if result.modified_count > 0:
        await message.reply_text(f"✅ Code {code} has been revoked.")
    else:
        await message.reply_text("❌ Code not found or already revoked.")

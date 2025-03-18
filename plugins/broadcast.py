import datetime, time, os, asyncio,logging 
from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong, PeerIdInvalid
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters, enums
from database.users_chats_db import db
from info import ADMINS, GRP_LNK
from itertools import cycle

# Loading animation frames
LOADING_CHARS = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
loading_animation = cycle(LOADING_CHARS)

def get_progress_bar(current, total, length=10):
    progress = (current / total) * length
    filled = int(progress)
    remaining = length - filled
    percent = (current / total) * 100
    return f"[{'█' * filled}{'░' * remaining}] {percent:.1f}% {next(loading_animation)}"

async def update_progress_message(message, current, total, stats):
    try:
        progress_text = get_progress_bar(current, total)
        status_text = f"""
<b>⚡ Broadcast Status</b>

<code>{progress_text}</code>

<b>💫 Progress:</b> <code>{current}/{total}</code>
<b>✅ Successful:</b> <code>{stats['successful']}</code>
<b>🚫 Blocked:</b> <code>{stats['blocked']}</code>
<b>🗑 Deleted:</b> <code>{stats['deleted']}</code>
<b>❌ Failed:</b> <code>{stats['failed']}</code>

<i>Processing...</i>
"""
        await message.edit(status_text)
    except Exception as e:
        print(f"Error updating progress: {e}")

async def pin_broadcast_message(client, user_ids, message):
    """Pin broadcast message for all successful users silently"""
    pinned = 0
    failed = 0
    
    for user_id in user_ids:
        try:
            sent_msg = await message.copy(chat_id=user_id)
            await sent_msg.pin(disable_notification=True)  # Silent pin
            pinned += 1
            await asyncio.sleep(0.1)  # Prevent flooding
        except Exception as e:
            print(f"Failed to pin for {user_id}: {str(e)}")
            failed += 1
    
    return pinned, failed

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast_handler(bot, message):
    """Broadcast to all users with pin option"""
    users = await db.get_all_users()
    reply_message = message.reply_to_message
    
    if not reply_message:
        return await message.reply_text("❌ Please reply to a message to broadcast!")

    # Initialize broadcast
    start_time = datetime.datetime.now()
    status_msg = await message.reply_text("⚡ Initializing broadcast...")
    
    total_users = await db.total_users_count()
    done = 0
    successful_users = []  # Store successful user IDs
    stats = {
        "successful": 0,
        "blocked": 0,
        "deleted": 0,
        "failed": 0
    }
    
    async for user in users:
        try:
            pti, sh = await broadcast_messages(int(user['id']), reply_message, None)
            if pti:
                stats['successful'] += 1
                successful_users.append(int(user['id']))
            else:
                if sh == "Deleted/Blocked":
                    stats['blocked'] += 1
                else:
                    stats['failed'] += 1
            
            done += 1
            if not done % 20:  # Update every 20 messages
                await update_progress_message(status_msg, done, total_users, stats)
                
        except Exception as e:
            stats['failed'] += 1
            print(f"Broadcast Error: {e}")
        
        await asyncio.sleep(0.1)

    time_taken = datetime.datetime.now() - start_time
    
    # Final status with pin option
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📌 Pin Broadcast", callback_data="pin_broadcast")],
        [InlineKeyboardButton("❌ Close", callback_data="close_broadcast")]
    ])
    
    final_status = f"""
<b>✅ Broadcast Completed!</b>

[██████████] 100% ✓

<b>⏰ Time Taken:</b> <code>{time_taken.seconds} seconds</code>
<b>👥 Total Users:</b> <code>{total_users}</code>
<b>✅ Successful:</b> <code>{stats['successful']}</code>
<b>🚫 Blocked:</b> <code>{stats['blocked']}</code>
<b>❌ Failed:</b> <code>{stats['failed']}</code>

<i>Use buttons below to pin broadcast or close this message.</i>
"""
    # Store context for pin operation
    context = {
        "successful_users": successful_users,
        "broadcast_message": reply_message
    }
    await status_msg.edit(final_status, reply_markup=buttons)
    return context

@Client.on_callback_query(filters.regex("^pin_broadcast"))
async def pin_broadcast_callback(bot, query):
    try:
        await query.answer("Starting to pin broadcast messages...")
        status_msg = await query.message.edit_text("📌 Pinning broadcast messages...", reply_markup=None)
        
        # Get context from stored data
        context = query.message.context  # You'll need to store this during broadcast
        
        pinned, failed = await pin_broadcast_message(
            bot,
            context["successful_users"],
            context["broadcast_message"]
        )
        
        await status_msg.edit(f"""
<b>📌 Broadcast Pin Complete!</b>

✅ Successfully Pinned: <code>{pinned}</code>
❌ Failed to Pin: <code>{failed}</code>

<i>Messages have been silently pinned.</i>
""")
    except Exception as e:
        await query.message.edit_text(f"❌ Error during pinning: {str(e)}")

@Client.on_callback_query(filters.regex("^close_broadcast"))
async def close_broadcast_callback(bot, query):
    try:
        await query.message.delete()
    except Exception as e:
        print(f"Error closing broadcast message: {str(e)}")

@Client.on_message(filters.command("groupcast") & filters.user(ADMINS) & filters.reply)
async def group_broadcast(bot, message):
    """Broadcast to all groups"""
    chats = await db.get_all_chats()
    reply_message = message.reply_to_message
    
    if not reply_message:
        return await message.reply_text("❌ Please reply to a message to broadcast!")

    # Initialize broadcast
    start_time = datetime.datetime.now()
    status_msg = await message.reply_text("⚡ Initializing group broadcast...")
    
    total_chats = await db.total_chat_count()
    done = 0
    stats = {
        "successful": 0,
        "blocked": 0,
        "deleted": 0,
        "failed": 0
    }
    
    async for chat in chats:
        try:
            pti, sh = await broadcast_messages(int(chat['id']), reply_message, None)
            if pti:
                stats['successful'] += 1
            else:
                if sh == "Deleted/Blocked":
                    stats['deleted'] += 1
                else:
                    stats['failed'] += 1
            
            done += 1
            if not done % 20:
                await update_progress_message(status_msg, done, total_chats, stats)
                
        except Exception as e:
            stats['failed'] += 1
            print(f"Group Broadcast Error: {e}")
        
        await asyncio.sleep(0.1)

    time_taken = datetime.datetime.now() - start_time
    
    final_status = f"""
<b>✅ Group Broadcast Completed!</b>

[██████████] 100% ✓

<b>⏰ Time Taken:</b> <code>{time_taken.seconds} seconds</code>
<b>👥 Total Groups:</b> <code>{total_chats}</code>
<b>✅ Successful:</b> <code>{stats['successful']}</code>
<b>🗑 Deleted:</b> <code>{stats['deleted']}</code>
<b>❌ Failed:</b> <code>{stats['failed']}</code>
"""
    await status_msg.edit(final_status)

@Client.on_message(filters.command("clear_junk") & filters.user(ADMINS))
async def remove_junkuser__db(bot, message):
    users = await db.get_all_users()
    b_msg = message 
    sts = await message.reply_text('<i>In Progress...</i>')   
    start_time = time.time()
    total_users = await db.total_users_count()
    blocked = 0
    deleted = 0
    failed = 0
    done = 0
    async for user in users:
        pti, sh = await clear_junk(int(user['id']), b_msg)
        if pti == False:
            if sh == "Blocked":
                blocked+=1
            elif sh == "Deleted":
                deleted += 1
            elif sh == "Error":
                failed += 1
        done += 1
        if not done % 20:
            await sts.edit(f"In Progress:\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nBlocked: {blocked}\nDeleted: {deleted}")    
    time_taken = datetime.timedelta(seconds=int(time.time()-start_time))
    await sts.delete()
    await bot.send_message(message.chat.id, f"Completed:\nCompleted in {time_taken} seconds.\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nBlocked: {blocked}\nDeleted: {deleted}")


@Client.on_message(filters.command("grp_broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast_group(bot, message):
    groups = await db.get_all_chats()
    if not groups:
        grp = await message.reply_text("❌ Nᴏ ɢʀᴏᴜᴘs ғᴏᴜɴᴅ ғᴏʀ ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ.")
        await asyncio.sleep(60)
        await grp.delete()
        return
    b_msg = message.reply_to_message
    sts = await message.reply_text(text='Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ ʏᴏᴜʀ ᴍᴇssᴀɢᴇs Tᴏ Gʀᴏᴜᴘs...')
    start_time = time.time()
    total_groups = await db.total_chat_count()
    done = 0
    failed = ""
    success = 0
    deleted = 0
    async for group in groups:
        pti, sh, ex = await broadcast_messages_group(int(group['id']), b_msg)
        if pti == True:
            if sh == "Succes":
                success += 1
        elif pti == False:
            if sh == "deleted":
                deleted+=1 
                failed += ex 
                try:
                    await bot.leave_chat(int(group['id']))
                except Exception as e:
                    print(f"{e} > {group['id']}")  
        done += 1
        if not done % 20:
            await sts.edit(f"Broadcast in progress:\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nSuccess: {success}\nDeleted: {deleted}")    
    time_taken = datetime.timedelta(seconds=int(time.time()-start_time))
    await sts.delete()
    try:
        await message.reply_text(f"Broadcast Completed:\nCompleted in {time_taken} seconds.\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nSuccess: {success}\nDeleted: {deleted}\n\nFiled Reson:- {failed}")
    except MessageTooLong:
        with open('reason.txt', 'w+') as outfile:
            outfile.write(failed)
        await message.reply_document('reason.txt', caption=f"Completed:\nCompleted in {time_taken} seconds.\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nSuccess: {success}\nDeleted: {deleted}")
        os.remove("reason.txt")

      
@Client.on_message(filters.command(["junk_group", "clear_junk_group"]) & filters.user(ADMINS))
async def junk_clear_group(bot, message):
    groups = await db.get_all_chats()
    if not groups:
        grp = await message.reply_text("❌ Nᴏ ɢʀᴏᴜᴘs ғᴏᴜɴᴅ ғᴏʀ ᴄʟᴇᴀʀ Jᴜɴᴋ ɢʀᴏᴜᴘs.")
        await asyncio.sleep(60)
        await grp.delete()
        return
    b_msg = message
    sts = await message.reply_text(text='..............')
    start_time = time.time()
    total_groups = await db.total_chat_count()
    done = 0
    failed = ""
    deleted = 0
    async for group in groups:
        pti, sh, ex = await junk_group(int(group['id']), b_msg)        
        if pti == False:
            if sh == "deleted":
                deleted+=1 
                failed += ex 
                try:
                    await bot.leave_chat(int(group['id']))
                except Exception as e:
                    print(f"{e} > {group['id']}")  
        done += 1
        if not done % 20:
            await sts.edit(f"in progress:\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nDeleted: {deleted}")    
    time_taken = datetime.timedelta(seconds=int(time.time()-start_time))
    await sts.delete()
    try:
        await bot.send_message(message.chat.id, f"Completed:\nCompleted in {time_taken} seconds.\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nDeleted: {deleted}\n\nFiled Reson:- {failed}")    
    except MessageTooLong:
        with open('junk.txt', 'w+') as outfile:
            outfile.write(failed)
        await message.reply_document('junk.txt', caption=f"Completed:\nCompleted in {time_taken} seconds.\n\nTotal Groups {total_groups}\nCompleted: {done} / {total_groups}\nDeleted: {deleted}")
        os.remove("junk.txt")

async def broadcast_messages_group(chat_id, message):
    try:
        await message.copy(chat_id=chat_id)
        return True, "Succes", 'mm'
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages_group(chat_id, message)
    except Exception as e:
        await db.delete_chat(int(chat_id))       
        logging.info(f"{chat_id} - PeerIdInvalid")
        return False, "deleted", f'{e}\n\n'
    
async def junk_group(chat_id, message):
    try:
        kk = await message.copy(chat_id=chat_id)
        await kk.delete(True)
        return True, "Succes", 'mm'
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await junk_group(chat_id, message)
    except Exception as e:
        await db.delete_chat(int(chat_id))       
        logging.info(f"{chat_id} - PeerIdInvalid")
        return False, "deleted", f'{e}\n\n'
    

async def clear_junk(user_id, message):
    try:
        key = await message.copy(chat_id=user_id)
        await key.delete(True)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await clear_junk(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"

async def broadcast_messages(user_id, message, reply_markup=None):
    try:
        await message.copy(chat_id=user_id,reply_markup=reply_markup)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await broadcast_messages(user_id, message,reply_markup=reply_markup)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"

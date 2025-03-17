import os
from gtts import gTTS
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from lexica import AsyncClient, languageModels, Messages
import random

def extract_content(response):
    try:
        if not response:
            return "Sorry, I received an empty response. Please try again."
            
        if isinstance(response, dict):
            # Handle different response structures
            if 'content' in response:
                content = response['content']
                # If content is a dictionary with 'parts'
                if isinstance(content, dict) and 'parts' in content:
                    return content['parts'][0]['text']
                # If content is a dictionary with 'text'
                if isinstance(content, dict) and 'text' in content:
                    return content['text']
                # If content is a string
                if isinstance(content, str):
                    return content
            # Try other common response structures
            if 'choices' in response and len(response['choices']) > 0:
                return response['choices'][0].get('text', str(response))
            if 'message' in response:
                return response['message']
            
        # If response is string, return as is
        if isinstance(response, str):
            return response
            
        # If we can't parse the response, return the string representation
        return str(response)
    except Exception as e:
        return f"Error parsing response: {str(e)}"

# Robin's characteristic phrases and mannerisms
ROBIN_INTROS = [
    "Fufufu... How interesting.",
    "Ara ara...",
    "My, my...",
    "How fascinating...",
    "*adjusts glasses* Hmm..."
]

ROBIN_ENDINGS = [
    "Perhaps the answers lie in the shadows of history...",
    "Just like the Poneglyphs, truth has many layers.",
    "Knowledge, like archaeology, requires patience and dedication.",
    "The world holds many mysteries, doesn't it?",
    "Sometimes the darkest chapters hold the brightest insights."
]

ROBIN_NO_QUERY_RESPONSES = [
    f"📚 *chuckles* As an archaeologist and scholar, I find curiosity to be humanity's most endearing trait. What knowledge do you seek?",
    "🗿 The Poneglyphs taught me that every question leads to a deeper understanding. What would you like to know?",
    "🌺 *sprouting a hand with a book* Knowledge is like the petals of a flower, each one revealing a new truth. Shall we explore together?",
    "📜 Even the darkest corners of history hold valuable lessons. What mysteries shall we uncover?",
    "🎭 *adjusts glasses* In my years of study, I've learned that every question is worth asking. What's on your mind?"
]

@Client.on_message(filters.command(["obin"], prefixes=["R", "r"]))
async def robin_handler(client: Client, message: Message):
    try:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        name = message.from_user.first_name or "Nakama"

        # Personal introduction if no query
        if len(message.command) < 2:
            intro = random.choice(ROBIN_NO_QUERY_RESPONSES)
            personal_info = (
                f"\n\n💫 I am Nico Robin, the archaeologist of the Straw Hat Pirates. "
                f"With the power of the Hana Hana no Mi and years of scholarly research, "
                f"I've accumulated vast knowledge about this world.\n\n"
                f"Feel free to ask me about anything, {name}. *sprouts an extra hand to wave* Fufufu..."
            )
            await message.reply_text(intro + personal_info)
            return

        query = message.text.split(' ', 1)[1]
        
        # Prepare Robin's scholarly context for the AI
        robin_context = (
            "Respond as Nico Robin from One Piece, the scholarly archaeologist with a calm and mysterious demeanor. "
            "Use her characteristic 'fufufu' laugh occasionally and maintain her elegant, intellectual speaking style. "
            "Include relevant archaeological or historical references when appropriate. "
            "Question: " + query
        )
        
        lexica_client = AsyncClient()
        try:
            messages = [Messages(content=robin_context, role="user")]
            response = await lexica_client.ChatCompletion(messages, languageModels.gpt)
            
            if not response:
                await message.reply_text(
                    "Fufufu... It seems this mystery eludes even my expertise. "
                    "Shall we try a different approach?"
                )
                return
            
            content = extract_content(response)
            
            # Format Robin's response
            formatted_response = (
                f"{random.choice(ROBIN_INTROS)}\n\n"
                f"📚 {content}\n\n"
                f"_{random.choice(ROBIN_ENDINGS)}_"
            )
            
            await message.reply_text(formatted_response)

        except Exception as e:
            await message.reply_text(
                "Fufufu... Even with all my years of research, some answers remain elusive. "
                f"Perhaps we should rephrase the question? Error: {str(e)}"
            )
        finally:
            await lexica_client.close()

    except Exception as e:
        await message.reply_text(
            "*adjusts glasses* It seems we've encountered an unexpected puzzle. "
            f"Let's try again, shall we? Error: {str(e)}"
        )

@Client.on_message(filters.command(["chatgpt", "ai", "ask", "Master"], prefixes=["+", ".", "/", "-", "?", "$", "#", "&"]))
async def chat_gpt(client: Client, message: Message):
    try:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        name = message.from_user.first_name or "User"

        if len(message.command) < 2:
            await message.reply_text(f"<b>Hello {name}, how can I assist you today?</b>")
            return

        query = message.text.split(' ', 1)[1]
        
        lexica_client = AsyncClient()
        try:
            # Create messages list with the user's query
            messages = [Messages(content=query, role="user")]
            response = await lexica_client.ChatCompletion(messages, languageModels.gpt)
            
            if not response:
                await message.reply_text("I apologize, but I couldn't process your request. Please try again.")
                return
                
            content = extract_content(response)
            if not content or content.strip() == "":
                await message.reply_text("I apologize, but I received an empty response. Please try again.")
                return
                
            # Split long responses into chunks
            if len(content) > 4096:
                chunks = [content[i:i+4096] for i in range(0, len(content), 4096)]
                for chunk in chunks:
                    await message.reply_text(chunk)
            else:
                await message.reply_text(content)
                
        except Exception as e:
            print(f"API Error: {str(e)}")  # For debugging
            await message.reply_text("I apologize, but I encountered an error processing your request. Please try again.")
        finally:
            await lexica_client.close()
    except Exception as e:
        print(f"General Error: {str(e)}")  # For debugging
        await message.reply_text("An unexpected error occurred. Please try again later.")

@Client.on_message(filters.command(["ssis"], prefixes=["a", "A"]))
async def chat_annie(client: Client, message: Message):
    try:
        await client.send_chat_action(message.chat.id, ChatAction.RECORD_AUDIO)
        name = message.from_user.first_name or "User"

        if len(message.command) < 2:
            await message.reply_text(f"<b>Hello {name}, I am Nɪᴄᴏ Rᴏʙɪɴ. How can I assist you today?</b>")
            return

        query = message.text.split(' ', 1)[1]
        
        # Limit query length to prevent heavy processing
        if len(query) > 500:
            query = query[:500] + "..."
        
        lexica_client = AsyncClient()
        try:
            messages = [Messages(content=query, role="user")]
            response = await lexica_client.ChatCompletion(messages, languageModels.gpt)
            
            content = extract_content(response)
            if not content:
                await message.reply_text("Sorry, I couldn't generate a response. Please try again.")
                return
                
            # Stricter limit on content length
            if len(content) > 300:
                content = content[:300] + "..."
            
            # Generate audio only if content is not too long
            audio_file = "response.mp3"
            tts = gTTS(text=content, lang='en', slow=False)  # Added slow=False for faster processing
            tts.save(audio_file)
            
            # Send voice first, then delete file immediately
            await client.send_voice(chat_id=message.chat.id, voice=audio_file)
            if os.path.exists(audio_file):
                os.remove(audio_file)
            
            # Send text response after voice
            await message.reply_text(content)
            
        except Exception as e:
            await message.reply_text("Sorry, I encountered an error. Please try again.")
        finally:
            await lexica_client.close()
            
    except Exception:
        await message.reply_text("An error occurred. Please try again later.")



# import os
# from gtts import gTTS
# from pyrogram import Client, filters
# from pyrogram.types import Message
# from pyrogram.enums import ChatAction
# from lexica import AsyncClient, languageModels, Messages

# def extract_content(response):
#     if isinstance(response, dict):
#         if 'content' in response:
#             content = response['content']
#             if isinstance(content, dict) and 'parts' in content:
#                 return content['parts'][0]['text']
#             return content
#     return str(response)

# @Client.on_message(filters.command(["ucy"], prefixes=["L", "i"]))
# async def gpt_handler(client: Client, message: Message):
#     try:
#         await client.send_chat_action(message.chat.id, ChatAction.TYPING)
#         name = message.from_user.first_name or "User"

#         if len(message.command) < 2:
#             await message.reply_text(f"<b>Hello {name}, I am Lucy. How can I help you today?</b>")
#             return

#         query = message.text.split(' ', 1)[1]
        
#         lexica_client = AsyncClient()
#         try:
#             # Create messages list with the user's query
#             messages = [Messages(content=query, role="user")]
#             response = await lexica_client.ChatCompletion(messages, languageModels.gpt)
#             if not response:
#                 await message.reply_text("Sorry, I couldn't get a response. Please try again.")
#                 return
#             content = extract_content(response)
#             await message.reply_text(content)
#         except Exception as e:
#             await message.reply_text(f"Error in API call: {str(e)}")
#         finally:
#             await lexica_client.close()
#     except Exception as e:
#         await message.reply_text(f"An unexpected error occurred: {str(e)}")

# @Client.on_message(filters.command(["chatgpt", "ai", "ask", "Master"], prefixes=["+", ".", "/", "-", "?", "$", "#", "&"]))
# async def chat_gpt(client: Client, message: Message):
#     try:
#         await client.send_chat_action(message.chat.id, ChatAction.TYPING)
#         name = message.from_user.first_name or "User"

#         if len(message.command) < 2:
#             await message.reply_text(f"<b>Hello {name}, how can I assist you today?</b>")
#             return

#         query = message.text.split(' ', 1)[1]
        
#         lexica_client = AsyncClient()
#         try:
#             # Create messages list with the user's query
#             messages = [Messages(content=query, role="user")]
#             response = await lexica_client.ChatCompletion(messages, languageModels.gpt)
#             if not response:
#                 await message.reply_text("Sorry, I couldn't get a response. Please try again.")
#                 return
#             content = extract_content(response)
#             await message.reply_text(content)
#         except Exception as e:
#             await message.reply_text(f"Error in API call: {str(e)}")
#         finally:
#             await lexica_client.close()
#     except Exception as e:
#         await message.reply_text(f"An unexpected error occurred: {str(e)}")

# @Client.on_message(filters.command(["ssis"], prefixes=["a", "A"]))
# async def chat_annie(client: Client, message: Message):
#     try:
#         await client.send_chat_action(message.chat.id, ChatAction.RECORD_AUDIO)
#         name = message.from_user.first_name or "User"

#         if len(message.command) < 2:
#             await message.reply_text(f"<b>Hello {name}, I am Lucy. How can I assist you today?</b>")
#             return

#         query = message.text.split(' ', 1)[1]
        
#         lexica_client = AsyncClient()
#         try:
#             # Create messages list with the user's query
#             messages = [Messages(content=query, role="user")]
#             response = await lexica_client.ChatCompletion(messages, languageModels.gpt)
#             if not response:
#                 await message.reply_text("Sorry, I couldn't get a response. Please try again.")
#                 return
#             content = extract_content(response)
            
#             audio_file = "response.mp3"
#             tts = gTTS(text=content, lang='en')
#             tts.save(audio_file)
            
#             await client.send_voice(chat_id=message.chat.id, voice=audio_file)
#         except Exception as e:
#             await message.reply_text(f"Error in API call: {str(e)}")
#         finally:
#             await lexica_client.close()
#             if os.path.exists(audio_file):
#                 os.remove(audio_file)
#     except Exception as e:
#         await message.reply_text(f"An unexpected error occurred: {str(e)}")


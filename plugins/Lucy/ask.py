import os
from gtts import gTTS
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from lexica import AsyncClient, languageModels, Messages

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

@Client.on_message(filters.command(["ucy"], prefixes=["L", "i"]))
async def gpt_handler(client: Client, message: Message):
    try:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        name = message.from_user.first_name or "User"

        if len(message.command) < 2:
            await message.reply_text(f"<b>Hello {name}, I am Lucy. How can I help you today?</b>")
            return

        query = message.text.split(' ', 1)[1]
        
        lexica_client = AsyncClient()
        try:
            # Create messages list with the user's query
            messages = [Messages(content=query, role="user")]
            response = await lexica_client.ChatCompletion(messages, languageModels.gpt)
            if not response:
                await message.reply_text("Sorry, I couldn't get a response. Please try again.")
                return
            content = extract_content(response)
            await message.reply_text(content)
        except Exception as e:
            await message.reply_text(f"Error in API call: {str(e)}")
        finally:
            await lexica_client.close()
    except Exception as e:
        await message.reply_text(f"An unexpected error occurred: {str(e)}")

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
            
            # Extract content with improved error handling
            content = extract_content(response)
            
            # If content is too long, split it into multiple messages
            if len(content) > 4096:
                chunks = [content[i:i+4096] for i in range(0, len(content), 4096)]
                for chunk in chunks:
                    await message.reply_text(chunk)
            else:
                await message.reply_text(content)
                
        except Exception as e:
            await message.reply_text(f"Error in API call: {str(e)}")
        finally:
            await lexica_client.close()
    except Exception as e:
        await message.reply_text(f"An unexpected error occurred: {str(e)}")

@Client.on_message(filters.command(["ssis"], prefixes=["a", "A"]))
async def chat_annie(client: Client, message: Message):
    try:
        await client.send_chat_action(message.chat.id, ChatAction.RECORD_AUDIO)
        name = message.from_user.first_name or "User"

        if len(message.command) < 2:
            await message.reply_text(f"<b>Hello {name}, I am Lucy. How can I assist you today?</b>")
            return

        query = message.text.split(' ', 1)[1]
        
        lexica_client = AsyncClient()
        try:
            messages = [Messages(content=query, role="user")]
            response = await lexica_client.ChatCompletion(messages, languageModels.gpt)
            
            content = extract_content(response)
            if not content:
                await message.reply_text("Sorry, I couldn't generate a response. Please try again.")
                return
                
            # Limit content length for voice conversion
            if len(content) > 1000:
                content = content[:1000] + "..."
            
            audio_file = "response.mp3"
            try:
                tts = gTTS(text=content, lang='en')
                tts.save(audio_file)
                
                await client.send_voice(chat_id=message.chat.id, voice=audio_file)
                await message.reply_text(content)  # Also send the text response
            except Exception as e:
                await message.reply_text(f"Error generating voice: {str(e)}\n\nText response: {content}")
            
        except Exception as e:
            await message.reply_text(f"Error in API call: {str(e)}")
        finally:
            await lexica_client.close()
            if os.path.exists(audio_file):
                os.remove(audio_file)
    except Exception as e:
        await message.reply_text(f"An unexpected error occurred: {str(e)}")




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

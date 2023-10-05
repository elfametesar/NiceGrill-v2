from nicegrill import Message, run
from telethon import TelegramClient as Client
from gtts import gTTS
from io import BytesIO

import asyncio
import html

class Language:

    @run(command="tts")
    async def text_to_speech(message: Message, client: Client):
        if not message.args and not message.is_reply:
            await message.edit("<i>You need to pass in or reply to a text to convert to speech</i>")
            return
        
        arguments = message.args.split()
        
        language = ""
        text=""
        
        if len(arguments) > 1:
            language, text = arguments[0], " ".join(arguments[1:])
        elif len(arguments) == 1:
            language = arguments[0]

        if message.is_reply:
            text = message.reply_to_text.message
            
        await message.edit("<i>Converting your text to speech</i>")
        
        try:
            tts_result = await asyncio.to_thread(
                gTTS, text=text, tld="com", lang=language
            )
        except (AssertionError, ValueError):
            tts_result = await asyncio.to_thread(
                gTTS, text=language + text, tld="com"
            )
        except Exception as e:
            await message.edit(f"<i>{html.escape(str(e))}</i>")
            return
        
        audio_buffer = BytesIO()
        audio_buffer.name = "tts.mp3"
        tts_result.write_to_fp(audio_buffer)
        
        audio_buffer.seek(0)
        
        try:
            await client.send_file(
                entity=message.chat,
                file=audio_buffer,
                voice_note=True
            )
            await message.delete()
        except Exception as e:
            await message.edit(f"<i>{html.escape(str(e))}</i>")

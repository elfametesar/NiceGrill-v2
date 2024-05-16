from nicegrill import Message, run
from telethon import TelegramClient as Client
from gtts import gTTS
from io import BytesIO
from translate import Translator

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

    @run(command="trt")
    async def google_translate(message: Message, client: Client):
        if not message.args:
            await message.edit("<i>You are missing arguments</i>")
            return
        
        base_lang = "autodetect"

        await message.edit("<i>Translating..</i>")

        if (start_index := message.args.find("base=")) > -1:
            end_index = message.args.find(" ", start_index)
            base_lang = message.args[start_index + 5:end_index]
            message.args = message.args.replace(message.args[start_index:end_index + 1], "")
        
        if message.is_reply:
            base_text = message.reply_to_text.raw_text
            target_lang = message.args
        elif not message.args.count(" "):
            await message.edit("<i>What am I even translating? Give me the target language and the text to translate</i>")
            return
        else:
            target_lang, base_text = message.args.split(maxsplit=2)

        translator = Translator(from_lang=base_lang, to_lang=target_lang)

        translation = translator.translate(base_text)

        if not translation:
            await message.edit("<i>No translation found for the provided text</i>")
            return
        
        await message.edit(f"<i>{translation}</i>")
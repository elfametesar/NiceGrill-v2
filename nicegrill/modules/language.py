#    This file is part of NiceGrill.

#    NiceGrill is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    NiceGrill is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with NiceGrill.  If not, see <https://www.gnu.org/licenses/>.

from elfrien.types.patched import Message
from config import DEEPGRAM_API_KEY
from elfrien.client import Client
from nicegrill import on
from io import BytesIO
from gtts import gTTS

import httpx
import html


class Language:
    """A class to handle language-related functionalities like text-to-speech and translation."""

    @on(pattern="tts")
    async def text_to_speech(client: Client, message: Message):
        """Convert the given text to speech using Google Text-to-Speech.

        The function takes a language code and text either from the message arguments
        or the replied message and converts it to speech.

        Args:
            .tts <lang> <text>: The language code and text.
            .tts <lang>: The text from the replied message.
        """
        if not message.raw_args and not message.reply_to_text:
            await message.edit(
                "<i>You need to pass in or reply to a text to convert to speech</i>"
            )
            return

        arguments = message.args.split()

        language = ""
        text = ""

        if len(arguments) > 1:
            language, text = arguments[0], " ".join(arguments[1:])
        elif len(arguments) == 1:
            language = arguments[0]

        if message.reply_to_text:
            text = message.reply_to_text.raw_text

        await message.edit("<i>Converting your text to speech</i>")

        try:
            tts_result = gTTS(text=text, tld="com", lang=language)
        except (AssertionError, ValueError):
            tts_result = gTTS(text=language + text, tld="com")
        except Exception as e:
            await message.edit(f"<i>{html.escape(str(e))}</i>")
            return

        audio_buffer = BytesIO()
        audio_buffer.name = "tts.mp3"
        tts_result.write_to_fp(audio_buffer)

        audio_buffer.seek(0)

        try:
            await message.respond(files=audio_buffer, force_type="VoiceNote")
            await message.delete()
        except Exception as e:
            await message.edit(f"<i>{html.escape(str(e))}</i>")

    @on(pattern="trt")
    async def translate_text(client: Client, message: Message):
        """Translate the given text to the specified language.

        The function takes a target language code and text either from the message arguments
        or the replied message and translates it.

        Args:
            .trt <lang> <text>: The target language code and text.
            .trt <lang>: The text from the replied message.
        """
        if not message.raw_args:
            await message.edit("<i>You are missing arguments</i>")
            return

        await message.edit("<i>Translating..</i>")

        result = """<b>◍ Text</b>

<i>{}</i>

<b>◍ Translated text</b>

{}"""

        try:
            if message.reply_to_text:
                target_lang = message.raw_args
                await message.edit(
                    message=result.format(
                        message.reply_to_text.raw_text,
                        (
                            await message.reply_to_text.translate(
                                to_language_code=target_lang
                            )
                        ).text,
                    )
                )
            elif not message.raw_args.count(" "):
                await message.edit(
                    "<i>What am I even translating? Give me the target language and the text to translate</i>"
                )
            else:
                target_lang = message.raw_args.split(maxsplit=2)[0]
                message.raw_text = message.raw_args

                await message.edit(
                    message=result.format(
                        message.raw_text,
                        (await message.translate(to_language_code=target_lang)).text,
                    )
                )
        except Exception as e:
            await message.edit(f"<i>{html.escape(str(e))}</i>")

    @on(pattern="stt")
    async def speech_to_Text(client: Client, message: Message):
        if not message.reply_to_text or (
            message.reply_to_text
            and getattr(message.reply_to_text.media, "mime_type", None)
            not in [
                "audio/aac",
                "audio/mp4",
                "audio/mpeg",
                "audio/ogg",
                "audio/opus",
                "audio/wav",
                "audio/webm",
                "audio/x-wav",
                "audio/x-ms-wma",
                "audio/x-matroska",
            ]
        ):
            await message.edit(
                "<i>You need to reply to a voice message to convert it to text</i>"
            )
            return

        if not DEEPGRAM_API_KEY:
            await message.edit("<i>Please set your Deepgram API key</i>")
            return

        await message.edit("<i>Converting your speech to text</i>")

        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "audio/wav",
        }

        audio_data = await message.reply_to_text.download()

        response = httpx.post(
            "https://api.deepgram.com/v1/listen",
            headers=headers,
            data=audio_data.getvalue(),
        )

        if response.status_code != 200:
            await message.edit(
                f"<i>Error: {response.json().get('err_msg', 'unknown')}</i>"
            )
        else:
            result = response.json().get("results", {})
            result = result.get("channels", [{}])
            result = result[0].get("alternatives", [{}])
            result = result[0].get("transcript", "No speech detected in the audio")

            await message.edit(f"<b>Recognized speech:</b> <i>{result}</i>")

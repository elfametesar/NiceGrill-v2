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

from io import BytesIO
from telethon import TelegramClient as Client
from nicegrill import Message, run, startup
from config import GEMINI_API
from database import settingsdb as settings
from g4f.client import AsyncClient as GPTClient
from g4f.errors import RateLimitError, RetryProviderError
from gemini_ng import GeminiClient as GeminiAPIClient
from gemini_ng.schemas.proxy import ProxyInfo
from gemini_webapi import GeminiClient
from gemini_webapi.exceptions import AuthError

import html


class ChatAI:

    CLIENT = GPTClient()
    GEMINI_AI_MODEL = "models/gemini-1.5-pro-latest"
    GEMINI_METADATA = None
    PROXY = None

    @run(command="gpt")
    async def converse_with_chatgpt(message: Message, client: Client):
        await message.edit("<i>Getting a response</i>")

        try:
            response = await ChatAI.CLIENT.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message.args}]
            )
        except (RateLimitError, RetryProviderError):
            await message.edit("<i>You have reached the limit of free use</i>")
            return
        except Exception as e:
            await message.edit(f"<b>Error: </b><i>{e}</i>")
            return

        await message.edit(
f"""⏺ **Me: **__{message.args}__

**⏺ ChatGPT: **
{response.choices[0].message.content}
""",
            parse_mode="md"
        )

    @run(command="gem")
    async def converse_with_gemini_via_cookies(message: Message, client: Client):
        file = None

        proxies = None
        if ChatAI.PROXY:
            proxies = {
                "http://": f"{ChatAI.PROXY.type}://{ChatAI.PROXY.host}:{ChatAI.PROXY.port}",
                "https://": f"{ChatAI.PROXY.type}://{ChatAI.PROXY.host}:{ChatAI.PROXY.port}",
            }

        try:
            gem_client = GeminiClient(
                proxies=proxies
            )

            await gem_client.init(timeout=30, auto_close=False, close_delay=300, auto_refresh=True)

        except ValueError:
            await message.edit(
                f"<i>Failed to load cookies from local browser. Please pass cookie values manually</i>"
            )
            return

        except AuthError:
            await message.edit(
                f"<i>SECURE_1PSIDTS could get expired frequently, please make sure cookie values are up to date</i>"
            )
            return
        
        await message.edit("<i>Asking GeminiAI</i>")

        if message.reply_to_text:
            if message.reply_to_text.photo:
                file: BytesIO = await message.reply_to_text.download_media(BytesIO())
                file.seek(0)
                file = file.getvalue()

            elif message.reply_to_text.message:
                message.args = message.reply_to_text.message + "\n\n" + message.args
        
        message.args = message.args.strip()

        chat = gem_client.start_chat(metadata=ChatAI.GEMINI_METADATA)

        try:
            response = await chat.send_message(message.args, image=file)
        except Exception as e:
            await message.edit(f"<b>GeminiAI: </b><i>{e}</i>")
            return

        ChatAI.GEMINI_METADATA = chat.metadata
        settings.set_ai_metadata(",".join(chat.metadata)) 

        image_urls = ""
        if response.images:
            for image in response.images:
                image_urls += f"\n\n* {image.title}({image.url})"

        await message.edit(
                f"""⏺ **Me: **__{message.args}__

**⏺ Gemini AI: **
{response}{image_urls}""",
                parse_mode="md"
            )

    @run(command="gemapi")
    async def converse_with_gemini_via_api(message: Message, client: Client):
        file_path = None

        try:
            gem_client = GeminiAPIClient(
                api_key=GEMINI_API,
                timeout=5,
                proxy_info=ChatAI.PROXY
            )
        except Exception as e:
            await message.edit(
                f"<b>GeminiAI:</b> <i>{html.escape(str(e))}</i>"
            )
            return
        
        await message.edit("<i>Asking GeminiAI</i>")

        if message.reply_to_text:
            if message.reply_to_text.photo:
                file_path = await message.reply_to_text.download_media("downloads")
                
                try:
                    file_path = gem_client.upload_image(file_path)
                except Exception as e:
                    await client.send_message(
                        message=f"<i>{html.escape(str(e))}</i>",
                        entity=client.me
                    )
                    return

            elif message.reply_to_text.video:
                file_path = await message.reply_to_text.download_media("downloads/")

                try:
                    file_path = gem_client.upload_video(file_path)
                except Exception as e:
                    await client.send_message(
                        message=f"<i>{html.escape(str(e))}</i>",
                        entity=client.me
                    )
                    return

            elif message.reply_to_text.message:
                message.args = message.reply_to_text.message + "\n\n" + message.args

        if not message.args:
            ChatAI.GEMINI_AI_MODEL = "models/gemini-1.5-pro-latest" if ChatAI.GEMINI_AI_MODEL != "models/gemini-1.5-pro-latest" else "models/gemini-1.0-pro"
            await message.edit(f"<i>Gemini version has been set to {ChatAI.GEMINI_AI_MODEL[7:]}</i>")
            return
        
        message.args = message.args.strip()

        with gem_client.start_chat(model=ChatAI.GEMINI_AI_MODEL) as chat:
            if file_path:
                prompt = [
                    file_path,
                    message.args
                ]
            else:
                prompt = [
                    message.args
                ]

            try:
                response = chat.send_message(prompt)
            except Exception as e:
                await client.send_message(
                    message=f"<i>{html.escape(str(e))}</i>",
                    entity=client.me
                )

                if message.chat_id != client.me.id:
                    await message.edit("<i>Error message is in saved messages for privacy</i>")
                else:
                    await message.delete()

                return

            await message.edit(
                f"""⏺ **Me: **__{message.args}__

**⏺ Gemini AI: **
{response.candidates[0].text}""",
                parse_mode="md"
            )

    @run(command="gemproxy")
    async def set_gemini_proxy(message: Message, client: Client):
        if not message.args:
            ChatAI.PROXY = None
            settings.set_ai_proxy("")

            await message.edit("<i>Proxy has been reset</i>")
            return

        if not message.args.count(" ") > 1:
            await message.edit("<i>You need to enter a valid proxy configuration. Example: proxy_type proxy_host proxy_server</i>")
            return
        
        proxy_type, host, port = message.args.split(maxsplit=3)

        try:    
            ChatAI.PROXY = ProxyInfo(
                type=proxy_type,
                host=host,
                port=port
            )

            settings.set_ai_proxy(f"{proxy_type} {host} {port}")
        except Exception:
            await message.edit("<i>Entered proxy configuration is invalid</i>")
            return

        await message.edit(f"<i>Proxy has been set to {proxy_type} type {host}:{port}")

    @run(command="getproxy")
    async def get_gemini_proxy(message: Message, client: Client):
        if ChatAI.PROXY:
            await message.edit(f"<i>{ChatAI.PROXY.type} = {ChatAI.PROXY.host}:{ChatAI.PROXY.port}</i>")
        else:
            await message.edit(f"<i>There is no proxy set for GeminiAI</i>")

@startup
def load_from_database():
    proxy_data = settings.get_ai_proxy()

    if proxy_data != "":
        proxy_type, host, port = proxy_data.split(maxsplit=3)

        ChatAI.PROXY = ProxyInfo(
            type=proxy_type,
            host=host,
            port=port
        )
    else:
        ChatAI.PROXY = None

    metadata = settings.get_ai_metadata()

    ChatAI.GEMINI_METADATA = metadata.split(",")

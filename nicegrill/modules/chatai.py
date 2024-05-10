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

import asyncio
from base64 import b64encode
from io import BytesIO, StringIO
import json
import os
from httpx import delete
from requests import get
from telethon import TelegramClient as Client
from nicegrill import Message, run, startup
from config import GEMINI_API
from database import settingsdb as settings
from gemini_ng import GeminiClient as GeminiAPIClient
from gemini_ng.schemas.proxy import ProxyInfo
from gemini_webapi import GeminiClient
from gemini_webapi.exceptions import AuthError

import html
import requests

class ChatAI:

    GEMINI_METADATA = None
    GEMINI_BEHAVIOR = "Act professionally and reply helpfully."
    PROXY = None

    @run(command="bbox")
    async def converse_with_blackbox(message: Message, client: Client):

        headers = { 
            'accept': '*/*', 
            'accept-language': 'en-US,en;q=0.9', 
            'content-type': 'multipart/form-data; boundary=----WebKitFormBoundary7vTTkk8Ugo0X9Dio', 
            'origin': 'https://www.blackbox.ai', 
            'priority': 'u=1, i', 
            'referer': 'https://www.blackbox.ai/', 
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"', 
            'sec-ch-ua-mobile': '?0', 
            'sec-ch-ua-platform': '"macOS"', 
            'sec-fetch-dest': 'empty', 
            'sec-fetch-mode': 'cors', 
            'sec-fetch-site': 'same-origin', 
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36', 
        }

        description = None
        kwargs = {}
        if message.is_reply:
            if message.reply_to_text.file:
                await message.edit("<i>Uploading media to BlackBoxAI</i>")
                file: BytesIO = await message.reply_to_text.download_media(BytesIO())
                file = file.getvalue()

                try:
                    response = requests.post( 
                        "https://www.blackbox.ai/api/upload", 
                        data=f'------WebKitFormBoundary7vTTkk8Ugo0X9Dio\r\nContent-Disposition: form-data; name="image"; filename="{message.reply_to_text.file.name or "photo.jpg"}"\r\nContent-Type: {message.reply_to_text.file.mime_type}\r\n\r\n{file.decode("latin1")}------WebKitFormBoundary7vTTkk8Ugo0X9Dio\r\nContent-Disposition: form-data; name="fileName"\r\n\r\n{message.reply_to_text.file.name or "photo.jpg"}\r\n------WebKitFormBoundary7vTTkk8Ugo0X9Dio\r\nContent-Disposition: form-data; name="userId"\r\n\r\n405dd035-2f02-4a10-8be8-2603097d954d\r\n------WebKitFormBoundary7vTTkk8Ugo0X9Dio--\r\n',
                        headers=headers
                    )
                except Exception as e:
                    await message.edit(f"<i>{e}</i>")
                    return

                description = json.loads(response.text or "{}").get("response")

                kwargs = {
                    'data': {
                        'imageBase64': f'data:image/webp;base64,{b64encode(file).decode("latin1")}',
                        'fileText': description,
                    }
                }

            elif message.reply_to_text.message:
                message.args = message.reply_to_text.message + "\n\n" + message.args
        
        message.args = message.args.strip()

        if not message.args:
            await message.edit("<i>You need to enter a query</i>")
            return

        await message.edit("<i>Getting a response</i>")

        json_data = {
            'messages': [
                {
                    'id': 'uUXiujU',
                    'content': f'{message.args}',
                    'role': 'user',
                    **kwargs
                },
            ],
            'id': 'uUXiujU',
            'previewToken': None,
            'userId': '405dd035-2f02-4a10-8be8-2603097d954d',
            'codeModelMode': True,
            'agentMode': {},
            'trendingAgentMode': {},
            'isMicMode': False,
            'isChromeExt': False,
            'githubToken': None,
            'clickedAnswer2': False,
            'clickedAnswer3': False,
            'visitFromURL': None,
        }

        response = requests.post('https://www.blackbox.ai/api/chat', headers=headers, json=json_data)
    
        await message.edit(
            f"""⏺ **Me: **__{message.args}__

**⏺ BlackBoxAI: **
__{response.text}__""",
            parse_mode="md"
        )

    @run(command="gpt")
    async def converse_with_chatgpt(message: Message, client: Client):

        if message.is_reply and message.reply_to_text.message:
                message.args = message.reply_to_text.message + "\n\n" + message.args
        
        message.args = message.args.strip()

        if not message.args:
            await message.edit("<i>You need to enter a query</i>")
            return

        await message.edit("<i>Getting a response</i>")

        headers = {
            'content-type': 'application/json',
            'origin': 'https://chat10.aichatos.xyz',
            'referer': 'https://chat10.aichatos.xyz/',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }

        json_data = {
            'prompt': message.args,
            'network': True,
            'withoutContext': False,
            'stream': True,
        }

        response = requests.post('https://api.binjie.fun/api/generateStream', headers=headers, json=json_data)

        await message.edit(
f"""⏺ **Me: **__{message.args}__

**⏺ ChatGPT: **
{response.text}
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

        if message.reply_to_text:
            if message.reply_to_text.photo:
                await message.edit("<i>Downloading media for GeminiAI</i>")
                file: BytesIO = await message.reply_to_text.download_media(BytesIO())
                file.seek(0)
                file = file.getvalue()

            elif message.reply_to_text.message:
                message.args = message.reply_to_text.message + "\n\n" + message.args
        
        message.args = message.args.strip()

        if not message.args:
            await message.edit("<i>You need to enter a query</i>")
            return

        await message.edit("<i>Asking GeminiAI</i>")

        chat = gem_client.start_chat(metadata=ChatAI.GEMINI_METADATA)

        try:
            response = await chat.send_message(
                prompt=f"""{ChatAI.GEMINI_BEHAVIOR}
Query: {message.args}""",
                image=file
            )
        except Exception as e:
            await message.edit(f"<b>GeminiAI: </b><i>{e}</i>")
            return

        ChatAI.GEMINI_METADATA = chat.metadata
        settings.set_ai_metadata(",".join(chat.metadata)) 

        image_list = []
        response_text = response.text
        if response.images:
            for image in response.images:
                image_response = get(image.url, allow_redirects=True, cookies=gem_client.cookies)
                if "image" in image_response.headers.get("Content-Type"):
                    image_file = BytesIO(image_response.content)
                    image_file.name = image.title + ".png"
                    image_file.seek(0)
                    image_list.append(image_file)
                else:
                    response_text += f"\n\n* {image.title}({image.url})"

        await message.edit(
                f"""⏺ **Me: **__{message.args}__

**⏺ Gemini AI: **
{response_text}""",
                parse_mode="md"
            )
        
        if image_list:
            await message.respond(
                file=image_list,
                message="<i>Generated by GeminiAI</i>"
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
                    f"""{ChatAI.GEMINI_BEHAVIOR}
Query: {message.args}"""
                ]
            else:
                prompt = [
                    f"""{ChatAI.GEMINI_BEHAVIOR}
Query: {message.args}"""
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

    @run(command="gembehavior")
    async def set_gemini_behavior(message: Message, client: Client):
        if not message.args:
            ChatAI.GEMINI_BEHAVIOR = "Act professionally and reply helpfully."
            settings.set_ai_behavior("Act professionally and reply helpfully.")
            await message.edit("<i>Gemini behavior setting has been reset</i>")
            return
        
        ChatAI.GEMINI_BEHAVIOR = message.args
        settings.set_ai_behavior(message.args)

        await message.edit("<i>A new behavior set for Gemini AI</i>")

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

    ChatAI.GEMINI_BEHAVIOR = settings.get_ai_behavior()

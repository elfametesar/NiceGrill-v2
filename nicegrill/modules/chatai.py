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

from config import (
    GEMINI_1PSID, GEMINI_1PSIDTS,
    OPENROUTER_COOKIE, CHATGPT_BEARER_KEY
)
from gemini_webapi.exceptions import AuthError
from nicegrill import Message, on, startup
from gemini_webapi import GeminiClient
from fake_useragent import UserAgent
from urllib.parse import urlencode
from elfrien.client import Client
from datetime import datetime
from base64 import b64encode
from database import settings
from hashlib import sha3_512
from random import choice
from requests import get
from io import BytesIO
from uuid import uuid4

import logging
import httpx
import json

class ChatAI:

    GEMINI_METADATA = None
    GPT_CONVERSATION_ID = None
    AI_BEHAVIOR = "Act professionally and reply helpfully."
    CLIENT: httpx.Client = None
    MODE = None

    LOG = logging.getLogger(__name__)

    @on(pattern="genimg")
    async def generate_image_from_input(client: Client, message: Message):
        if message.reply_to_text:
            message.raw_args = f"{message.reply_to_text.raw_text}\n\n{message.raw_args}"

        if not message.raw_args:
            await message.edit("<i>You need to describe the image you want to generate</i>")
            return

        await message.edit(f"<i>Generating image for {message.raw_args}</i>")

        response = ChatAI.CLIENT.get(
            'https://perchance.org/api/getAccessCodeForAdPoweredStuff'
        )

        access_code = response.text

        user_key = ChatAI.CLIENT.get('https://image-generation.perchance.org/api/verifyUser').json()
        if not (user_key := user_key.get("userKey")):
            await message.edit(
                "<i>Cannot fetch user key, you need to go to https://perchance.org/ai-text-to-image-generator and click on generate manually</i>",
                link_preview=False
            )
            return

        params = {
            "prompt": message.raw_args,
            "seed": -1,
            "resolution": '1920x1080',
            "guidanceScale": 7,
            "negativePrompt": ', (worst quality, low quality, blurry:1.3), black and white, low-quality, deformed, text, poorly drawn, bad art, bad anatomy, bad lighting, disfigured, faded, blurred face',
            "channel": 'ai-text-to-image-generator',
            "subChannel": 'public',
            "userKey": user_key,
            "adAccessCode": access_code,
            "requestId": 0.8165463415238716,
            "__cacheBust": 0.3450872446915627
        }

        image_list = []
        for _ in range(6):
            response = ChatAI.CLIENT.post(
                url='https://image-generation.perchance.org/api/generate?' + urlencode(params, doseq=True)
            )

            try:
                image_id = response.json()["imageId"]
                data = BytesIO(
                    ChatAI.CLIENT.get(
                        url='https://image-generation.perchance.org/api/downloadTemporaryImage',
                        params={
                            "imageId": image_id
                        }
                    ).content
                )
            except Exception as e:
                await message.edit(
                    f"<i>Could not generate images</i>\n<b>Reason:</b> <i>{e}</i>"
                )
                return

            data.name = "generated_image.png"
            image_list.append(data)

        await message.delete()
        await message.respond(
            files=image_list,
            message="<i>Generated by Perchance</i>"
        )

    @on(pattern="(mytho|mistral|nous|openchat|toppy|cine|meta|gemma)")
    async def converse_with_multi_ai(client: Client, message: Message):
        """mytho, mistral, nous, openchat, toppy, cine, meta, gemma

All of these seems to be fake, i just added them anyway, more the merrier I took them from openrouter.ai. You can find your __session cookie there after logging in"""

        if message.reply_to_text and message.reply_to_text.raw_text:
                message.raw_args = message.reply_to_text.raw_text + "\n\n" + message.raw_args
        
        message.raw_args = message.raw_args

        if not message.raw_args:
            await message.edit("<i>You need to enter a query</i>")
            return
        
        await message.edit("<i>Asking the AI...</i>")
        
        if message.cmd == "mytho":
            model = "gryphe/mythomist-7b:free"
        elif message.cmd == "mistral":
            model = "mistralai/mistral-7b-instruct:free"
        elif message.cmd == "nous":
            model = "nousresearch/nous-capybara-7b:free"
        elif message.cmd == "openchat":
            model = "openchat/openchat-7b:free"
        elif message.cmd == "toppy":
            model = "undi95/toppy-m-7b:free"
        elif message.cmd == "cine":
            model = "openrouter/cinematika-7b:free"
        elif message.cmd == "meta":
            model = "meta-llama/llama-3-8b-instruct:free"
        elif message.cmd == "gemma":
            model = "google/gemma-7b-it:free"

        data = {
            "stream": False,
            "model": model,
            "max_tokens": 0,
            "messages": [
                {
                    "role": "system",
                    "content": ChatAI.AI_BEHAVIOR
                },
                {
                    "role": "user",
                    "content": message.raw_args
                }
            ]
        }

        response = ChatAI.CLIENT.post(
            url='https://openrouter.ai/api/v1/chat/completions',
            cookies={
                '__session': OPENROUTER_COOKIE
            },
            data=json.dumps(data).encode(),
            headers={
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
            }
        )

        if response.is_success and response.json().get("choices"):
            response = response.json().get("choices")[0].get("message").get("content").strip()
            await message.edit(
                f"""⏺ **Me: **__{message.raw_args}__

**⏺ {message.cmd.title()}AI: **
__{response}__""",
                parse_mode="Markdown"
            )
        else:
            await message.edit(f"<i>No response receieved from {message.cmd.title()}</i>\n<b>Reason:</b> <i>{response.reason}</i>")

    @on(pattern="bbox")
    async def converse_with_blackbox(client: Client, message: Message):

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
            'sec-fetch-site': 'same-origin'
        }

        description = None
        kwargs = {}
        if message.reply_to_text:
            if message.reply_to_text.file:
                await message.edit("<i>Uploading media to BlackBoxAI</i>")
                file: BytesIO = await message.reply_to_text.download_media(BytesIO())
                file = file.getvalue()

                try:
                    response = ChatAI.CLIENT.post(
                        url="https://www.blackbox.ai/api/upload", 
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

            elif message.reply_to_text.raw_text:
                message.raw_args = message.reply_to_text.raw_text + "\n\n" + message.raw_args
        
        message.raw_args = message.raw_args

        if not message.raw_args:
            await message.edit("<i>You need to enter a query</i>")
            return

        await message.edit("<i>Getting a response</i>")

        json_data = {
            'messages': [
                {
                    'id': 'uUXiujU',
                    'content': f'{ChatAI.AI_BEHAVIOR}\nQuery:{message.raw_args}',
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

        response = ChatAI.CLIENT.post(
            'https://www.blackbox.ai/api/chat',
            headers=headers,
            json=json_data
        )
    
        await message.edit(
            f"""⏺ **Me: **__{message.raw_args}__

**⏺ BlackBoxAI: **
__{response.text}__""",
            parse_mode="Markdown"
        )

    # https://github.com/josStorer/chatGPTBox/blob/487e1f88c27356a1d5f4629cdb9e55b6c1b5af8b/src/services/apis/chatgpt-web.mjs#L97
    def generate_proof_token(seed, diff, user_agent=str(UserAgent.chrome)):
        """
        Generates a proof token based on the provided seed, difficulty, and user agent.

        Args:
            seed: The seed value used for hashing.
            diff: The difficulty level represented by a hexadecimal string.
            user_agent: The user agent string.

        Returns:
            A proof token string or a fallback token if no match is found within 100000 iterations.
        """

        cores = [8, 12, 16, 24]
        screens = [3000, 4000, 6000]

        core = choice(cores)
        screen = choice(screens)

        current_time = str(datetime.now())

        config = [core + screen, current_time, 4294705152, 0, user_agent]

        diff_length = int(len(diff) / 2)

        for _ in range(100000):
            config[3] = _
            json_data = json.dumps(config)
            base64_data = b64encode(json_data.encode('utf-8')).decode('utf-8')
            hash_value = sha3_512(seed.encode('utf-8') + base64_data.encode('utf-8')).hexdigest()

            if hash_value[:diff_length] <= diff:
                return 'gAAAAAB' + base64_data

        fallback_base64 = b64encode(f'"{seed}"'.encode('utf-8')).decode('utf-8')
        return 'gAAAAABwQ8Lk5FbGpA2NcR9dShT6gYjU7VxZ4D' + fallback_base64

    @on(pattern="gptchats")
    async def get_gpt_chats(client: Client, message: Message):
        await message.edit("<i>Requesting for ChatGPT chats</i>")
        
        headers = {
            'authorization': f'Bearer {CHATGPT_BEARER_KEY}',
            'oai-language': 'en-US',
            'priority': 'u=1, i',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': str(UserAgent.chrome)
        }

        params = (
            ('offset', '0'),
            ('limit', '28'),
            ('order', 'updated'),
        )

        response = ChatAI.CLIENT.get(
            'https://chatgpt.com/backend-api/conversations',
            headers=headers,
            cookies={
                '__Secure-next-auth.session-token': CHATGPT_BEARER_KEY,
            },
        )

        if not response.is_success:
            ChatAI.LOG.error(response.text)
            await message.edit(f"<i>Cannot request ChatGPT for chat information</i>\n<b>Reason: </b><i>{response.reason_phrase} (Details in the logs)</i>")
            return

        menu = "<b>Your ChatGPT Chats</b>\n\n"
        for chat in response.json().get("items"):
            menu += f'<b>Chat ID:</b> <i>{chat.get("id")}</i>\n<b>Chat Title:</b> {chat.get("title")}</i>\n\n'
        
        await message.edit(menu)

    @on(pattern="setgptchat")
    async def set_chat_id(client: Client, message: Message):
        if not message.raw_args:
            await message.edit("<i>Give me a chat ID</i>")
            return
        
        ChatAI.GPT_CONVERSATION_ID = message.raw_args
        settings.set_gpt_chat(message.raw_args)

        await message.edit("<i>Chat ID has been set</i>")

    @on(pattern="gpt")
    async def converse_with_chatgpt(client: Client, message: Message):

        if message.reply_to_text and message.reply_to_text.raw_text:
                message.raw_args = message.reply_to_text.raw_text + "\n\n" + message.raw_args
        
        message.raw_args = message.raw_args

        if not message.raw_args:
            await message.edit("<i>You need to enter a query</i>")
            return

        if not ChatAI.GPT_CONVERSATION_ID:
            await message.edit("<i>I need you to set a conversation ID first, you can find it in the in the URL in ChatGPT chat page<i>")
            return

        cookies = {
            "__Secure-next-auth.session-token": CHATGPT_BEARER_KEY
        }

        headers = {
            'content-type': 'application/json',
            'oai-language': 'en-US',
            'priority': 'u=1, i',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': str(UserAgent.chrome)
        }

        file_id = None
        if message.reply_to_text:
            if message.reply_to_text.photo or message.reply_to_text.sticker:
                await message.edit("<i>Downloading media for ChatGPT</i>")
                file: BytesIO = await message.reply_to_text.download()

                response = ChatAI.CLIENT.post(
                    url='https://chatgpt.com/backend-api/files',
                    cookies=cookies,
                    headers={**headers, 'authorization': f'Bearer {CHATGPT_BEARER_KEY}'},
                    data=json.dumps({
                        'file_name': message.reply_to_text.file.name or "photo.jpg",
                        'file_size': message.reply_to_text.file.size,
                        'use_case': 'multimodal',
                        'reset_rate_limits': False,
                    })
                )

                if response.json().get("status") != "success":
                    ChatAI.LOG.error(response.text)
                    await message.edit(f"<i>Cannot upload media to ChatGPT</i>\n<b>Reason: </b><i>{response.reason_phrase} (Details in the logs)</i>")
                    return

                file_id = response.json().get("file_id")

                params = response.json().get("upload_url")
                params = params[params.find("?"):]

                response = ChatAI.CLIENT.put(
                    url='https://files.oaiusercontent.com/' + file_id + params,
                    headers={**headers, 'x-ms-blob-type': 'BlockBlob', 'x-ms-version': '2020-04-08', "content-type": message.reply_to_text.file.mime_type},
                    data=file.getvalue()
                )

                if not response.is_success:
                    ChatAI.LOG.error(response.text)
                    await message.edit(f"<i>Cannot sign media file in ChatGPT</i>\n<b>Reason: </b><i>{response.reason_phrase} (Details in the logs)</i>")
                    return
                
                response = ChatAI.CLIENT.post(
                    f'https://chatgpt.com/backend-api/files/{file_id}/uploaded',
                    cookies=cookies,
                    headers={**headers, 'authorization': f'Bearer {CHATGPT_BEARER_KEY}'},
                    json={},
                )

            elif message.reply_to_text.raw_text:
                message.raw_args = message.reply_to_text.raw_text + "\n\n" + message.raw_args

        await message.edit("<i>Getting a response</i>")

        try:
            response = ChatAI.CLIENT.post(
                url='https://chatgpt.com/backend-api/sentinel/chat-requirements',
                cookies=cookies,
                headers={**headers, 'authorization': f'Bearer {CHATGPT_BEARER_KEY}'}
            )

            if response.status_code != 200:
                ChatAI.LOG.error(response.text)
                raise ConnectionAbortedError(f"Connection to requirements API received {response.status_code}. Check logs for details...")

            headers["openai-sentinel-chat-requirements-token"] = response.json().get("token")

            seed = response.json().get("proofofwork").get("seed")
            difficulty = response.json().get("proofofwork").get("difficulty")
        except Exception as e:
            await message.edit(f"<i>Token cannot be fetched</i>\n<b>Reason: </b><i>{e}</i>")
            return

        headers["openai-sentinel-proof-token"] = ChatAI.generate_proof_token(seed, difficulty)

        json_data = {
            'action': 'next',
            'messages': [
                {
                    'id': str(uuid4()),
                    'author': {
                        'role': 'user',
                    },
                    'content': {
                        'content_type': 'text',
                        'parts': [
                            message.raw_args,
                        ],
                    },
                } if not file_id else {
                    'id': str(uuid4()),
                    'author': {
                        'role': 'user',
                    },
                    'content': {
                        'content_type': 'multimodal_text',
                        'parts': [{
                            'content_type': 'image_asset_pointer',
                            'asset_pointer': f'file-service://{file_id}',
                            'size_bytes': message.reply_to_text.file.size,
                            'width': message.reply_to_text.photo.sizes[-1].w,
                            'height': message.reply_to_text.photo.sizes[-1].h
                        }, message.raw_args],
                    },
                    'metadata': {
                        'attachments': [
                            {
                                'id': file_id,
                                'size': message.reply_to_text.file.size,
                                'name': message.reply_to_text.file.name or "photo.jpg",
                                'mime_type': 'image/jpeg',
                                'width': message.reply_to_text.photo.sizes[-1].w,
                                'height': message.reply_to_text.photo.sizes[-1].h,
                            },
                        ],
                    },
                }
            ],
            'conversation_id': ChatAI.GPT_CONVERSATION_ID,
            'model': 'auto',
            'history_and_training_disabled': False,
            'force_paragen': False,
            'force_paragen_model_slug': '',
            'force_nulligen': False,
            'force_rate_limit': False,
            'reset_rate_limits': False,
            'force_use_sse': True
        }

        try:
            response = ChatAI.CLIENT.post(
                url='https://chatgpt.com/backend-api/conversation',
                cookies=cookies,
                headers={**headers, 'authorization': f'Bearer {CHATGPT_BEARER_KEY}'},
                json=json_data
            )
        except Exception as e:
            await message.edit(f"<i>Connection to ChatGPT failed<i>\n<b>Reason:</b> <i>{e}</i>")
            return

        if response.status_code != 200:
            ChatAI.LOG.error(response.text)
            await message.edit(f"<i>Connection to ChatGPT backend api received {response.status_code}. Check logs for details...</i>")
            return
        
        response = [line[6:] for line in response.text.splitlines() if line.startswith("data: {\"message")][-1]
        if not response:
            ChatAI.LOG.error(f"Received and processed data from ChatGPT:\n\n {response}")
            await message.edit("<i>There seems to be a problem with the response from ChatGPT. Check logs for details...</i>")
            return

        response = "".join(json.loads(response).get("message").get("content").get("parts"))

        await message.edit(
f"""⏺ **Me: **__{message.raw_args}__

**⏺ ChatGPT: **
{response}
""",
            parse_mode="Markdown"
        )

    @on(pattern="gem")
    async def converse_with_gemini_via_cookies(client: Client, message: Message):
        file = None

        try:
            gem_client = GeminiClient(
                secure_1psid=GEMINI_1PSID,
                secure_1psidts=GEMINI_1PSIDTS,
                proxies={
                    "https://": ":".join(ChatAI.CLIENT.proxy).replace(":", "://", 1)
                } if ChatAI.CLIENT.proxy else None
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

            elif message.reply_to_text.raw_text:
                message.raw_args = message.reply_to_text.raw_text + "\n\n" + message.raw_args
        
        message.raw_args = message.raw_args

        if not message.raw_args:
            await message.edit("<i>You need to enter a query</i>")
            return

        await message.edit("<i>Asking GeminiAI</i>")

        chat = gem_client.start_chat(metadata=ChatAI.GEMINI_METADATA)

        try:
            response = await chat.send_message(
                prompt=f"""{ChatAI.AI_BEHAVIOR}
Query: {message.raw_args}""",
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
                f"""⏺ **Me: **__{message.raw_args}__

**⏺ Gemini AI: **
{response_text}""",
                parse_mode="Markdown"
            )
        
        if image_list:
            await message.respond(
                file=image_list,
                message="<i>Generated by GeminiAI</i>"
            )

    @on(pattern="setproxy")
    async def set_gemini_proxy(client: Client, message: Message):
        if not message.raw_args:
            ChatAI.CLIENT = httpx.Client(follow_redirects=True, proxies=None)
            ChatAI.CLIENT.proxy = None
            settings.set_ai_proxy("")

            await message.edit("<i>Proxy has been reset</i>")
            return

        if not message.raw_args.count(" ") > 1:
            await message.edit("<i>You need to enter a valid proxy configuration. Example: proxy_type proxy_host proxy_server</i>")
            return
        
        proxy_type, host, port = message.raw_args.split(maxsplit=3)

        try:
            ChatAI.CLIENT = httpx.Client(follow_redirects=True, proxies=f"{proxy_type}://{host}:{port}")
        except Exception as e:
            await message.edit(f"<i>{e}</i>")
            return

        ChatAI.CLIENT.proxy = [proxy_type, host, port]

        settings.set_ai_proxy(f"{proxy_type} {host} {port}")

        await message.edit(f"<i>Proxy has been set to {proxy_type} type {host}:{port}")

    @on(pattern="getproxy")
    async def get_gemini_proxy(client: Client, message: Message):
        if ChatAI.CLIENT.proxy:
            await message.edit(f"<i>{ChatAI.CLIENT.proxy[0]} = {ChatAI.CLIENT.proxy[1]}:{ChatAI.CLIENT.proxy[2]}</i>")
        else:
            await message.edit(f"<i>There is no proxy set for AI</i>")

    @on(pattern="aibehavior")
    async def set_AI_BEHAVIOR(client: Client, message: Message):
        if not message.raw_args:
            ChatAI.AI_BEHAVIOR = "Act professionally and reply helpfully."
            settings.set_ai_behavior("Act professionally and reply helpfully.")
            await message.edit("<i>Gemini behavior setting has been reset</i>")
            return
        
        ChatAI.AI_BEHAVIOR = message.raw_args
        settings.set_ai_behavior(message.raw_args)

        await message.edit("<i>A new behavior set for the AI</i>")

    @on(pattern="mode")
    async def enable_message_listener(client: Client, message: Message):
        if not message.raw_args:
            ChatAI.MODE = None
            await message.edit("<i>Chat mode is disabled</i>")
            return
        
        if message.raw_args.lower() != "chatgpt" and message.raw_args.lower() != "gemini":
            await message.edit("<i>Only Gemini and ChatGPT is supported with this feature</i>")
            return

        await message.edit(f"<i>Conversation mode with AI is now enabled and set to {message.raw_args.title()}</i>")
        ChatAI.MODE = message.raw_args.lower()

@on(prefix="", pattern="")
async def listen_for_message(client: Client, message: Message):
    if not ChatAI.MODE:
        return

    message.raw_args = message.raw_text
    if ChatAI.MODE == "chatgpt":
        await ChatAI.converse_with_chatgpt(message, client)

    elif ChatAI.MODE == "gemini":
        await ChatAI.converse_with_gemini_via_cookies(message, client)

@startup
def load_from_database():
    proxy_data = settings.get_ai_proxy()

    if proxy_data:
        proxy_type, host, port = proxy_data.split(maxsplit=3)
        proxy = f"{proxy_type}://{host}:{port}"
    else:
        proxy = None

    ChatAI.CLIENT = httpx.Client(follow_redirects=True, proxies=proxy)
    ChatAI.CLIENT.proxy = proxy_data.split(maxsplit=3)
    ChatAI.GPT_CONVERSATION_ID = settings.get_gpt_chat()

    metadata = settings.get_ai_metadata()
    ChatAI.GEMINI_METADATA = metadata.split(",")
    ChatAI.AI_BEHAVIOR = settings.get_ai_behavior()


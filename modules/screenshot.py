from telethon import TelegramClient
from telethon.tl.types import Message
from main import run
from config import SCREENSHOT_API
from httpx import AsyncClient
from io import BytesIO

import html

class Screenshot:
    
    API_URL = "https://api.screenshotlayer.com/api/capture?access_key={}&url={}&fullpage={}&format={}&viewport={}"
    
    @run(command="ss")
    async def screenshot_taker(message: Message, client: TelegramClient):
        if not message.args:
            await message.edit("<i>You need to input a URL to be taken screenshot of</i>")
            return
        
        if not SCREENSHOT_API:
            await message.edit(
                "<i>You need to get an API id first, you can do so by visiting and registering to:\n"
                "https://screenshotlayer.com/</i>"
            )
            return
        
        await message.edit("<i>Taking a screenshot...</i>")
        
        async with AsyncClient() as session:
            result = await session.get(
                url=Screenshot.API_URL.format(
                    SCREENSHOT_API, message.args, "1", "PNG", "2560x1440"
            ),
            follow_redirects=True
        )
        
        content_type = result.headers["content-type"]
        
        if "image" in content_type:
            image_buffer = BytesIO(result.content)
            image_buffer.name = "screenshot.png"
            
            try:
                await message.respond(
                    file=image_buffer
                )
                await message.delete()
            except Exception as e:
                await message.edit(f"<i>{html.escape(e)}</i>")
                return
            
            return
        
        await message.edit("<i>No image received from server, check your URL</i>")
from main import run
from telethon import TelegramClient
from telethon.tl.types import Message
from config import WOLFRAM_API
from httpx import AsyncClient

class Wolfram:
    
    API_URL = "https://api.wolframalpha.com/v1/spoken?appid={}&i={}"
    
    @run(command="ask")
    async def wolfram_query(message: Message, client: TelegramClient):
        if not message.args:
            await message.edit("<i>You need to input a query text to ask the server</i>")
            return
        
        if not WOLFRAM_API:
            await message.edit(
                "<i>You need to get an API id first, you can do so by visiting and registering to:\n"
                "products.wolframalpha.com/api/</i>"
            )
            return
        
        await message.edit("<i>Thinking...</i>")

        async with AsyncClient() as session:
            result = await session.get(
                url=Wolfram.API_URL.format(
                    WOLFRAM_API, message.args
            ),
            follow_redirects=True
        )
        
        await message.edit(f"<i>{result.text}</i>")
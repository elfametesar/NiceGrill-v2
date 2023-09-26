from main import Message, run
from telethon import TelegramClient as Client
from config import WOLFRAM_API
from httpx import AsyncClient

class Wolfram:
    
    API_URL = "https://api.wolframalpha.com/v1/spoken?appid={}&i={}"
    
    @run(command="ask")
    async def wolfram_query(message: Message, client: Client):
        query = message.args

        if message.is_reply:
            query = message.reply_to_text.text

        if not query:
            await message.edit("<em>You need to input a query text to ask the server</em>")
            return
        
        if not WOLFRAM_API:
            await message.edit(
                "<em>You need to get an API id first, you can do so by visiting and registering to:\n"
                "</em>http://products.wolframalpha.com/api/"
            )
            return
        
        await message.edit("<em>Thinking...</em>")

        async with AsyncClient() as session:
            result = await session.get(
                url=Wolfram.API_URL.format(
                    WOLFRAM_API, query
            ),
            follow_redirects=True
        )
        
        await message.edit(f"<em>{result.text}</em>")
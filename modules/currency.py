from telethon import TelegramClient as Client
from main import Message, run
from bs4 import BeautifulSoup

from httpx import get

class Currency:
    
    SEARCH_URL = "https://www.bing.com/search?q={query}&setlang=en"
    
    @run(command="cur")
    async def convert_currency(message: Message, client: Client):
        if not message.args:
            await message.edit("<i>You need to specify an amount to convert</i>")
            return
        
        await message.edit("<i>Converting specified currency</i>")
        
        html_data = get(Currency.SEARCH_URL.format(query=message.args), follow_redirects=True).text
        html_parser = BeautifulSoup(html_data, "lxml")
        
        result = html_parser.find("div", class_="b_focusTextSmall curr_totxt")
        
        if result and result.text:
            await message.edit(f"<b>{message.args}:</b> <i>{result.text}</i>")
        else:
            await message.edit("<i>There is no result for your currency query</i>")
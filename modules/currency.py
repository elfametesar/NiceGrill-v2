from telethon import TelegramClient as Client
from main import Message, run
from bs4 import BeautifulSoup

from httpx import get

class Currency:
    
    SEARCH_URL = "https://www.bing.com/search?q={query}&setlang=en"
    HEADERS = {"User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"}
    
    @run(command="cur")
    async def convert_currency(message: Message, client: Client):
        if not message.args:
            await message.edit("<i>You need to specify an amount to convert</i>")
            return
        
        await message.edit("<i>Converting specified currency</i>")
        
        html_data = get(
            url=Currency.SEARCH_URL.format(query=message.args),
            follow_redirects=True,
            headers=Currency.HEADERS
        ).text

        html_parser = BeautifulSoup(html_data, "lxml")
        
        source_currency = html_parser.find("div", class_="b_focusTextExtraSmall curr_fl curr_frtxt")
        converted_currency = html_parser.find("div", class_="b_focusTextSmall curr_totxt")
        
        result = f"{str(source_currency).replace(' =', ' is ', -1)}{converted_currency}"
        
        if not source_currency or not converted_currency:
            await message.edit("<i>There is no result for your currency query</i>")
        else:
            await message.edit(f"<i>{result}</i>")
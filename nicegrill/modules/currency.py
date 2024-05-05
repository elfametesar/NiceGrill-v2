from telethon import TelegramClient as Client
from nicegrill import Message, run
from bs4 import BeautifulSoup as bs
from requests import get

import asyncio

class Currency:

    URL = "https://www.bing.com/search"
    
    HEADERS = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-full-version': '"124.0.6367.29"',
        'sec-ch-ua-full-version-list': '"Not-A.Brand";v="99.0.0.0", "Chromium";v="124.0.6367.29"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Linux"',
        'sec-ch-ua-platform-version': '"6.8.2"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }

    @run(command="cur")
    async def convert_currency(message: Message, client: Client):
        if not message.args:
            await message.edit("<i>You need to specify an amount to convert</i>")
            return

        await message.edit("<i>Converting specified currency</i>")

        response = await asyncio.to_thread(
            get,
            url=f"https://www.bing.com/search?q={message.args.replace(' ', '+')}",
            headers=Currency.HEADERS
        )

        soup = bs(
            response.content, "lxml"
        )

        source = soup.find(
            name="div",
            attrs={"class": "b_focusTextExtraSmall curr_fl curr_frtxt"}
        )

        if not source:
            await message.edit("<i>No currency conversion found</i>")
            return

        destination = soup.find(
            name="div",
            attrs={"class": "b_focusTextSmall curr_totxt"}
        )

        source, destination = source.text.rstrip(" ="), destination.text

        await message.edit(f"<i>{source} is {destination}</i>")

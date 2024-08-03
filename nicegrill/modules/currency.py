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
from bs4 import BeautifulSoup as bs
from elfrien.client import Client
from nicegrill import on
from requests import get


class Currency:

    URL = "https://www.bing.com/search"

    HEADERS = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=0, i",
        "sec-ch-ua": '"Not-A.Brand";v="99", "Chromium";v="124"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-bitness": '"64"',
        "sec-ch-ua-full-version": '"124.0.6367.29"',
        "sec-ch-ua-full-version-list": '"Not-A.Brand";v="99.0.0.0", "Chromium";v="124.0.6367.29"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Linux"',
        "sec-ch-ua-platform-version": '"6.8.2"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }

    @on(pattern="cur")
    async def convert_currency(client: Client, message: Message):
        if not message.raw_args:
            await message.edit("<i>You need to specify an amount to convert</i>")
            return

        await message.edit("<i>Converting specified currency</i>")

        response = get(
            url=f"https://www.bing.com/search?q={message.raw_args.replace(' ', '+')}",
            headers=Currency.HEADERS,
        )

        soup = bs(response.content, "lxml")

        source = soup.find(
            name="div", attrs={"class": "b_focusTextExtraSmall curr_fl curr_frtxt"}
        )

        if not source:
            await message.edit("<i>No currency conversion found</i>")
            return

        destination = soup.find(
            name="div", attrs={"class": "b_focusTextSmall curr_totxt"}
        )

        source, destination = source.text.rstrip(" ="), destination.text

        await message.edit(f"<i>{source} is {destination}</i>")

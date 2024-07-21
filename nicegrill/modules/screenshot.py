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

from playwright.async_api import async_playwright
from elfrien.types.patched import Message
from elfrien.client import Client
from nicegrill import on

import html

class Screenshot:
    
    @on(pattern="ss")
    async def screenshot_taker(client: Client, message: Message):
        if not message.raw_args:
            await message.edit("<i>You need to input a URL to be taken screenshot of</i>")
            return

        await message.edit("<i>Taking a screenshot...</i>")
        
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch()
                browser = await browser.new_page(java_script_enabled=True, viewport={"width": 1920, "height": 1080})
                await browser.goto(message.raw_args, wait_until="networkidle")
                image = await browser.screenshot(type="png")
        except Exception as e:
            await message.edit(f"<i>Error: {html.escape(str(e))}</i>")
            return
    
        await message.respond(
            files=image,
            force_type="Photo"
        )
        await message.delete()
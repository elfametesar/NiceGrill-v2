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


class Speedtest:

    @on(pattern="speed")
    async def speedtest_by_ookla(client: Client, message: Message):
        await message.edit("<i>Speedtest is running</i>")

        async with async_playwright() as playwright:

            browser = await playwright.chromium.launch(args=["--start-maximized"])

            browser = await browser.new_page(permissions=["geolocation"])

            await browser.goto(
                url="https://www.speedtest.net/", wait_until="networkidle"
            )

            if (
                await (button := browser.get_by_role("button", name="I Accept")).count()
                == 1
            ):
                await button.click()

            if (
                await (
                    button := browser.get_by_role("link", name="Back to test results")
                ).count()
                == 1
            ):
                await button.click()

            await browser.get_by_label(
                "start speed test - connection type multi"
            ).click()

            result = await browser.wait_for_selector(
                'div[class="result-container-speed result-container-speed-active"]',
                timeout=120000,
            )

            screenshot = await result.screenshot(omit_background=True, type="png")

            await message.delete()
            await message.respond(files=screenshot, force_type="Photo")

            await browser.close()

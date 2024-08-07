from io import BytesIO
from nicegrill import Message, TelegramClient as Client, run
from playwright.async_api import async_playwright

import os

class Speedtest:

    @run(command="speed")
    async def speedtest_by_ookla(message: Message, client: Client):
        await message.edit("<i>Speedtest is running</i>")

        async with async_playwright() as playwright:

            browser = await playwright.chromium.launch(
                args=["--start-maximized"]
            )

            browser = await browser.new_page(permissions=["geolocation"])

            await browser.goto(
                url="https://www.speedtest.net/", wait_until="networkidle"
            )

            if await (button := browser.get_by_role("button", name="I Accept")).count() == 1:
                await button.click()

            if await (button := browser.get_by_role("link", name="Back to test results")).count() == 1:
                await button.click()

            await (browser.get_by_label("start speed test - connection type multi")).click()

            result = await browser.wait_for_selector("div[class=\"result-container-speed result-container-speed-active\"]", timeout=120000)
            
            screenshot = BytesIO(
                await result.screenshot(
                    omit_background=True,
                    type="png"
                )
            )

            screenshot.name = "results.png"

            await message.delete()
            await message.respond(
                file=screenshot
            )

            await browser.close()

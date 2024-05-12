from telethon import TelegramClient as Client
from nicegrill import Message, run
from io import BytesIO
from playwright.async_api import async_playwright

import html

class Screenshot:
    
    @run(command="ss")
    async def screenshot_taker(message: Message, client: Client):
        if not message.args:
            await message.edit("<i>You need to input a URL to be taken screenshot of</i>")
            return

        await message.edit("<i>Taking a screenshot...</i>")
        
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch()
                browser = await browser.new_page(java_script_enabled=True, viewport={"width": 1920, "height": 1080})
                await browser.goto(message.args, wait_until="networkidle")
                image = BytesIO(await browser.screenshot(type="png"))
        except Exception as e:
            await message.edit(f"<i>Error: {html.escape(str(e))}</i>")
            return
    
        image.name = "screenshot.png"
    
        await message.respond(
            file=image
        )
        await message.delete()
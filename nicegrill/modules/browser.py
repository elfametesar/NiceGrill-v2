from datetime import datetime
from httpx import delete
import playwright
from playwright.async_api import async_playwright
from playwright.async_api import Page, Locator
import playwright.async_api
from telethon import TelegramClient as Client
from nicegrill import Message, run
from io import BytesIO

import asyncio
import html
import sys
import os

class Browser:

    TEXT_ELEMENTS = ["input[type='text']", "div[role='textbox']", "textbox", "textarea", "rich-textarea"]
    BUTTON_ELEMENTS = ["button", "input[role='button']", "a", "ui-button", "div[role='button']", "div[jsaction='.*']"]
    CHECKBOX_ELEMENTS = ["input[type='checkbox']"]
    RADIO_ELEMENTS = ["input[type='radio']"]

    LAST_MESSAGE: Message = None

    @run(command="act")
    async def input_text(message: Message, client: Client):
        if message.args == "exit":
            sys.stdin.write("exit")

        if not Browser.LAST_MESSAGE or message.reply_to_msg_id != Browser.LAST_MESSAGE.id:
            await message.delete()
            return
        
        sys.stdin.write(message.args)

        await message.delete()

    async def select_action(selected_obj: Locator, action):
        if not action:
            Browser.LAST_MESSAGE = await Browser.LAST_MESSAGE.edit(f"""<b>Actions

Selected Element:</b>
<blockquote>{html.escape(str(selected_obj)[:200])}</blockquote>

<b>Time:<b> <i>{datetime.now().strftime("%c")}
<i>
1 - Click
2 - Tap
3 - Double Click
4 - Check
5 - Type
6 - Clear Text
7 - Hover
8 - Focus
9 - Select Option
10 - Highlight
</i>
<b>Select an action: </b>""")

            action = int(await asyncio.to_thread(input))

        if action == 1:
            await selected_obj.click(timeout=2000)
        if action == 2:
            await selected_obj.click(timeout=2000)
        elif action == 3:
            await selected_obj.dblclick(timeout=2000)
        elif action == 4:
            await selected_obj.check(timeout=2000)
        elif action == 5:
            Browser.LAST_MESSAGE = await Browser.LAST_MESSAGE.edit(f"{Browser.LAST_MESSAGE.text}\n\n<b>Text</b>: ")

            text = ""
            for line in (await asyncio.to_thread(input)).splitlines():
                text += f"""{line.strip()}\n"""

            await selected_obj.type(text=text.strip(), timeout=2000)
        elif action == 6:
            await selected_obj.press("Control+KeyA", timeout=2000)
            await selected_obj.press("Backspace", timeout=2000)
        elif action == 7:
            await selected_obj.hover(timeout=2000)
        elif action == 8:
            await selected_obj.focus(timeout=2000)
        elif action == 9:
            menu = ""
            options = {}
            for line_no, line in enumerate((await selected_obj.text_content()).splitlines()):
                menu += f"{line_no}: {line}\n"
                options.update({str(line_no): line})

            Browser.LAST_MESSAGE = await Browser.LAST_MESSAGE.edit(f"\n<i>{menu}</i>\n<b>Select an item:</b> ")

            index = await asyncio.to_thread(input)

            await selected_obj.select_option(
                timeout=2000,
                value=options.get(index)
            )
        elif action == 10:
            await selected_obj.highlight()

    async def find_item(browser: Page, element: str):
        obj_list = []

        if element.count(" "):
            pass
        elif "text" in element:
            element = Browser.TEXT_ELEMENTS
        elif "button" in element:
            element = Browser.BUTTON_ELEMENTS
        elif "checkbox" in element:
            element = Browser.CHECKBOX_ELEMENTS
        elif "radio" in element:
            element = Browser.RADIO_ELEMENTS
        else:
            element = [element]

        for frame in browser.frames:
            if element.count(" ") == 0:
                for item in element:
                    obj_list.extend(await frame.locator(item).all())
            else:
                element, filter_text = element.split(maxsplit=1)
                obj_list.extend(await frame.locator(element).filter(has_text=filter_text).all())

        obj_list = list(enumerate(obj_list))
        menu = ""
        for index, obj in obj_list:
            if await obj.is_visible():
                label = await obj.text_content() or \
                            (await obj.inner_text(timeout=1000)).strip() or \
                            await obj.get_attribute('id') or \
                            await obj.get_attribute('url') or \
                            await obj.get_attribute('aria-label') or \
                            await obj.get_attribute('placeholder') or \
                            await obj.get_attribute("class") or str(obj)

                label = label.replace('\n', ' ').strip()[:100]
                menu += f"{index}: {label}\n"

        if not menu.strip():
            return None

        Browser.LAST_MESSAGE = await Browser.LAST_MESSAGE.edit(f"<i>{menu}</i>\n<b>Select an element: </b>")

        return obj_list[int(await asyncio.to_thread(input))][1]

    async def key_parser(key: str):
        key = key.replace(" ", "").title()

        if "up" in key.lower():
            key = "ArrowUp"
        elif "down" in key.lower():
            key = "ArrowDown"
        elif "left" in key.lower():
            key = "ArrowLeft"
        elif "right" in key.lower():
            key = "ArrowRight"

        if key.count("+") > 0:
            key_list = [key_item.title() for key_item in key.split("+")]
            key = "+".join(key_list)
        
        return key

    @run("browser")
    async def launch_firefox(message: Message, client: Client):
        await message.edit("<i>Launching browser...</i>")
        async with async_playwright() as playwright:
            browser = await playwright.firefox.launch_persistent_context(
                user_data_dir=f"{os.getenv('HOME')}/.mozilla/firefox",
                java_script_enabled=True,
                no_viewport=True,
                viewport={"width": 1920, "height": 1080},
                args=["--start-maximized"]
            )

            browser = browser.pages[0]
            asyncio.create_task(Browser.test(browser))

            await browser.goto(message.args or "https://www.google.com", wait_until="domcontentloaded")
            await message.delete()
            sys.stdin.clear()

            selected_obj = None
            while True:
                menu = f"""<b>Command List

Selected Element:</b>
<blockquote>{html.escape(str(selected_obj)[:200])}</blockquote>

<b>Time:<b> <i>{datetime.now().strftime("%c")}

1 - press [keyboard-key]
2 - goto [url] (starting with http, https, ftp...)
3 - find <html-element>
4 - actions
5 - reload - the page
6 - refresh - the screenshot
7 - exit
</i>
<b>Select an action:</b> 
{sys.stdin.read() if not sys.stdin.is_empty else ""}"""

                screenshot = BytesIO(await browser.screenshot())
                screenshot.name = "ss.jpg"

                if Browser.LAST_MESSAGE:
                    Browser.LAST_MESSAGE = await Browser.LAST_MESSAGE.edit(
                        text=menu,
                        file=await client.upload_file(file=screenshot, file_name="ss.jpg")
                    )
                else:
                    Browser.LAST_MESSAGE = await message.respond(file=screenshot, message=menu)

                try:
                    sys.stdin.clear()
                    command = await asyncio.to_thread(input)

                    if command.startswith("1") or command.lower().startswith("press "):
                        await browser.keyboard.press(
                            await Browser.key_parser(command.split()[-1])
                        )
                        continue

                    elif command.startswith("2") or command.startswith("goto "):
                        await browser.goto(command.split()[-1], wait_until="domcontentloaded")
                        continue
                    
                    elif command.startswith("3") or command.startswith("find "):
                        element = " ".join(command.split()[1:])
                        selected_obj = await Browser.find_item(browser=browser, element=element)

                        if not selected_obj:
                            await Browser.LAST_MESSAGE.edit(f"{Browser.LAST_MESSAGE.text}\n<i>No elements found</i>")
                            await asyncio.sleep(2)
                            continue

                        await Browser.select_action(selected_obj=selected_obj, action="")

                    elif command.startswith("4") or command.startswith("actions"):
                        action = ""
                        if command.count(" "):
                            action = command.split()[1]

                        if not selected_obj:
                            Browser.LAST_MESSAGE = await Browser.LAST_MESSAGE.edit(Browser.LAST_MESSAGE.text + "\n\n<i>Select an object first!</i>")
                            await asyncio.sleep(2)
                            continue

                        await Browser.select_action(selected_obj=selected_obj, action=int(action) if action else "")
                    
                    elif command == "5" or command == "reload":
                        await browser.reload(wait_until="domcontentloaded")

                    elif command == "6" or command == "refresh":
                        continue

                    elif command == "6" or command == "exit":
                        await Browser.LAST_MESSAGE.delete()
                        Browser.LAST_MESSAGE = None
                        return
                
                except ValueError:
                    print(f"\n<b>Error:</b> <i>Invalid selection</i>")
                    await asyncio.sleep(2)

                except Exception as e:
                    print(f"\n<b>Error:</b> <i>{e}</i>")
                    await asyncio.sleep(2)
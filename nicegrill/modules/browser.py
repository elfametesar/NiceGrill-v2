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

from playwright.async_api import async_playwright, Page, Locator
from quart import Quart, render_template, websocket
from nicegrill.utils import ProcessManager
from elfrien.types.patched import Message
from hypercorn.asyncio import serve
from hypercorn.config import Config
from elfrien.client import Client
from datetime import datetime
from base64 import b64encode
from nicegrill import on
from io import BytesIO

import asyncio
import html
import sys
import os

class Browser:

    """A class to handle browser automation and interaction through a web server interface."""

    HOST = Quart(__name__)

    HOST_TASK = None
    MOUSE = {"x": 0, "y": 0, "act": 0}
    URL = ""
    IMAGE_DATA = b""
    BROWSER: Page = None

    TEXT_ELEMENTS = ["input[type='text']", "div[role='textbox']", "textbox", "textarea", "rich-textarea"]
    BUTTON_ELEMENTS = ["button", "input[role='button']", "a", "ui-button", "div[role='button']", "div[jsaction='.*']"]
    CHECKBOX_ELEMENTS = ["input[type='checkbox']"]
    RADIO_ELEMENTS = ["input[type='radio']"]

    LAST_MESSAGE: Message = None

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

            action = int(await input())

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
            for line in (await input()).splitlines():
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

            index = await input()

            await selected_obj.select_option(
                timeout=2000,
                value=options.get(index)
            )
        elif action == 10:
            await selected_obj.highlight()

    async def find_item(browser: Page, element: str):
        obj_list = []

        filter_text = ""
        if (index := element.find("filter=")) != -1:
            filter_text = element[index + 7:]
            element = element.replace("filter=" + filter_text, "")

        if "text" in element:
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
            for item in element:
                obj_list.extend(await frame.locator(item).filter(has_text=filter_text).all())

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

        return obj_list[int(await input())][1]

    @on(pattern="browser")
    async def launch_firefox(client: Client, message: Message):
        """Launch the Firefox browser and navigate to a specified URL."""
        if Browser.HOST_TASK:
            await message.edit("<i>There is a running browser server, you can't use this function</i>")
            return

        await message.edit("<i>Launching browser...</i>")
        async with async_playwright() as playwright:
            Browser.BROWSER = await playwright.firefox.launch_persistent_context(
                user_data_dir=f"{os.getenv('HOME')}/.mozilla/firefox",
                java_script_enabled=True,
                no_viewport=True,
                viewport={"width": 1920, "height": 1080},
            )

            Browser.BROWSER = Browser.BROWSER.pages[0]

            await Browser.BROWSER.goto(message.raw_args or "https://www.google.com", wait_until="domcontentloaded")
            await message.delete()
            await sys.stdin.clear()

            selected_obj = None
            while True:
                menu = f"""<b>Command List

Selected Element:</b>
<blockquote>{html.escape(str(selected_obj)[:200])}</blockquote>

<b>Time:<b> <i>{datetime.now().strftime("%c")}

1 - press <a href=https://playwright.dev/docs/api/class-keyboard>[keyboard-key]</a>
2 - goto [url] (starting with http, https, ftp...)
3 - find <html-element>
4 - actions
5 - reload - the page
6 - refresh - the screenshot
7 - exit
</i>
<b>Select an action:</b> 
{await sys.stdin.read(block=False)}"""

                if Browser.BROWSER.is_closed():
                    await message.delete()
                    break

                screenshot = BytesIO(await Browser.BROWSER.screenshot())
                screenshot.name = "ss.jpg"

                if Browser.LAST_MESSAGE:
                    Browser.LAST_MESSAGE = await Browser.LAST_MESSAGE.edit(
                        message=menu,
                        file=screenshot
                    )
                else:
                    Browser.LAST_MESSAGE = await message.respond(files=screenshot, message=menu)

                ProcessManager.add_process(
                    message_id=Browser.LAST_MESSAGE.id,
                    process=sys
                )

                try:
                    await sys.stdin.clear()
                    command = await input()

                    if command.startswith("1") or command.lower().startswith("press "):
                        for key in command.split()[1:]:
                            await Browser.BROWSER.keyboard.press(key)

                        continue

                    elif command.startswith("2") or command.startswith("goto "):
                        await Browser.BROWSER.goto(command.split()[-1], wait_until="domcontentloaded")
                        continue
                    
                    elif command.startswith("3") or command.startswith("find "):
                        element = " ".join(command.split()[1:])
                        selected_obj = await Browser.find_item(browser=Browser.BROWSER, element=element)

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
                        await Browser.BROWSER.reload(wait_until="domcontentloaded")

                    elif command == "6" or command == "refresh":
                        continue

                    elif command == "7" or command == "exit":
                        await Browser.LAST_MESSAGE.delete()
                        Browser.LAST_MESSAGE = None
                        return
                
                except ValueError:
                    sys.stdin.write(f"\n<b>Error:</b> <i>Invalid selection</i>")
                    await asyncio.sleep(2)

                except Exception as e:
                    sys.stdin.write(f"\n<b>Error:</b> <i>{e}</i>")
                    await asyncio.sleep(2)

    @HOST.websocket("/ws")
    async def websocket():
        while True:
            await asyncio.sleep(0)
            await websocket.send_json({'url': Browser.URL})
            Browser.MOUSE = await websocket.receive_json()


    @on(pattern="stopweb")
    async def stop_web_server(client: Client, message: Message):
        """Stop the localhost server. It is crucial to do this before bot shuts down
        otherwise server will remain open in designated port

        Usage:
        .stopweb               # Stops the running download
        ."""
        if Browser.HOST_TASK:
            Browser.HOST_TASK.cancel()
            Browser.HOST_TASK = None
            sys.stdin.write("exit")
            await message.edit("<i>Browser server has got closed</i>")
            await asyncio.sleep(2)
            await message.delete()
        else:
            await message.edit("<i>There is no browser server running</i>")

    @on(pattern="(browser_web|bweb)")
    async def start_hosting(client: Client, message: Message):
        """Launch the browser on localhost in a simulated web browser experience

        Usage:
        .bweb <port>               # Stops the running download
        ."""
        if Browser.HOST_TASK:
            await message.edit("<i>There is already a running server</i>")
            return

        if Browser.BROWSER:
            sys.stdin.write("exit")

        port = 5000
        if message.raw_args.isdigit():
            port = int(message.raw_args)

        try:
            asyncio.create_task(Browser.browser_loop())
            
            config = Config()
            config.bind = [f"127.0.0.1:{port}"]
            Browser.HOST_TASK = asyncio.create_task(serve(Browser.HOST, config=config))

            await message.edit(f"<i>Browser server started. You can access it through http://127.0.0.1:{port}</i>")

        except Exception as e:
            await message.edit(f"<i>Failed to start the server</i>\n<b>Reason:</b> <i>{e}</i>")

    async def generate_frame():
        while True:
            frame_data = b64encode(Browser.IMAGE_DATA).decode('utf-8')
            await asyncio.sleep(0)
            yield frame_data

    @HOST.get('/frame')
    async def frame():
        async for data in Browser.generate_frame():
            return data

    @HOST.route('/')
    async def index():
        return await render_template(['index.html'])

    async def browser_loop():
        async with async_playwright() as playwright:
            Browser.BROWSER = await playwright.firefox.launch_persistent_context(
                user_data_dir=f"{os.getenv('HOME')}/.mozilla/firefox",
                java_script_enabled=True,
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15"
            )

            Browser.BROWSER = Browser.BROWSER.pages[0]
            await Browser.BROWSER.goto("https://www.google.com")

            while True:
                try:
                    x, y, act = Browser.MOUSE.values()
                    Browser.URL = Browser.BROWSER.url

                    if act == 0:
                        await Browser.BROWSER.mouse.move(x=x,y=y)
                    if act == 1:
                        await Browser.BROWSER.mouse.click(x=x, y=y)
                    elif act == 2:
                        await Browser.BROWSER.mouse.dblclick(x=x, y=y)
                    elif act == 3:
                        await Browser.BROWSER.mouse.wheel(delta_x=x, delta_y=y)
                    elif act == 4:
                        await Browser.BROWSER.go_back(timeout=4000)
                    elif act == 5:
                        await Browser.BROWSER.go_forward(timeout=4000)
                    elif act == 6:
                        asyncio.create_task(Browser.BROWSER.reload(timeout=4000))
                    elif act == 7:
                        await Browser.BROWSER.mouse.down()
                    elif act == 8:
                        await Browser.BROWSER.mouse.up()
                    elif x < 0 and y < 0:
                        if isinstance(act, str):
                            asyncio.create_task(Browser.BROWSER.goto(act, timeout=5))
                    elif isinstance(act, str):
                        await Browser.BROWSER.keyboard.press(act)

                    if not sys.stdin.is_empty and await sys.stdin.read() == "exit":
                        break

                    await asyncio.sleep(0)

                    Browser.MOUSE["act"] = act = -1
                    Browser.IMAGE_DATA = await Browser.BROWSER.screenshot(type="jpeg", quality=40, caret="initial", timeout=15000)
                except Exception:
                    pass

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
from nicegrill.utils import timeout
from elfrien.client import Client
from database import settings
from datetime import datetime
from nicegrill import on

import asyncio
import html
import sys
import os

class Misc:

    @on(pattern="restart")
    async def restart(client: Client, message: Message):
        msg = await message.edit("<i>Restarting...</i>")
        settings.set_restart_details(msg.chat_id, msg.id)
        os.execl(sys.executable, sys.executable, "-m", "nicegrill")

    @on(pattern="shutdown")
    async def shutdown(client: Client, message: Message):
        await message.edit("<i>Shutting down...</i>")
        await client.logout()

    @on(pattern="read")
    async def read(client: Client, message: Message):
        
        if not message.reply_to_text:
            await message.edit("<i>You need to reply to a document</i>")
            return
        
        await message.edit("<i>Putting on the reading glasses</i>")
        msg = message.raw_args.split()

        tail = False
        head = False

        line_count = 10

        if "tail" in msg:
            tail = True
            line_count = msg[-1] if msg[-1].isdigit() else 10
        elif "head" in msg:
            head = True
            line_count = msg[-1] if msg[-1].isdigit() else 10

        file = await message.reply_to_text.download()

        try:
            contents = file.getvalue().decode()
        except Exception as e:
            await message.edit(f"<i>File cannot be read: {str(e)}</i>")
            return

        if head:
            contents = "\n".join(contents.split("\n")[:int(line_count)])
        elif tail:
            contents = "\n".join(contents.split("\n")[-int(line_count):])

        await message.edit_stream(contents, link_preview=False)

    @on(pattern="logs")
    async def get_logs(client: Client, message: Message):
        if os.stat(path="error.txt").st_size > 0:
            await message.respond(
                files="error.txt",
                message="<b>Here's logs in ERROR level.</b>"
            )

        await message.delete()

    @on(pattern="style")
    async def style(client: Client, message: Message):
        style = message.raw_args.lower()

        if not message.reply_to_text:
            await message.delete()
            return
        try:
            if style == "n":
                await message.reply_to_text.edit(message.reply_to_text.raw_text)
            elif style == "c":
                await message.reply_to_text.edit(f"<code>{message.reply_to_text.raw_text}</code>")
            elif style == "b":
                await message.reply_to_text.edit(f"<b>{message.reply_to_text.raw_text}</b>")
            elif style == "i":
                await message.reply_to_text.edit(f"<i>{message.reply_to_text.raw_text}</i>")
            elif style == "u":
                await message.reply_to_text.edit(f"<u>{message.reply_to_text.raw_text}</u>")
            elif style == "s":
                await message.reply_to_text.edit(f"<del>{message.reply_to_text.raw_text}</del>")
            else:
                pass
        except:
            pass
        await message.delete()

    @on(pattern="dump")
    async def dump_sticker(client: Client, message: Message):
        if not message.reply_to_text or message.reply_to_text and not message.reply_to_text.sticker:
            await message.edit("<i>Reply to a sticker message</i>")
            return
        
        sticker = await message.reply_to_text.download()

        await message.delete()
        await message.respond(
            files=sticker,
            force_type="Photo"
        )
    
    @on(prefix="", pattern=r"^s(\S|[0-9]|[^a-z]).*\1.*\1.*|/.*/(,|{|}|\w|;)")
    async def sed_pattern_reader(client: Client, message: Message):
        if not message.reply_to_text:
            return

        sed_args = message.raw_text
        proc = await asyncio.create_subprocess_shell(
            cmd="sed '{}'".format(sed_args.replace("'", r"'\''")),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE
        )

        res, _ = await timeout(
            timeout=10,
            func=proc.communicate,
            input=message.reply_to_text.raw_text.encode()
        )

        if proc.returncode == 0:
            await message.reply_to_text.reply(
                "<b>SED Bot:</b> " +
                html.escape(res.decode()))

    @on(pattern="(update|update-now)")
    async def update(client: Client, message: Message):
        if message.raw_args:
            return

        if message.cmd == "update":
            current_branch = os.popen("git rev-parse --abbrev-ref HEAD").read().strip()

            await message.edit("<i>Checking...</i>")
            os.popen("git fetch")

            await asyncio.sleep(1)

            updates = os.popen(
                "git log --pretty=format:'%s - %an (%cr)' --abbrev-commit"
                f" --date=relative {current_branch}..origin/{current_branch}").readlines()

            if updates:
                ls = "<b>Updates:</b>\n\n"
                for i in updates:
                    ls += f"◍  <i>{i.capitalize()}</i>"
                await message.edit(
                    f"{ls}\n\n<b>Type</b> <i>.update now</i> <b>to update</b>")
            else:
                await message.edit("<i>Well, no updates yet</i>")
            return

        await message.edit("<i>Updating</i>")
        result = os.popen("git pull").read()

        if "up to date" not in result:
            await message.edit(f"<i>Succesfully Updated</i>")
            await asyncio.sleep(1.5)
            await Misc.restart(message, client)
        else:
            await message.edit(f"<i>{result}</i>")

    @on(pattern="time")
    async def time(client: Client, message: Message):
        await message.edit(f"<i>{datetime.now().strftime('%D %T')}</i>")
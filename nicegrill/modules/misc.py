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

from nicegrill import Message, run, event_watcher
from database import settingsdb as settings
from datetime import datetime
from telethon import TelegramClient as Client
from io import BytesIO

import os
import sys
import asyncio
import html

class Misc:

    @run(command="restart")
    async def restart(message: Message, client: Client):
        msg = await message.edit("<i>Restarting...</i>")
        settings.set_restart_details(msg.chat_id, msg.id)
        print(os.getcwd())
        os.execl(sys.executable, sys.executable, "-m", "nicegrill")


    @run(command="shutdown")
    async def shutdown(message: Message, client: Client):
        await message.edit("<i>Shutting down...</i>")
        await client.disconnect()


    @run(command="logs")
    async def logs(message: Message, client: Client):
        try:
            await client.send_file(
                entity=message.chat_id,
                file="error.txt",
                caption="<b>Here's logs in ERROR level.</b>"

            )

            await message.delete()

            with open('error.txt', 'w'):
                pass
        except:
            await message.edit("<i>There is no log in ERROR level</i>")
            return


    @run(command="(update|update-now)")
    async def update(message: Message, client: Client):
        if message.args:
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

    @run(command="read")
    async def read(message: Message, client: Client):
        
        if not message.is_reply:
            await message.edit("<i>You need to reply to a document</i>")
            return
        
        await message.edit("<i>Putting on the reading glasses</i>")
        msg = message.args.split()

        tail = False
        head = False

        line_count = 10

        if "tail" in msg:
            tail = True
            line_count = msg[-1] if msg[-1].isdigit() else 10
        elif "head" in msg:
            head = True
            line_count = msg[-1] if msg[-1].isdigit() else 10

        file = await client.download_media(message.reply_to_text, BytesIO())

        try:
            contents = file.getvalue().decode()
        except Exception as e:
            await message.edit(f"<i>File cannot be read: {e}</i>")
            return

        if head:
            contents = "\n".join(contents.split("\n")[:int(line_count)])
        elif tail:
            contents = "\n".join(contents.split("\n")[-int(line_count):])

        if len(contents) > 4000:
            await message.edit("<i>File is too big</i>")
            return

        await message.edit(contents)


    @run(command="style")
    async def style(message: Message, client: Client):
        style = message.args.lower()

        if not message.is_reply:
            await message.delete()
            return
        try:
            if style == "n":
                await message.reply_to_text.edit(message.reply_to_text.message)
            elif style == "c":
                await message.reply_to_text.edit(f"<code>{message.reply_to_text.message}</code>")
            elif style == "b":
                await message.reply_to_text.edit(f"<b>{message.reply_to_text.message}</b>")
            elif style == "i":
                await message.reply_to_text.edit(f"<i>{message.reply_to_text.message}</i>")
            elif style == "u":
                await message.reply_to_text.edit(f"<u>{message.reply_to_text.message}</u>")
            elif style == "s":
                await message.reply_to_text.edit(f"<del>{message.reply_to_text.message}</del>")
            else:
                pass
        except:
            pass
        await message.delete()


    @run(command="time")
    async def time(message: Message, client: Client):
        await message.edit(f"<i>{datetime.now().strftime('%D %T')}</i>")


    async def sed_killer(proc):
        await asyncio.sleep(10)
        try:
            proc.kill()
        except:
            pass

    @run(command="dump")
    async def dump_sticker(message: Message, client: Client):
        if not message.is_reply or (message.is_reply and not message.reply_to_text.sticker):
            await message.edit("<i>Reply to a sticker file first</i>")
            return

        await message.edit("<i>Dumping the sticker of your selection</i>")
        
        sticker_data = BytesIO()
        
        await message.reply_to_text.download_media(sticker_data)
        
        sticker_data.seek(0)
        if "video" in message.reply_to_text.sticker.mime_type:
            sticker_data.name = "sticker.mp4"
        else:
            sticker_data.name = "sticker.png"
        
        await message.delete()
        await message.reply_to_text.reply(file=sticker_data, supports_streaming=True)

    @event_watcher(pattern=r"^s(\S|[0-9]|[^a-z]).*\1.*\1.*|/.*/(,|{|}|\w|;)", incoming=False)
    async def sed_pattern_reader(message: Message, client: Client):
        if not message.reply_to_text:
            return

        sed_args = message.args
        proc = await asyncio.create_subprocess_shell(
            cmd="sed '{}'".format(sed_args.replace("'", r"'\''")),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE
        )

        asyncio.create_task(Misc.sed_killer(proc))

        res, _ = await proc.communicate(
            input=bytes(message.reply_to_text.message, "utf-8")
        )

        if proc.returncode == 0:
            await message.reply_to_text.reply(
                "<b>SED Bot:</b> " +
                html.escape(res.decode()))

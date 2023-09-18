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

from main import run, event_watcher
from database import settingsdb as settings
from datetime import datetime
from telethon import functions, TelegramClient
from telethon.tl.patched import Message
from io import BytesIO

import os
import sys
import asyncio
import html

class Misc:

    @run(command="restart")
    async def restart(message: Message, client: TelegramClient):
        msg = await message.edit("<i>Restarting...</i>")
        settings.set_restart_details(msg.chat_id, msg.id)
        os.execl(sys.executable, sys.executable, "main.py")


    @run(command="shutdown")
    async def shutdown(message: Message, client: TelegramClient):
        await message.edit("<i>Shutting down...</i>")
        await client.disconnect()


    @run(command="logs")
    async def logs(message: Message, client: TelegramClient):
        try:
            await client.send_file(entity=message.chat_id, file="error.txt",
                                        caption="<b>Here's logs in ERROR level.</b>")
            await message.delete()
            with open('error.txt', 'w'):
                pass
        except:
            await message.edit("<i>There is no log in ERROR level</i>")
            return


    @run(command="update")
    async def update(message: Message, client: TelegramClient):
        if not message.args:
            os.popen("git fetch")
            await message.edit("<i>Checking...</i>")
            await asyncio.sleep(1)
            updates = os.popen(
                "git log --pretty=format:'%s - %an (%cr)' --abbrev-commit"
                " --date=relative main..origin/main").readlines()
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
        update = os.popen("git pull").read()
        if "up to date" not in update:
            await message.edit(f"<i>Succesfully Updated</i>")
            await asyncio.sleep(1.5)
            await Misc.restart(message)
        else:
            await message.edit(f"<i>{update}</i>")


    # @run(command="asset")
    # async def asset(message: Message, client: TelegramClient):
    #     arg = message.args
    #     if arg == "make":
    #         channel = await client(
    #             functions.channels.CreateChannelRequest(
    #                 title='NiceGrill Storage(DO NOT DELETE)',
    #                 about='Storage channel for your files',
    #         ))
    #         settings.set_asset(int("-100" + str(channel.updates[1].channel_id)))
    #         await message.edit("<i>Added successfully</i>")
    #         return
    #     if not str(arg)[1:].isdigit() and arg != "make":
    #         await message.edit(f"<i>Either put an ID or type .asset make</i>")
    #         return
    #     settings.set_asset(int(arg))
    #     await message.edit("<i>Added successfully</i>")


    @run(command="read")
    async def read(message: Message, client: TelegramClient):
        
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

        file = await client.download_media(message.replied, BytesIO())

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
    async def style(message: Message, client: TelegramClient):
        style = message.args.lower()

        if not message.is_reply:
            await message.delete()
            return
        try:
            if style == "n":
                await message.replied.edit(message.replied.message)
            elif style == "c":
                await message.replied.edit(f"<code>{message.replied.message}</code>")
            elif style == "b":
                await message.replied.edit(f"<b>{message.replied.message}</b>")
            elif style == "i":
                await message.replied.edit(f"<i>{message.replied.message}</i>")
            elif style == "u":
                await message.replied.edit(f"<u>{message.replied.message}</u>")
            elif style == "s":
                await message.replied.edit(f"<del>{message.replied.message}</del>")
            else:
                pass
        except:
            pass
        await message.delete()


    @run(command="time")
    async def time(message: Message, client: TelegramClient):
        await message.edit(f"<i>{datetime.now().strftime('%D %T')}</i>")


    async def sed_killer(proc):
        await asyncio.sleep(10)
        try:
            proc.kill()
        except:
            pass

    @run(command="dump")
    async def dump_sticker(message: Message, client: TelegramClient):
        if not message.is_reply or (message.is_reply and not message.replied.sticker):
            await message.edit("<i>Reply to a sticker file first</i>")
            return

        await message.edit("<i>Dumping the sticker of your selection</i>")
        
        sticker_data = BytesIO()
        
        await message.replied.download_media(sticker_data)
        
        sticker_data.seek(0)
        if "video" in message.replied.sticker.mime_type:
            sticker_data.name = "sticker.mp4"
        else:
            sticker_data.name = "sticker.png"
        
        await message.delete()
        await message.replied.reply(file=sticker_data, supports_streaming=True)

    @event_watcher(pattern=r"^s(\S|[0-9]|[^a-z]).*\1.*\1.*|/.*/(,|{|}|\w|;)", incoming=False)
    async def sed_pattern_reader(message: Message, client: TelegramClient):
        if not message.replied:
            return

        sedArgs = message.args
        proc = await asyncio.create_subprocess_shell(
            cmd="gsed '{}'".format(sedArgs.replace("'", r"'\''")),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE
        )

        asyncio.create_task(Misc.sed_killer(proc))

        res, _ = await proc.communicate(
            input=bytes(message.replied.message, "utf-8")
        )

        if proc.returncode == 0:
            await message.replied.reply(
                "<b>SED Bot:</b> " +
                html.escape(res.decode()))

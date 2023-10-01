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

from main import run, Message
from telethon import TelegramClient as Client
from telethon.tl.types import MessageEntityUrl
from telethon.errors.rpcerrorlist import MessageTooLongError
from io import BytesIO

import utils

class FileBin:

    SERVER = "https://nekobin.com"
    PATH = "/api/documents"

    @run(command="paste")
    async def write_to_url(message: Message, client: Client):
        context = message.args

        if message.is_reply:
            
            if message.reply_to_text.document:
                document = await message.reply_to_text.download_media(file=BytesIO())
                if document.readable():
                    context = document.getvalue().decode()
            else:
                context = message.reply_to_text.message

        if not context:
            await message.edit("<i>Type in or reply to some text to paste</i>")
            return

        await message.edit("<i>Pasting..</i>")

        link = await utils.full_log(context)

        await message.edit(
            f"<i>Your text pasted successfully.\n"
            f"Here's the link: {FileBin.SERVER}/{link.json()['result'].get('key')}</i>",
            link_preview=False
        )


    @run(command="getpaste")
    async def read_from_url(message: Message, client: Client):
        links = [link for _, link in message.get_entities_text(MessageEntityUrl)]
        arg = message.args.strip()

        if message.reply_to_text:
            link = ""
            for _, link in message.reply_to_text.get_entities_text(MessageEntityUrl):
                if link.startswith(FileBin.SERVER):
                    links.append(link.replace(".com", ".com/api/documents"))
                    print(link)

        elif arg.startswith(FileBin.SERVER):
            links.append(arg)

        if not links:
            await message.edit("<i>You didn't specify a valid URL</i>")
            return

        if not arg.isdigit() or len(links) < int(arg) - 1:
            arg = -1


        raw_text = await utils.get_full_log(
            url=links[int(arg)]
        )

        if raw_text:
            raw_text = raw_text.json()["result"].get("content")
            try:
                await message.edit(raw_text)
            except MessageTooLongError:
                await utils.stream(
                    message=message,
                    res=raw_text,
                    template="",
                    exit_code="",
                    log=False
                )
        else:
            await message.edit(f"<i>God is dead: {raw_text.reason}</i>")
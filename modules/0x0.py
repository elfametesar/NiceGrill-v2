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

from main import run
from telethon.tl.types import MessageEntityUrl
from telethon.errors.rpcerrorlist import MessageTooLongError

import os
import utils

class FileBin:

    SERVER = "https://0x0.st"

    @run(command="paste")
    async def write_to_url(message, client):
        """Hell"""
        context = message.args

        if (message.replied and message.replied.document
                and message.replied.document.mime_type.startswith("text")):
            doc = await message.replied.download_media()
            with open(doc, "r") as file:
                context = file.read()
            os.remove(doc)

        elif message.is_reply and message.replied.message:
            context = message.replied.message

        if not context:
            await message.edit("<i>Type in or reply to some text to paste</i>")
            return

        await message.edit("<i>Pasting..</i>")

        link = await utils.full_log(context)

        await message.edit(
            f"<i>Your text pasted successfully.\n"
            f"Here's the link: {link.text}</i>"
                if link.text.startswith(FileBin.SERVER)
                else f"<i>{link.text}</i>"
        )


    @run(command="getpaste")
    async def read_from_url(message, client):
        links = []
        arg = message.args.strip()

        if message.is_reply:
            link = ""
            for entity in message.replied.entities:
                if isinstance(entity, MessageEntityUrl):
                    if (link := message.replied.message[
                            entity.offset: entity.offset + entity.length
                    ]) and link.startswith(FileBin.SERVER):
                        links.append(link)

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
            raw_text = raw_text.text
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


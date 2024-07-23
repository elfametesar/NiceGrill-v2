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
from elfrien.client import Client
from nicegrill import on

import httpx
import os

class Renamer:

    @on(pattern="(rn|rename)")
    async def rename_from_telegram(client: Client, message: Message):
        if not message.reply_to_text or (message.reply_to_text and not message.reply_to_text.file):
            await message.edit("<i>Reply to a message with file</i>")
            return

        if not message.raw_args:
            await message.edit("<i>Specify a new name for the file</i>")
            return

        await message.edit("<i>Downloading..</i>")

        file = await message.reply_to_text.download()

        file.name = message.raw_args

        await message.edit("<i>Renaming..</i>")
        await message.reply_to_text.reply(
            files=file,
            supports_streaming=True
        )
        await message.delete()


    @on(pattern="rndl")
    async def rename_from_url(client: Client, message: Message):
        arguments = message.raw_args.split(" ", 2)

        if len(arguments) < 2:
            await message.edit("<i>First comes the URL, then the name</i>")
            return
        
        url, new_name = arguments

        await message.edit("<i>Downloading..</i>")

        if os.path.isfile(new_name):
            os.remove(new_name)

        try:
            async with httpx.AsyncClient() as web_client:
                result = await web_client.get(url, timeout=10)

                with open("tempfile", "wb") as fd:
                    fd.write(await result.aread())

        except ValueError:
            await message.edit("<i>You did it wrong.. It's .rndl url filename </i>")
            return

        await message.edit("<i>Renaming..</i>")

        file = await client.upload_file("tempfile")
        file.name = new_name

        os.remove("tempfile")
        await message.reply_to_text.reply(
            files=file,
            supports_streaming=True
        )

        await message.delete()

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

from io import BytesIO
from telethon import TelegramClient as Client
from main import Message, run

import os
import httpx

class Renamer:

    @run(command="(rn|rename)")
    async def rename_from_telegram(message: Message, client: Client):
        if not message.is_reply or (message.reply_to_text and not message.reply_to_text.file):
            await message.edit("<i>Reply to a message with file</i>")
            return

        if not message.args:
            await message.edit("<i>Specify a new name for the file</i>")
            return

        await message.edit("<i>Downloading..</i>")

        file = await message.reply_to_text.download_media(file=BytesIO())

        file.name = message.args
        file.seek(0)

        await message.edit("<i>Renaming..</i>")
        
        await message.reply_to_text.reply(
            file=file,
            force_document=True
        )

        await message.delete()


    @run(command="rndl")
    async def rename_from_url(message: Message, client: Client):
        arguments = message.args.split(" ", 2)

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
        await client.send_file(
            entity=await message.get_chat(),
            file=file,
            force_document=True,
            support_streaming=True,
            reply_to=message.reply_to_text
        )

        await message.delete()

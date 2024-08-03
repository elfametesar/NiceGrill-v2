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

from elfrien.types.errors.variants import MessageTooLong
from elfrien.types.patched import TextEntityTypeUrl
from nicegrill.utils import up_to_bin, get_bin_url
from elfrien.types.patched import Message
from elfrien.client import Client
from nicegrill import on
from io import BytesIO


class FileBin:

    SERVER = "https://0x0.st"

    @on(pattern="paste")
    async def write_to_url(client: Client, message: Message):
        """
        Uploads text content to a pastebin-like service and returns the URL.

        Usage:
        .paste <text>        # Uploads the given text to the pastebin
        Reply with .paste    # Uploads the replied-to text or file content to the pastebin
        """
        content = message.args

        if message.reply_to_text:

            if message.reply_to_text.document:
                document: BytesIO = await message.reply_to_text.download()
                if document.readable():
                    content = document.getvalue().decode()
            else:
                content = message.reply_to_text.raw_text

        if not content:
            await message.edit("<i>Type in or reply to some text to paste</i>")
            return

        await message.edit("<i>Pasting..</i>")
        content = await up_to_bin(content)

        await message.edit(
            f"<i>Your text pasted successfully.\n"
            f"Here's the link: {content.read().decode()}</i>",
            link_preview=False,
        )

    @on(pattern="getpaste")
    async def read_from_url(client: Client, message: Message):
        """
        Fetches text content from a given URL and displays it.

        Usage:
        .getpaste <url>     # Fetches and displays the content from the given URL
        Reply with .getpaste # Fetches and displays the content from the replied-to URL
        """
        links = message.get_entities_text(TextEntityTypeUrl)
        arg = message.args.strip()

        if message.reply_to_text:
            link = ""
            for link in message.reply_to_text.get_entities_text(TextEntityTypeUrl):
                if link.startswith(FileBin.SERVER):
                    links.append(link)

        elif arg.startswith(FileBin.SERVER):
            links.append(arg)

        if not links:
            await message.edit("<i>You didn't specify a valid URL</i>")
            return

        if not arg.isdigit() or len(links) < int(arg) - 1:
            arg = -1

        response = await get_bin_url(url=links[int(arg)])

        if response.status_code == 200:
            await message.edit(response.read().decode())
        else:
            await message.edit(f"<i>God is dead: {response.reason_phrase}</i>")

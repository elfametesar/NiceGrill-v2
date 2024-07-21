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
from typing import TextIO
from nicegrill import on

import asyncio
import os

class Notepad:

    FILE_DESCRIPTORS = {}
    LENGTH_DELIMITER = 3000

    @on(pattern="edit")
    async def edit_text(client: Client, message: Message):
        """Handle the .edit command to open and edit a text file."""
        if not message.raw_args:
            await message.edit("<i>You need to specify a file in your filesystem</i>")
            return

        if not os.path.isfile(message.raw_args):
            try:
                open(message.raw_args, "w")
            except Exception as e:
                await message.edit(f"<i>Error: {e}</i>")
                return
            await message.edit(
                "<i>File doesn't exist in your filesystem, we are creating it</i>"
            )
            await asyncio.sleep(2)

        await message.delete()

        file_descriptor = open(message.raw_args, "r+")
        message_ids = []

        if not (content := file_descriptor.read().strip()):
            content = "<i>File editor is open now. Make your changes on this message and do .save on it<i>"

        content = [
            content[delim : delim + Notepad.LENGTH_DELIMITER]
            for delim in range(0, len(content), Notepad.LENGTH_DELIMITER)
        ]

        for chunk in content:
            message = await message.respond(chunk, parse_mode=None)
            message_ids.append(message.id)

        Notepad.FILE_DESCRIPTORS.update({file_descriptor: message_ids})

    async def is_fd(client: Client, message: Message) -> (str, TextIO):
        messages = []
        for file_descriptor, message_ids in Notepad.FILE_DESCRIPTORS.items():
            if message.reply_to_text.id in message_ids:
                messages = await client.get_messages(
                    entity=await message.get_chat(),
                    ids=message_ids
                )
                break

        if not messages:
            return (None, None)
        else:
            text = ""
            for msg in messages.messages:
                text += msg.raw_text

            return text, file_descriptor

    @on(pattern="save")
    async def save_file(client: Client, message: Message):
        """Handle the .save command to save the edited text back to the file."""
        text, file_descriptor = await Notepad.is_fd(message=message, client=client)

        if not file_descriptor:
            await message.edit(
                "<i>You need to reply to a message containing a file</i>"
            )
            return

        if not os.path.exists(file_descriptor.name):
            file_descriptor = open(file_descriptor.name, "w+")
            Notepad.FILE_DESCRIPTORS.update(
                {file_descriptor: Notepad.FILE_DESCRIPTORS[file_descriptor]}
            )

        try:
            file_descriptor.truncate(0)
            file_descriptor.seek(0)
            file_descriptor.write(text)
            file_descriptor.flush()
            await message.edit(
                f"<i>File successfully saved, file is still open tho</i>"
            )
        except Exception as e:
            await message.edit(f"<i>Error: {e}</i>")

    @on(pattern="close")
    async def close_file(client: Client, message: Message):
        """Handle the .close command to close the file descriptor."""
        _, file_descriptor = await Notepad.is_fd(message=message, client=client)

        if not file_descriptor:
            await message.edit(
                "<i>You need to reply to a message containing a file</i>"
            )
            return

        Notepad.FILE_DESCRIPTORS.pop(file_descriptor)
        file_descriptor.close()
        await message.edit("<i>File closed, no more edits for you</i>")

    @on(pattern="filename")
    async def get_file_name(client: Client, message: Message):
        """Handle the .filename command to get the name of the file being edited."""
        _, file_descriptor = await Notepad.is_fd(message=message, client=client)

        if not file_descriptor:
            await message.edit(
                "<i>You need to reply to a message containing a file</i>"
            )
            return

        await message.edit(
            f"<i>File name in the replied message: {file_descriptor.name}</i>"
        )

    @on(pattern="discard")
    async def discard_file(client: Client, message: Message):
        """Handle the .discard command to discard the file being edited."""
        _, file_descriptor = await Notepad.is_fd(message=message, client=client)

        if not file_descriptor:
            await message.edit(
                "<i>You need to reply to a message containing a file</i>"
            )
            return

        if not os.path.isfile(file_descriptor.name):
            await message.edit("<i>File does not exist in your filesystem</i>")
        else:
            try:
                os.remove(file_descriptor.name)
                await message.edit("<i>File discarded</i>")
            except Exception as e:
                await message.edit(f"<i>Error: {e}</i>")

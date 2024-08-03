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

from elfrien.types.functions import CreateNewSupergroupChat
from elfrien.types.patched import Message
from elfrien.client import Client
from database import settings
from nicegrill import on


class Settings:

    @on(pattern="prefix", prefix=".")
    async def set_prefix(client: Client, message: Message):
        if not message.args:
            await message.edit("<i>You need it to pass in a prefix first</i>")
            return

        settings.set_prefix(message.args)
        await message.edit(
            f"<i>Prefix has been successfully set to: {message.args}, changes will apply on restart</i>"
        )

    @on(pattern="getprefix", prefix=".")
    async def get_prefix(client: Client, message: Message):
        await message.edit(f"<i>{settings.get_prefix() or '.'}</i>")

    @on(pattern="setdb")
    async def set_new_chat(client: Client, message: Message):
        if not message.args or not message.args.isnumeric():
            await message.edit("<i>You need to input a valid chat ID</i>")
            return

        try:
            await client.get_entity(int(message.args))
            await message.edit(
                f"<i>Storage database is successfully set to </i>{message.args}"
            )
        except Exception:
            await message.edit("<i>Chat ID is not valid</i>")

    @on(pattern="newdb")
    async def create_new_chat(client: Client, message: Message):
        created_private_channel = await client(
            CreateNewSupergroupChat(
                title="NiceGrill Storage Database",
                description="Reserved for bot usage, do not manually edit.",
                is_channel=True,
                for_import=False,
                message_auto_delete_time=None,
                is_forum=None,
            )
        )

        channel_id = created_private_channel.id
        settings.set_storage_channel(channel_id)

        await message.edit("<i>You've successfully created a new storage database</i>")

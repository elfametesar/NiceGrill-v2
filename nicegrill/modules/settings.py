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

from telethon import TelegramClient as Client
from database import settingsdb as settings
from nicegrill import Message, run
from telethon.tl.functions.channels import CreateChannelRequest

class Settings:

    @run(command="prefix", prefix=".")
    async def set_prefix(message: Message, client: Client):
        if not message.args:
            await message.edit("<i>You need it to pass in a prefix first</i>")
            return

        settings.set_prefix(message.args)
        await message.edit(
            f"<i>Prefix has been successfully set to: {message.args}, changes will apply on restart</i>"
        )

    @run(command="getprefix", prefix=".")
    async def get_prefix(message: Message, client: Client):
        await message.edit(f"<i>{settings.get_prefix() or '.'}</i>")
    
    @run(command="setdb")
    async def set_new_chat(message: Message, client: Client):
        if not message.args or not message.args.isnumeric():
            await message.edit("<i>You need to input a valid chat ID</i>")
            return

        try:
            await client.get_input_entity(int(message.args))
            await message.edit(f"<i>Storage database is successfully set to </i>{message.args}")
        except Exception:
            await message.edit("<i>Chat ID is not valid</i>")

    @run(command="newdb")
    async def create_new_chat(message: Message, client: Client):
        created_private_channel = await client(
            CreateChannelRequest(
                title="NiceGrill Storage Database",
                about="Reserved for bot usage, do not manually edit.",
                broadcast=True, megagroup=True
            )
        )

        channel_id = created_private_channel.created_private_channel.chats[0].id
        settings.set_storage_channel(channel_id)

        await message.edit("<i>You've successfully created a new storage database</i>")

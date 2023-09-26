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
from main import Message, run


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
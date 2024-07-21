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
from datetime import datetime, timezone
from nicegrill import on, startup
from elfrien.client import Client
from database import alive

import platform

class Alive:

    NAME = None
    MESSAGE = None

    @on(pattern="ping")
    async def ping(client: Client, message: Message):
        """Shows you the response time between the message sent and userbot received"""
        await message.edit("<i>Ping...</i>")
        message_time = message.date
        current_time = datetime.now(tz=timezone.utc)
        await message.edit("<i>Pong... {}ms</i>"
                           .format(round((current_time - message_time).microseconds / 1000, 2)))

    @on(pattern="alive")
    async def alive(client: Client, message: Message):
        """Show off to people with my bot using this command"""
        if not Alive.NAME:
            
            Alive.NAME = "NiceGrill Bot"

        if not Alive.MESSAGE:
            Alive.MESSAGE = "Hold on, Whaa.. I'm alive 🤥🤥"

        tot = f"""
{Alive.MESSAGE}

<b>User name:</b> <i>{Alive.NAME}</i>
<b>Python version:</b> <i>{platform.python_version()}</i>
<b>Elfrien version:</b> <i>1.0</i>
<b>Current time:</b> <i>{datetime.now().strftime("%D %T")}</i>
"""

        await message.edit(tot)

    @on(pattern="setmessage")
    async def set_alive_message(client: Client, message: Message):
        """Sets your alive message"""
        if not message.raw_args:
            alive.set_alive_message("Hold on, Whaa.. I'm alive 🤥🤥")
            Alive.MESSAGE = "Hold on, Whaa.. I'm alive 🤥🤥"
            await message.edit("<i>Alive message set to default</i>")
            return

        alive.set_alive_message(message.raw_args)

        Alive.MESSAGE = message.raw_args
        await message.edit("<i>Message succesfully set</i>")


    @on(pattern="setname")
    async def set_alive_name(client: Client, message: Message):
        """Sets your alive name"""
        name = message.raw_args
        if not name:
            alive.set_alive_name("NiceGrill Bot")
            Alive.NAME = "NiceGrill Bot"
            await message.edit("<i>Alive message set to default</i>")
            return

        alive.set_alive_name(message.raw_args)

        Alive.NAME = message.raw_args
        await message.edit("<i>Name succesfully set</i>")

@startup
def load_from_database():
    Alive.NAME = alive.get_alive_name()
    Alive.MESSAGE = alive.get_alive_message()

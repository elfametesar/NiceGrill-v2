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

from database import alivedb
from datetime import datetime
from telethon.version import __version__
from telethon import TelegramClient as Client
from main import Message, run, startup

import platform


class Alive:

    NAME = None
    MESSAGE = None

    @run(command="ping")
    async def ping(message: Message, client: Client):
        """Shows you the response speed of the bot"""
        a = message.date.now()
        b = datetime.now()
        await message.edit("<i>Ping...</i>")
        await message.edit("<i>Pong... {}ms</i>"
                           .format(((b - a).microseconds / 1000), 2))

    @run(command="alive")
    async def alive(message: Message, client: Client):
        """Show off to people with my bot using this command"""
        if not Alive.NAME:
            Alive.NAME = "NiceGrill Bot"

        if not Alive.MESSAGE:
            Alive.MESSAGE = "Hold on, Whaa.. I'm alive 🤥🤥"

        tot = f"""
{Alive.MESSAGE}

<b>User name:</b> <i>{Alive.NAME}</i>
<b>Python version:</b> <i>{platform.python_version()}</i>
<b>Telethon version:</b> <i>{__version__}</i>
<b>Current time:</b> <i>{datetime.now().strftime("%D %T")}</i>
"""
        await message.edit(tot)

    @run(command="setmessage")
    async def setalive(message: Message, client: Client):
        """Sets your alive message"""
        if not message.args:
            alivedb.set_alive_message("Hold on, Whaa.. I'm alive 🤥🤥")
            Alive.MESSAGE = "Hold on, Whaa.. I'm alive 🤥🤥"
            await message.edit("<i>Alive message set to default</i>")
            return

        alivedb.set_alive_message(message.args)

        Alive.MESSAGE = message.args
        await message.edit("<i>Message succesfully set</i>")


    @run(command="setname")
    async def setname(message: Message, client: Client):
        """Sets your alive name"""
        name = message.args
        if not name:
            alivedb.set_alive_name("NiceGrill Bot")
            Alive.NAME = "NiceGrill Bot"
            await message.edit("<i>Alive message set to default</i>")
            return

        alivedb.set_alive_name(message.args)

        Alive.NAME = message.args
        await message.edit("<i>Name succesfully set</i>")

@startup
def load_from_database():
    Alive.NAME = alivedb.get_alive_name()
    Alive.MESSAGE = alivedb.get_alive_message()

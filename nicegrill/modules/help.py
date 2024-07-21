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

from nicegrill import on, HELP_BOOK, HELP_BOOK_DATA, HELP_MENU_CAPTION
from elfrien.types.patched import Message
from elfrien.client import Client

import html

class Help:

    @on(pattern="help")
    async def display_help_menu(client: Client, message: Message):
        if message.raw_args:
            await Help.help_display_command(client, message)
            return
        
        await message.edit(HELP_BOOK[:-2] + "</i>")

    async def help_display_command(client: Client, message: Message):
        if message.args in HELP_BOOK_DATA:
            if help_info := HELP_BOOK_DATA[message.args]:
                await message.edit(
f"""{HELP_MENU_CAPTION}

<b>Class/Command:</b>
<i>{message.raw_args}</i>

<b>Definition:</b>
<i>{html.escape(help_info.replace('        ', ''))}</i>"""
                )
            else:
                await message.edit("<i>No help found for this command</i>")
        else:
            await message.edit(f"<i>Command <u>{message.args}</u> does not exist</i>")

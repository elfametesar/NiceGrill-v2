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

import asyncio
from nicegrill import Message, run
from telethon import TelegramClient as Client
from urbandictionary_python import UrbanDictionary, exceptions

class Urban:

    @run(command="(ud|urban)")
    async def urban_search(message: Message, client: Client):
        """Searches through urban dictionary"""
        word = message.args
        
        if message.reply_to_text:
            word = message.reply_to_text.message

        await message.edit(f"<i>Searching for a definition for <u>{word}</u></i>")

        try:
            result = await asyncio.to_thread(UrbanDictionary, word)
        except exceptions.WordNotFound:
            await message.edit(f"<i>No definition found for <u>{word}</u></i>")
            return
        except Exception as e:
            await message.edit(f"<i>Error: {e}</i>")
            return

        await message.edit(
f"""<b>◍ Word:</b>
<i>{result.data['word']}</i>

<b>◍ Meaning:</b>
<i>{result.data['meaning']}</i>

<b>◍ Example:</b>
<i>{result.data['example']}</i>"""
        )

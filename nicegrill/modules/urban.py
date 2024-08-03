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
from udpy import UrbanClient
from nicegrill import on


class Urban:

    @on(pattern="(ud|urban)")
    async def urban_search(client: Client, message: Message):
        """Searches through urban dictionary"""
        word = message.args

        if message.reply_to_text:
            word = message.reply_to_text.raw_text

        await message.edit(f"<i>Searching for a definition for <u>{word}</u></i>")

        urban_client = UrbanClient()

        result = urban_client.get_definition(word)

        if not result:
            await message.edit(f"<i>No definition found for <u>{word}</u></i>")
            return

        result = result[0]

        await message.edit(
            f"""<b>◍ Word:</b>
<i>{word}</i>

<b>◍ Meaning:</b>
<i>{result.definition}</i>

<b>◍ Example:</b>
<i>{result.example}</i>"""
        )

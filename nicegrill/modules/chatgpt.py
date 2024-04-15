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
from nicegrill import Message, run
from g4f.client import AsyncClient as GPTClient

class ChatGPT:

    CLIENT = GPTClient()

    @run(command="chat")
    async def converse_with_chatgpt(message: Message, client: Client):
        await message.edit("<i>Getting a response</i>")

        response = await ChatGPT.CLIENT.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message.args}]
        )

        await message.edit(
f"""⚙︎ **Me: **__{message.args}__

**⚙︎ ChatGPT: **
{response.choices[0].message.content}
""",
            parse_mode="md"
        )
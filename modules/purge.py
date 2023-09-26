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

from main import Message, run
from telethon import TelegramClient as Client

import asyncio

class Purge:

    @run(command="(purge|purgeme)")
    async def purge_messages(message: Message, client: Client):
        """Perfect tool(like you 🥰) for a spring cleaning\n
    Purges the chat with a given message delete_count or until the replied message"""

        delete_count = int(message.args) + 1 if message.args.isdigit() else None

        messages = []

        chat = await message.get_chat()

        if not delete_count and not message.is_reply:
            await message.edit("<i>Enter a number and reply to a message</i>")
            return
        elif not delete_count and message.is_reply:
            delete_count = message.reply_to_text.id - 1

        await message.edit("<i>Collecting messages for batch deletion</i>")

        messages = await client.get_messages(
            entity=chat,
            from_user='me' if message.cmd == "purgeme" else None,
            limit=delete_count,
            min_id=delete_count
        )

        await message.edit("<i>Purging</i>")
        await client.delete_messages(chat, messages)

        success_message = (
            await message.respond(
                "<i>Purge has been successful. This message will disappear in 3 seconds.</i>"
            )
        )

        await asyncio.sleep(3)
        await success_message.delete()

    @run(command="del")
    async def delete(message: Message, client: Client):
        await message.delete()

        if message.is_reply:
            try:
                await message.reply_to_text.delete()
            except:
                pass

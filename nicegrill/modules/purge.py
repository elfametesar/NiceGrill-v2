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
from nicegrill import on

import asyncio

class Purge:

    @on(pattern="(purge|purgeme)")
    async def purge_messages(client: Client, message: Message):
        """Perfect tool(like you 🥰) for a spring cleaning\n
        Purges the chat with a given message delete_count or until the replied message"""

        delete_count = int(message.raw_args) + 1 if message.raw_args.isdigit() else None

        messages = []

        if not delete_count and not message.reply_to_text:
            await message.edit("<i>Enter a number and reply to a message</i>")
            return
        elif not delete_count and message.reply_to_text:
            delete_count = message.reply_to_text.id 

        await message.edit("<i>Collecting messages for batch deletion</i>")

        messages = await client.search_messages(
            entity=message.chat,
            from_user='me' if message.cmd == "purgeme" else None,
            limit=delete_count,
            until_message=delete_count
        )

        await message.edit("<i>Purging</i>")
        await client.delete_messages(
            entity=message.chat,
            message_ids=[message.id for message in messages if any([message.can_be_deleted_for_all_users, message.can_be_deleted_only_for_self])]
        )

        success_message = (
            await message.respond(
                "<i>Purge has been successful. This message will disappear in 3 seconds.</i>"
            )
        )

        await asyncio.sleep(3)

        try:
            await success_message.delete()
        except Exception:
            pass

    @on(pattern="del")
    async def delete(client: Client, message: Message):
        await message.delete()

        if message.reply_to_text:
            try:
                await message.reply_to_text.delete()
            except:
                pass

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

from database import blacklistdb as blacklist
from telethon import TelegramClient
from telethon.tl.patched import Message
from main import run, bad_chat_list

class Blacklist:

    async def get_chat_id(client, chat):
        try:
            return await client.get_peer_id(chat)
        except:
            return 0


    @run("blacklist")
    async def blacklist_chat(message, client):

        if message.args == "chats":
            await Blacklist.list_blacklist_chats(message, client)
            return

        chat = message.chat_id if not message.args else message.args
        chat = await Blacklist.get_chat_id(client, chat)

        if chat and chat in bad_chat_list:
            await message.edit("<i>This chat is already blacklisted</i>")
            return
        elif not chat:
            await message.edit(f"<i>Cannot blacklist the chat</i>")
            return

        blacklist.blacklist_chat(chat)
        bad_chat_list.append(chat)

        await message.edit("<i>This chat is now blacklisted</i>")


    async def list_blacklist_chats(message: Message, client: TelegramClient):
        chats = "<b>⬤ Blacklisted chats:</b>\n\n"
        for chat in bad_chat_list:
            try:
                chat = await client.get_entity(chat)

                if hasattr(chat, "title"):
                    name = chat.title
                    chats += f"<i><a href=https://t.me/{chat.username}>{name}</a></i>\n"
                else:
                    name = f"{chat.first_name} {chat.last_name}"
                    chats += f"<i><a href=tg://user?id={chat.id}>{name}</a></i>\n"

            except Exception as e:
                print(e)
                pass

        await message.edit(chats)


    @run(command="whitelist")
    async def whitelist_chat(message: Message, client: TelegramClient):
        chat = message.chat_id if not message.args else message.args
        chat = await Blacklist.get_chat_id(client, chat)

        if not chat:
            await message.edit("<i>Chat is not valid<i>")
            return

        if chat in bad_chat_list:
            bad_chat_list.remove(chat)
            blacklist.whitelist_chat(chat)
            await message.edit("<i>This chat is now whitelisted</i>")
        else:
            await message.edit("<i>This chat is already whitelisted</i>")

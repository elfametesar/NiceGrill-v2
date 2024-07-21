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
from nicegrill.utils import up_to_bin
from elfrien.client import Client
from datetime import datetime
from nicegrill import on

import asyncio
import re


class TelegramSearch:

    @on(pattern="search")
    async def search_telegram_messages(client: Client, message: Message):
        """
        Searches for messages in a Telegram chat based on various parameters.

        This function allows you to search for messages within a chat, filtering by user, date, query, and other parameters. 
        It supports limiting the number of results and using regular expressions for searching.

        Search Parameters:
            - chat=<chat_id_or_username>: Specifies the chat to search in. Defaults to the chat where the command was invoked.
            - limit=<number>: Limits the number of messages returned. Default is 5.
            - user=<user_id_or_username>: Filters messages sent by a specific user.
            - from_date=<YYYYMMDD>: Filters messages from this date onward.
            - year=<year>: Filters messages from a specific year.
            - month=<month>: Filters messages from a specific month.
            - day=<day>: Filters messages from a specific day.
            - regex=<pattern>: Uses a regular expression to search within messages.
            - <query>: The text query to search for in messages.

        Examples:
            .search chat=examplechat limit=10 user=exampleuser from_date=20220101 regex=\berror\b
            .search limit=5 query
        """
        kwargs = {
            "entity": message.chat_id,
            "from_user": None if not message.reply_to_text else message.reply_to_text.sender
        }
        regex = None
        query = ""
        limit = 5
        year = month = day = None

        for param in message.args.split():
            if param.startswith("chat="):
                try:
                    kwargs["entity"] = await client.get_entity(param.strip("chat="))
                except Exception:
                    pass
            elif param.startswith("limit="):
                limit = param.strip("limit=")
                if limit.isdigit():
                    limit = int(limit)
                else:
                    limit = None
            elif param.startswith("user="):
                try:
                    kwargs["from_user"] = await client.get_entity(param.strip("user="))
                except Exception:
                    pass
            elif param.startswith("from_date="):
                try:
                    kwargs["offset_date"] = datetime.fromisoformat(param.strip("from_date="))
                except Exception:
                    await message.edit("<i>Date format should be YearMonthDay, example: 20221105</i>")
                    await asyncio.sleep(2)
            elif param.startswith("year="):
                year = param.strip("year=")
            elif param.startswith("month="):
                month = param.strip("month=")
            elif param.startswith("day="):
                day = param.strip("day=")
            elif param.startswith("regex="):
                regex = param[6:]
            else:
                query += param

        kwargs["query"] = query

        search_result = ""

        await message.edit(f"<i>Searching for messages with </i><b>{query or regex or 'anything'}</b>")

        hit_counter = 0
        async for mesg in client.iter_messages(
            **kwargs,
        ):
            if year and int(year) != mesg.date.year:
                continue
            if month and int(month) != mesg.date.month:
                continue
            if day and int(day) != mesg.date.day:
                continue
            if not mesg.raw_text:
                continue

            if regex:
                if not mesg.raw_text:
                    continue

                if re_sult := re.search(regex, mesg.raw_text, re.MULTILINE):
                    query = re_sult.group(0).lower()
                else:
                    continue

            offset = mesg.raw_text.lower().find(query)
            end = offset + len(query)
            await mesg()

            found_query = mesg.raw_text[offset: end] if offset > 0 else None
            local_mesg_time = message.date
            utc_offset = local_mesg_time.strftime("%z").strip("0").replace("+0", "+")
            
            if not hasattr(mesg.chat, "first_name"):
                chat_permalink = f"<a href=https://t.me/c/{mesg.chat_id}>{mesg.chat.title}</a>"
                message_permalink = f"<a href=https://t.me/c/{mesg.chat.id}/{mesg.id}>Message</a>"
            else:
                chat_permalink = f"<a href=tg://user?id={mesg.sender_id}>{mesg.sender.first_name}</a>"
                if mesg.sender.username:
                    message_permalink = f"<a href=https://t.me/{mesg.sender.username}/{mesg.id}>Message</a>"
                else:
                    message_permalink = "User chats with no username set cannot be hyperlinked"

            search_result = f"""• <b>From: </b><a href='tg://user?id={mesg.sender_id}'>{mesg.sender.name or "Deleted Account"}</a>
• <b>Where: </b>{chat_permalink}
• <b>When: </b><i>{local_mesg_time.strftime("%F %T")} UTC{0 if utc_offset == "+" or not utc_offset else utc_offset}</i>
• <b>Message link: </b><i>{message_permalink}</i>
• <b>Message:</b>
{mesg.raw_text.replace(found_query, f"<b>{found_query}</b>") if found_query else mesg.raw_text}

""" + search_result

            if hit_counter == limit:
                break

            hit_counter += 1

        if len(search_result or "") < 4096:
            await message.edit(
                search_result or f"<i>No messages found with the query </i><b>{query or regex}</b>",
                link_preview=False
            )
        else:
            await message.edit(
                search_result[-4000:] +
                "\n\n" + 
                (await up_to_bin(search_result)).read().decode(),
                link_preview=False
            )
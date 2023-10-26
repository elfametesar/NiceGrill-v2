from telethon import TelegramClient as Client
from nicegrill import Message, run
from nicegrill.utils import full_log
from datetime import datetime

import re
import time
import asyncio


class TelegramSearch:

    @run(command="search")
    async def tester(message: Message, client: Client):

        kwargs = {
            "entity": message.chat_id,
            "from_user": None if not message.is_reply else message.reply_to_text.from_user
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

        kwargs["search"] = query

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

            found_query = mesg.raw_text[offset: end] if offset > 0 else None
            local_mesg_time = mesg.date.astimezone(datetime.now().tzinfo)
            utc_offset = int(local_mesg_time.strftime("%z").strip("0"))
            
            if not hasattr(mesg.chat, "first_name"):
                chat_permalink = f"<a href=https://t.me/c/{mesg.chat_id}>{mesg.chat.title}</a>"
                message_permalink = f"<a href=https://t.me/c/{mesg.chat.id}/{mesg.id}>Message</a>"
            else:
                chat_permalink = f"<a href=tg://user?id={mesg.sender_id}>{mesg.sender.first_name}</a>"
                if mesg.sender.username:
                    message_permalink = f"<a href=https://t.me/{mesg.sender.username}/{mesg.id}>Message</a>"
                else:
                    message_permalink = "User chats with no username set cannot be hyperlinked"

            search_result = f"""• <b>From: </b><a href='tg://user?id={mesg.sender_id}'>{mesg.sender.first_name or "Deleted Account"}</a>
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
            await message.edit(search_result or f"<i>No messages found with the query </i><b>{query or regex}</b>")
        else:
            await message.edit(
                search_result[-4000:] +
                "\n\nhttps://nekobin.com/" + 
                (await full_log(search_result)).json()['result'].get('key')
            )
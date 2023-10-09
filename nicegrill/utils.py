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
from telethon.types import User
from telethon.tl.patched import Message as MainMessage
from httpx import AsyncClient
from pprint import pformat

import asyncio
import html

class Message(MainMessage):
    
    def init(self):
        self.reply_to_text: Message|None
        self.from_user: User
        self.args: str
        self.cmd: str
        self.prefix: str

class fake_user:
    
    def __init__(self, first_name="") -> None:
        self.first_name :str = first_name
        self.last_name: str = ""
        self.title: str = ""
        self.name: str = first_name
        self.id: int = 0
        self.photo = None
    
    def __repr__(self) -> str:
        return f"User(first_name = {self.first_name}, last_name = {self.last_name})"

message_counter = 0
async def get_messages_recursively(message: Message, command=None, prefix=None, recursion_limit: int=0):

    if not message:
        return

    global message_counter
    message_counter += 1

    message.__class__.__str__ = lambda self: pformat(self.to_dict(), indent=4, sort_dicts=False)

    if message._sender:
        message._sender.__class__.__str__ = lambda self: pformat(self.to_dict(), indent=4, sort_dicts=False)
    if message.media:
        message.media.__class__.__str__ = lambda self: pformat(self.to_dict(), indent=4, sort_dicts=False)

    if command:
        message.args = get_arg(message)
    else:
        message.args = message.message

    if prefix:
        message.cmd = message.raw_text.split(" ", maxsplit=1)
        message.cmd = message.cmd[0]

    if not message.sender and not message.fwd_from:
        message._sender = await message.get_sender()

    if message.fwd_from:
        user = fake_user()

        if message.fwd_from.from_name:
            user.first_name = message.fwd_from.from_name
        else:
            if hasattr(message.fwd_from.from_id, "user_id"):
                fwd_id = message.fwd_from.from_id.user_id
            elif hasattr(message.fwd_from.from_id, "channel_id"):
                fwd_id = message.fwd_from.from_id.channel_id
            else:
                fwd_id = message.fwd_from.from_id.chat_id

            try:
                user = await message.client.get_entity(
                    entity=fwd_id
                )
            except Exception as e:
                print(e)

        message._sender = user

    message.from_user = message._sender

    if hasattr(message.from_user, "first_name"):
        message.from_user.name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    elif hasattr(message.from_user, "title"):
        message.from_user.name = f"{message.from_user.title}"

    message.reply_to_text = await message.get_reply_message()

    if message_counter > recursion_limit:
        message_counter = 0
        return message

    if message.is_reply:
        await get_messages_recursively(message.reply_to_text)
    else:
        message_counter = 0
    
    return message

async def humanize(data, time=False):
    hit_limit = 1024 if not time else 60
    magnitudes = ("bytes", "Kb", "Mb", "Gb", "Tb", "Pb") if not time \
        else ("seconds", "minutes", "hours", "days", "months", "years")

    m = 0
    while data > hit_limit and m < len(magnitudes):
        data /= hit_limit
        m += 1

    return f"{data:.2f} {magnitudes[m]}" if not time else f"{int(data)} {magnitudes[m]}"

async def get_full_log(url):
    async with AsyncClient() as session:
        content = await session.get(
            url=url,
            follow_redirects=True
        )
        return content

async def full_log(log):
    async with AsyncClient() as session:
        url = await session.post(
            url="https://nekobin.com/api/documents",
            json={
                "content": html.unescape(log),
                "title": "None",
                "Author": "Anon"
            }
        )
        return url

def strip_prefix(string: str, delimiter:str="/"):
    index = string.rfind(delimiter)
    if index != -1:
        return string[index + 1:]
    else:
        return index

async def get_user(user, client: Client):
    if user.isdigit():
        user = int(user)

    try:
        user = await client.get_entity(user)

        if not hasattr(user, "first_name"):
            raise Exception
        else:
            return user

    except Exception:
        return False

async def stream(message: Message, res, template, exit_code="", log=True):
    delim = 3900 - len(template) - len(exit_code)

    if delim < 0:
        message = await message.reply(
            f"<i>Message was too long, therefore continuing on this message</i>")
        delim = 3900
        template = ""
        await asyncio.sleep(2)

    if log and len(res) > delim:
        log_url = f"""

<b>For full log:</b> https://nekobin.com/{(await full_log(res)).json()['result'].get('key')}
        """
    else:
        log_url = ""

    res = [res[y: delim + y] for y in range(0, len(res), delim)]

    part = (await message.edit(template + f"<code>{res[0]}</code>")).text

    del[res[0]]

    for part in res:
        try:
            await asyncio.sleep(2)
            await message.edit(template + f"<code>{part}</code>")
        except:
            continue

    await message.edit(
        template +
        f"<code>{part}</code>" +
        exit_code +
        log_url
    )

async def replace_message(message: Message):
    return await message.reply(message.message.message)

def get_arg(message: Message):
    msg = message.message
    msg = msg.replace(" ", "", 1) if msg[1] == " " else msg
    split = msg[1:].replace("\n", " \n").split(" ")
    if " ".join(split[1:]).strip() == "":
        return ""
    return " ".join(split[1:])

def get_arg_split(message, char=" "):
    args = get_arg(message).split(char)
    for space in args:
        if not space.strip():
            args.remove(space)
    return args

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

import asyncio
import html
import httpx
import re


class Message(MainMessage):
    
    def init(self):
        self.reply_to_text: Message|None
        self.from_user: User
        self.args: str
        self.cmd: str
        self.prefix: str
        self.pdocument: MessageMediaDocument
        

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


class MessageMediaDocument():
    
    def __init__(self) -> None:
        self.file_name: str
        self.size: int
        self.alt: str
    
    def __repr__(self) -> str:
        repr_data = "Document("
        for key, val in self.__dict__.items():
            repr_data += f"{key}={repr(val)}, "
        return f"{repr_data[:-2]})"


async def parse_document(document: MainMessage.document):
    if not document:
        return None
    
    new_document = MessageMediaDocument()
    for key, val in document.__dict__.items():
        setattr(new_document, key, val)
    
    for attribute in document.attributes:
        for key, val in attribute.__dict__.items():
            setattr(new_document, key, val)
    
    return new_document


message_counter = 0
async def get_messages_recursively(message: Message, command=None, prefix=None):
    global message_counter
    message_counter += 1

    if message.document:
        message.pdocument = await parse_document(message.document)

    message.from_user = message.sender
    
    if command:
        message.args = get_arg(message)
    else:
        message.args = message.message

    if prefix:
        get_cmd = re.search(command + r"($| |\n)", message.message)
        if get_cmd:
            message.cmd = get_cmd.group(0).strip()

    message.from_user = message.sender
    if not message.sender and not message.fwd_from:
        try:
            message.from_user = await message.client.get_entity(message.sender_id)
        except:
            message.from_user = None
    
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

            user = await message.client.get_entity(
                entity=fwd_id
            )
        
        user.name = user.title if hasattr(user, "title") else user.first_name

        message._sender = user
        message.from_user = message.sender

    
    message.from_user.name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    message.reply_to_text = await message.get_reply_message()

    if message_counter > 4:
        message_counter = 0
        return message

    if message.is_reply:
        await get_messages_recursively(message.reply_to_text)
    
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
    async with httpx.AsyncClient() as session:
        content = await session.get(
            url=url,
            follow_redirects=True
        )
        return content

async def full_log(log):
    async with httpx.AsyncClient() as session:
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

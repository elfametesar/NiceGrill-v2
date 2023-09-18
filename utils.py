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

from telethon import TelegramClient

import asyncio
import html
import httpx
import io


async def human_readables(data=None, seconds=None):
    if data:
        magnitudes = ("bytes", "Kb", "Mb", "Gb", "Tb", "Pb")
        m = 0
        while data > 1024 and m < len(magnitudes):
            data /= 1024
            m += 1
        return f"{data:.2f} {magnitudes[m]}"
    else:
        magnitudes = ("seconds", "minutes", "hours", "days", "months", "years")
        m = 0
        while seconds > 60 and m < len(magnitudes):
            seconds //= 60
            m += 1
        return f"{seconds} {magnitudes[m]}"


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
            url="https://0x0.st",
            files={"file": (
                "log.txt",
                io.BytesIO(bytes(html.unescape(log), "utf-8"))
            )}
        )
        return url

def strip_prefix(string: str, delimiter:str="/"):
    index = string.rfind(delimiter)
    if index != -1:
        return string[index + 1:]
    else:
        return index


async def get_user(user, client: TelegramClient):
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


async def stream(message, res, template, exit_code="", log=True):
    delim = 3900 - len(template) - len(exit_code)

    if delim < 0:
        message = await message.reply(
            f"<i>Message was too long, therefore continuing on this message</i>")
        delim = 3900
        template = ""
        await asyncio.sleep(2)

    if log and len(res) > delim:
        log_url = f"""

<b>For full log:</b> {(await full_log(res)).text}
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

async def replace_message(message):
    return await message.reply(message.message.message)


def get_arg(message):
    msg = message.message.message
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

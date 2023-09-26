from main import Message, event_watcher
from telethon import TelegramClient as Client

import asyncio

class Memes:

    @event_watcher(pattern="yey|oof|://", users=639275571)
    async def watchout(message: Message, client: Client):
        if message.text.lower() == "yey" or message.text.lower() == "oof":
            for i in range(2,13):
                await message.edit(message.text[0].upper() + message.text[1] * i + message.text[2])
                await asyncio.sleep(.2)

        if message.text.lower() == "://":
            face = [ ":\\", ":/"]
            for i in range(0, 12):
                await message.edit(face[i%2])
                await asyncio.sleep(.2)

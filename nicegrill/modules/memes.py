from nicegrill import Message, event_watcher
from telethon import TelegramClient as Client

import asyncio

class Memes:

    @event_watcher(pattern="yey|oof|://", users='me')
    async def meme_watcher(message: Message, client: Client):
        if message.raw_text.lower() == "yey" or message.raw_text.lower() == "oof":
            for i in range(2,13):
                await message.edit(message.raw_text[0].upper() + message.raw_text[1] * i + message.raw_text[2])
                await asyncio.sleep(.2)

        if message.raw_text.lower() == "://":
            face = [ ":\\", ":/"]
            for i in range(0, 12):
                await message.edit(face[i%2])
                await asyncio.sleep(.2)

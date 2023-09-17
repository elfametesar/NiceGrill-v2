from main import run
from telethon import TelegramClient
from telethon.tl.types import Message

import os
import asyncio

class Notepad:
    
    FILE_DESCRIPTORS = {}
    
    @run(command="edit")
    async def edit_text(message: Message, client: TelegramClient):
        if not message.args:
            await message.edit("<i>You need to specify a file in your filesystem</i>")
            return
        
        if not os.path.isfile(message.args):
            try:
                open(message.args, "w")
            except Exception as e:
                await message.edit(f"<i>Error: {e}</i>")
                return
            await message.edit("<i>File doesn't exist in your filesystem, we are creating it</i>")
            await asyncio.sleep(2)
        
        file_descriptor = open(message.args, "r+")
        if content := file_descriptor.read().strip():
            try:
                await message.edit(content)
            except:
                file_descriptor.close()
                await message.edit("<i>File is too big, therefore cannot be edited</i>")
                return
        else:
            await message.edit("<i>File editor is open now. Make your changes on this message and do .save on it<i>")
        
        Notepad.FILE_DESCRIPTORS.update(
            {message.id: file_descriptor}
        )

    @run(command="save")
    async def save_file(message: Message, client: TelegramClient):
        if not message.is_reply or (message.is_reply and message.replied.id not in Notepad.FILE_DESCRIPTORS):
            await message.edit("<i>You need to reply to a message containing a file</i>")
            return
        
        file_descriptor = Notepad.FILE_DESCRIPTORS[message.replied.id]
        
        if not os.path.exists(file_descriptor.name):
            file_descriptor = Notepad.FILE_DESCRIPTORS[message.replied.id] = open(file_descriptor.name, "w+")

        try:
            file_descriptor.truncate(0)
            file_descriptor.seek(0)
            file_descriptor.write(message.replied.text)
            file_descriptor.flush()
            await message.edit(f"<i>File successfully saved, file is still open tho</i>")
        except Exception as e:
            await message.edit(f"<i>Error: {e}</i>")


    @run(command="close")
    async def close_file(message: Message, client: TelegramClient):
        if not message.is_reply or (message.is_reply and message.replied.id not in Notepad.FILE_DESCRIPTORS):
            await message.edit("<i>You need to reply to a message containing a file</i>")
            return
        
        Notepad.FILE_DESCRIPTORS[message.replied.id].close()
        del Notepad.FILE_DESCRIPTORS[message.replied.id]
        await message.edit("<i>File closed, no more edits for you</i>")
    
    
    @run(command="filename")
    async def get_file_name(message: Message, client: TelegramClient):
        if not message.is_reply or (message.is_reply and message.replied.id not in Notepad.FILE_DESCRIPTORS):
            await message.edit("<i>You need to reply to a message containing a file</i>")
            return
        
        await message.edit(f"<i>File name in the replied message: {Notepad.FILE_DESCRIPTORS[message.replied.id]}</i>")


    @run(command="discard")
    async def discard_file(message: Message, client: TelegramClient):
        if not message.is_reply or (message.is_reply and message.replied.id not in Notepad.FILE_DESCRIPTORS):
            await message.edit("<i>You need to reply to a message containing a file</i>")
            return
        
        file_descriptor = Notepad.FILE_DESCRIPTORS[message.replied.id]
        
        if not os.path.isfile(file_descriptor.name):
            await message.edit("<i>File does not exist in your filesystem</i>")
        else:
            try:
                os.remove(file_descriptor.name)
                await message.edit("<i>File discarded</i>")
            except Exception as e:
                await message.edit(f"<i>Error: {e}</i>")
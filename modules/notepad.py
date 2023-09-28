from telethon import TelegramClient as Client
from main import Message, run
from typing import TextIO

import os
import asyncio

class Notepad:
    
    FILE_DESCRIPTORS = {}
    LENGTH_DELIMITER = 3000
    
    @run(command="edit")
    async def edit_text(message: Message, client: Client):
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
        
        await message.delete()

        file_descriptor = open(message.args, "r+")
        message_ids = []

        if not (content := file_descriptor.read().strip()):
            content = "<i>File editor is open now. Make your changes on this message and do .save on it<i>"

        content = [content[delim: delim + Notepad.LENGTH_DELIMITER] for delim in range(0, len(content), Notepad.LENGTH_DELIMITER)]

        for chunk in content:
            message = await message.respond(chunk, parse_mode=None)
            message_ids.append(message.id)

        Notepad.FILE_DESCRIPTORS.update(
            {file_descriptor: message_ids}
        )

    async def is_fd(message: Message, client: Client) -> (str, TextIO):
        messages = []
        for file_descriptor, message_ids in Notepad.FILE_DESCRIPTORS.items():
            if message.reply_to_text.id in message_ids:
                messages = await client.get_messages(
                    entity=await message.get_chat(),
                    ids=message_ids
                )
                break
        
        if not messages:
            return (None, None)
        else:
            text = ""
            for msg in messages:
                text += msg.message

            return text, file_descriptor


    @run(command="save")
    async def save_file(message: Message, client: Client):
        text, file_descriptor = await Notepad.is_fd(
            message=message,
            client=client
        )

        if not file_descriptor:
            await message.edit("<i>You need to reply to a message containing a file</i>")
            return
        
        if not os.path.exists(file_descriptor.name):
            file_descriptor = open(file_descriptor.name, "w+")
            Notepad.FILE_DESCRIPTORS.update(
                {
                    file_descriptor: Notepad.FILE_DESCRIPTORS[file_descriptor]
                }
            )

        try:
            file_descriptor.truncate(0)
            file_descriptor.seek(0)
            file_descriptor.write(text)
            file_descriptor.flush()
            await message.edit(f"<i>File successfully saved, file is still open tho</i>")
        except Exception as e:
            await message.edit(f"<i>Error: {e}</i>")


    @run(command="close")
    async def close_file(message: Message, client: Client):
        _, file_descriptor = await Notepad.is_fd(
            message=message,
            client=client
        )

        if not file_descriptor:
            await message.edit("<i>You need to reply to a message containing a file</i>")
            return
        
        Notepad.FILE_DESCRIPTORS.pop(file_descriptor)
        file_descriptor.close()
        await message.edit("<i>File closed, no more edits for you</i>")
    
    
    @run(command="filename")
    async def get_file_name(message: Message, client: Client):
        _, file_descriptor = await Notepad.is_fd(
            message=message,
            client=client
        )

        if not file_descriptor:
            await message.edit("<i>You need to reply to a message containing a file</i>")
            return
        
        await message.edit(f"<i>File name in the replied message: {file_descriptor.name}</i>")


    @run(command="discard")
    async def discard_file(message: Message, client: Client):
        _, file_descriptor = await Notepad.is_fd(
            message=message,
            client=client
        )

        if not file_descriptor:
            await message.edit("<i>You need to reply to a message containing a file</i>")
            return
        
        if not os.path.isfile(file_descriptor.name):
            await message.edit("<i>File does not exist in your filesystem</i>")
        else:
            try:
                os.remove(file_descriptor.name)
                await message.edit("<i>File discarded</i>")
            except Exception as e:
                await message.edit(f"<i>Error: {e}</i>")
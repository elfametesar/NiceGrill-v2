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

from io import BytesIO
from telethon import TelegramClient as Client
from nicegrill import Message, run, startup
from database import settingsdb as settings
from PIL import Image
from telethon.functions import stickers, messages
from telethon import types
from telethon.utils import get_attributes
from telethon.tl.functions.messages import GetStickerSetRequest
from telethon.tl.types import InputStickerSetShortName, InputDocument, InputStickerSetID 

import math
import emoji
import random

class Stickers:

    STICKER_PACK = ""
    KANGING_STR = [
        "Ugh, fine, I'll borrow this sticker... but I'm not happy about it.",
        "Wow, so original. Mind if I, like, totally steal your vibe, hon?",
        "Guess I gotta add this sticker to my collection of 'borrowed' goods...",
        "Is this sticker, like, even that good? Whatever, I'm taking it.",
        "Damn, this sticker fire. You wouldn't happen to mind if I yoinked it, would you?",
        "Sorry, not sorry, but this sticker is coming with me. #nostealing*",
        "Distract them with that shiny object over there... *sneaks sticker into pocket*",
        "This sticker's about to get abducted by aliens... aliens named me.",
        "Hold my drink, fam. Gotta snag this epic sticker real quick.",
        "Me? Steal a sticker? Perish the thought. (Just kidding, it's mine now.)",
    ]

    @run(command="kang")
    async def steal_da_sticker(message: Message, client: Client):
        if not message.is_reply or all([message.is_reply, not message.reply_to_text.sticker, not message.reply_to_text.photo]):
            await message.edit("<i>You need to reply to a sticker</i>")
            return
        
        await message.edit(f"<i>{random.choice(Stickers.KANGING_STR)}</i>")

        sticker_emoji = ""

        for char in message.args:
            if emoji.is_emoji(char):
                sticker_emoji += char

        sticker_pack = ""
        for param in message.args.split():
            if "pack=" in param:
                sticker_pack = param[6:]
                break

        if message.reply_to_text.file.mime_type == "image/jpeg":
            sticker_file: BytesIO = await message.reply_to_text.download_media(BytesIO())
            sticker_file.name = message.reply_to_text.file.name or "sticker.jpg"
            sticker_file.seek(0)

            result = await Stickers.convert_to_sticker(
                photo=sticker_file,
                sticker_emoji=sticker_emoji,
                client=client
            )
        else:
            result = types.InputStickerSetItem(
                document=InputDocument(
                    id=message.reply_to_text.document.id,
                    access_hash=message.reply_to_text.document.access_hash,
                    file_reference=message.reply_to_text.document.file_reference
                ),
                emoji=sticker_emoji or "🤌"
            )

        try:
            stickerset = await client(
                GetStickerSetRequest(
                    stickerset=InputStickerSetShortName(
                        short_name=sticker_pack or Stickers.STICKER_PACK
                    ),
                    hash=1
                )
            )

            await client(stickers.AddStickerToSetRequest(
                stickerset=InputStickerSetID(
                    id=stickerset.set.id,
                    access_hash=stickerset.set.access_hash
                ),
                sticker=result
            ))
                
            await message.edit(f"<i>Successfully kanged. You can access to your sticker</i> <a href=https://t.me/addstickers/{stickerset.set.short_name}><i>here</i></a>")

        except Exception as e:
            await message.edit(f"<i>{e}</i>")

    async def convert_to_sticker(photo: BytesIO, client: Client, sticker_emoji=""):
        """ Resize the given photo to 512x512 """
        maxsize = (512, 512)
        with Image.open(photo) as image:
            if (image.width and image.height) < 512:
                size1 = image.width
                size2 = image.height
                if image.width > image.height:
                    scale = 512 / size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512 / size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                image = image.resize(sizenew)
            else:
                image.thumbnail(maxsize)
            
            photo = BytesIO()
            image.save(photo, format="webp")

        photo.name = "sticker.webp"
        photo.seek(0)

        photo = await client.upload_file(photo)
        attribute, mime_type = get_attributes(photo)

        media = types.InputMediaUploadedDocument(
            file=photo,
            mime_type=mime_type,
            attributes=attribute
        )

        result = await client(messages.UploadMediaRequest(
            peer='me',
            media=media,
        ))


        return types.InputStickerSetItem(
            document=InputDocument(
                id=result.document.id,
                access_hash=result.document.access_hash,
                file_reference=result.document.file_reference,
            ),
            emoji=sticker_emoji or '🤌'
        )

    @run(command="packs")
    async def list_sticker_pack(message: Message, client: Client):
        sticker_packs = ""
        await message.edit("<i>Getting sticker packs list...</i>")

        async with client.conversation(
            entity="Stickers"
        ) as convo:
            await convo.send_message("/editsticker")

            resp = await convo.get_response()

            for button in resp.buttons:
                for button in button:
                    sticker_packs += f"· <a href=https://t.me/addstickers/{button.button.text}><i>{button.button.text}</i></a>\n"

            await convo.send_message("/cancel")

            async for msg in client.iter_messages(
                entity="Stickers",
                limit=4
            ):
                await msg.delete()

            if not sticker_packs:
                await message.edit("<i>You have no sticker packs</i>")
                return

            await message.edit(
                f"""<b>Sticker Packs</b>

{sticker_packs}"""
            )

    @run(command="setpack")
    async def set_sticker_pack(message: Message, client: Client):
        if not message.args:
            await message.edit("<i>You need to input a sticker pack name, refer to .packs<i>")
            return

        Stickers.STICKER_PACK = message.args
        settings.set_sticker_pack(message.args)

        await message.edit(f"<i>Default sticker pack is now set to {message.args}</i>")

    @run(command="curpack")
    async def set_sticker_pack(message: Message, client: Client):
        await message.edit(f"<i>Current sticker pack is set to {Stickers.STICKER_PACK}</i>")

    @run(command="delpack")
    async def delete_sticker_pack(message: Message, client: Client):
        if not message.args:
            await message.edit("<i>Provide a sticker pack name</i>")
            return

        try:
            stickerset = await client(
                GetStickerSetRequest(
                    stickerset=InputStickerSetShortName(
                        short_name=message.args
                    ),
                    hash=1
                )
            )

            await client(stickers.DeleteStickerSetRequest(
                stickerset=InputStickerSetID(
                    id=stickerset.set.id,
                    access_hash=stickerset.set.access_hash
                )
            ))
            await message.edit("<i>Successfully removed</i>")
        except Exception as e:
            await message.edit(f"<i>{e}</i>")

    @run(command="delsticker")
    async def delete_sticker(message: Message, client: Client):
        if not message.is_reply:
            await message.edit("<i>Reply to a sticker</i>")
            return

        try:
            await client(stickers.RemoveStickerFromSetRequest(
                sticker=message.reply_to_text.document
            ))
            await message.edit("<i>Successfully removed</i>")
        except Exception as e:
            await message.edit(f"<i>{e}</i>")

    @run(command="newpack")
    async def make_sticker_pack(message: Message, client: Client):
        args = message.args.split(maxsplit=2, sep=", ")

        if len(args) < 2:
            await message.edit("<i>You need to input a sticker name and short name sepearated by comma (,)</i>")
            return

        if not message.is_reply or all([message.is_reply, not message.reply_to_text.sticker, not message.reply_to_text.photo]):
            await message.edit("<i>You need to reply to a sticker</i>")
            return

        sticker_name, sticker_id = args
        await message.edit("<i>Creating a new pack...</i>")

        if message.reply_to_text.file.mime_type == "image/jpeg":
            file = await message.reply_to_text.download_media(BytesIO())
            file.seek(0)
            file.name = message.reply_to_text.file.name or "sticker.jpg"

            sticker = [await Stickers.convert_to_sticker(photo=file, client=client)]
        else:
            sticker = [
                types.InputStickerSetItem(
                    InputDocument(
                        id=message.reply_to_text.document.id,
                        access_hash=message.reply_to_text.document.access_hash,
                        file_reference=message.reply_to_text.document.file_reference
                    ),
                    emoji="🤌"
                )
            ]

        try:
            await client(stickers.CreateStickerSetRequest(
                user_id='me',
                title=sticker_name,
                short_name=sticker_id,
                stickers=sticker,
                animated=True
            ))

            await message.edit(
                f'<i>"{sticker_name}" sticker pack has been created. You can access to it</i> <a href=https://t.me/addstickers/{sticker_id}>here</a>'
            )
        except Exception as e:
            await message.edit(f"<i>{e}</i>")

@startup
def load_from_database():
    Stickers.STICKER_PACK = settings.get_sticker_pack()
#    This file is part of NiceGrill.
#
#    NiceGrill is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    NiceGrill is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with NiceGrill.  If not, see <https://www.gnu.org/licenses/>.

from elfrien.types.functions import (
    AddStickerToSet, CreateNewStickerSet, DeleteStickerSet,
    RemoveStickerFromSet, GetOwnedStickerSets
)
from elfrien.types.tl import (
    StickerTypeRegular, InputSticker, StickerTypeCustomEmoji,
    InputFileId, StickerFormatTgs, StickerFormatWebm,
    StickerFormatWebp
)
from elfrien.types.patched import Message
from database import settings
from nicegrill import on, startup
from elfrien.client import Client
from io import BytesIO
from PIL import Image

import random
import emoji
import math

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

    @on(pattern="kang")
    async def steal_da_sticker(client: Client, message: Message):
        if not message.reply_to_text or not any([message.reply_to_text.sticker, message.reply_to_text.photo, message.reply_to_text.animated_emoji]):
            await message.edit("<i>You need to reply to a sticker, photo or a custom emojir</i>")
            return

        await message.edit(f"<i>{random.choice(Stickers.KANGING_STR)}</i>")

        sticker_emoji = "".join(char for char in message.raw_args if emoji.is_emoji(char))

        sticker_pack = Stickers.STICKER_PACK
        for param in message.raw_args.split():
            if param.startswith("pack="):
                sticker_pack = param[5:]
                break

        sticker_format = StickerFormatWebp()
        if message.reply_to_text.sticker:
            if message.reply_to_text.sticker.format == "tgs":
                sticker_format = StickerFormatTgs()
            if message.reply_to_text.sticker.format == "webp":
                sticker_format = StickerFormatWebp()
            else:
                sticker_format = StickerFormatWebm()

        if message.reply_to_text.file.mime_type == "image/jpeg":
            sticker_file: BytesIO = await message.reply_to_text.download()
            sticker_file.name = message.reply_to_text.file.name or "sticker.jpg"

            result = await Stickers.convert_to_sticker(
                photo=sticker_file,
                sticker_emoji=sticker_emoji,
                client=client
            )
        else:
            result = InputSticker(
                keywords=[],
                emojis=sticker_emoji or "🤌",
                format=sticker_format,
                sticker=InputFileId(
                    id=message.reply_to_text.media.file.id if not hasattr(message.reply_to_text.media.file, "file") else message.reply_to_text.media.file.file.id
                )
            )

        try:
            await client(
                AddStickerToSet(
                    sticker=result,
                    name=sticker_pack,
                    user_id=client.me.id
                )
            )

            await message.edit(
                f"<i>Successfully kanged. You can access your sticker</i> <a href='https://t.me/addstickers/{sticker_pack}'><i>here</i></a>",
                link_preview=False
            )
        except Exception as e:
            await message.edit(f"<i>{e}</i>")

    async def convert_to_sticker(photo: BytesIO, client: Client, sticker_emoji=""):
        """Resize the given photo to 512x512"""
        maxsize = (512, 512)
        with Image.open(photo) as image:
            if image.width < 512 and image.height < 512:
                size1, size2 = image.width, image.height
                if size1 > size2:
                    scale = 512 / size1
                    size1new, size2new = 512, size2 * scale
                else:
                    scale = 512 / size2
                    size1new, size2new = size1 * scale, 512
                sizenew = (math.floor(size1new), math.floor(size2new))
                image = image.resize(sizenew)
            else:
                image.thumbnail(maxsize)

            photo = BytesIO()
            image.save(photo, format="webp")

        photo.name = "sticker.webp"
        photo.seek(0)

        photo = await client.upload_file(photo, file_type="Sticker")
        await client.send_message(entity="me", files=photo, force_type="Sticker", fake_send=True)

        return InputSticker(
            keywords=[],
            emojis=sticker_emoji or '🤌',
            format=StickerFormatWebp(),
            sticker=InputFileId(
                photo.id
            )
        )

    @on(pattern="packs")
    async def list_sticker_pack(client: Client, message: Message):
        sticker_packs = ""
        await message.edit("<i>Getting sticker packs list...</i>")
        stickers = await client(GetOwnedStickerSets(limit=100, offset_sticker_set_id=0))

        for sticker_set in stickers.sets:
            sticker_packs += f"· <a href='https://t.me/addstickers/{sticker_set.name}'><i>{sticker_set.name}</i></a>\n"

        await message.edit(
            f"""<b>Sticker Packs</b>

{sticker_packs}""",
            link_preview=False
        )

    @on(pattern="setpack")
    async def set_sticker_pack(client: Client, message: Message):
        if not message.raw_args:
            await message.edit("<i>You need to input a sticker pack name, refer to .packs</i>")
            return

        Stickers.STICKER_PACK = message.raw_args
        settings.set_sticker_pack(message.raw_args)

        await message.edit(f"<i>Default sticker pack is now set to {message.raw_args}</i>")

    @on(pattern="curpack")
    async def get_current_pack(client: Client, message: Message):
        await message.edit(f"<i>Current sticker pack is set to {Stickers.STICKER_PACK}</i>")

    @on(pattern="delpack")
    async def delete_sticker_pack(client: Client, message: Message):
        if not message.raw_args:
            await message.edit("<i>Provide a sticker pack name</i>")
            return

        try:
            await client(
                DeleteStickerSet(
                    name=message.raw_args
                )
            )
            await message.edit("<i>Successfully removed</i>")
        except Exception as e:
            await message.edit(f"<i>{e}</i>")

    @on(pattern="delsticker")
    async def delete_sticker(client: Client, message: Message):
        if not message.reply_to_text or not message.reply_to_text.sticker:
            await message.edit("<i>Reply to a sticker</i>")
            return

        try:
            await client(
                RemoveStickerFromSet(
                    sticker=InputFileId(
                        id=message.reply_to_text.sticker.file.id
                    )
                )
            )
            await message.edit("<i>Successfully removed</i>")
        except Exception as e:
            await message.edit(f"<i>{e}</i>")

    @on(pattern="newpack")
    async def make_sticker_pack(client: Client, message: Message):
        args = message.raw_args.split(", ", maxsplit=2)

        if len(args) < 2:
            await message.edit("<i>You need to input a sticker name and short name separated by a comma (,)</i>")
            return

        if not message.reply_to_text or not any([message.reply_to_text.sticker, message.reply_to_text.photo, message.reply_to_text.animated_emoji]):
            await message.edit("<i>You need to reply to a sticker, photo or a custom emojir</i>")
            return

        sticker_name, sticker_id = args
        await message.edit("<i>Creating a new pack...</i>")

        if message.reply_to_text.animated_emoji:
            sticker_type = StickerTypeCustomEmoji()
        else:
            sticker_type = StickerTypeRegular()
        
        sticker_format = StickerFormatWebp()
        if message.reply_to_text.sticker:
            if message.reply_to_text.sticker.format == "tgs":
                sticker_format = StickerFormatTgs()
            if message.reply_to_text.sticker.format == "webp":
                sticker_format = StickerFormatWebp()
            else:
                sticker_format = StickerFormatWebm()

        if message.reply_to_text.file.mime_type == "image/jpeg":
            file = await message.reply_to_text.download()
            file.name = message.reply_to_text.file.name or "sticker.jpg"

            sticker = [await Stickers.convert_to_sticker(photo=file, client=client)]
        else:
            sticker = [
                InputSticker(
                    keywords=[],
                    emojis="🤌",
                    format=sticker_format,
                    sticker=InputFileId(
                        id=message.reply_to_text.media.file.id if not hasattr(message.reply_to_text.media.file, "file") else message.reply_to_text.media.file.file.id
                    )
                )
            ]

        try:
            await client(
                CreateNewStickerSet(
                    source="",
                    needs_repainting=True,
                    user_id=client.me.id,
                    title=sticker_name,
                    name=sticker_id,
                    stickers=sticker,
                    sticker_type=sticker_type
                )
            )

            await message.edit(
                f'<i>"{sticker_name}" sticker pack has been created. You can access it</i> <a href="https://t.me/addstickers/{sticker_id}">here</a>',
                link_preview=False
            )
        except Exception as e:
            await message.edit(f"<i>{e}</i>")


@startup
def load_from_database():
    Stickers.STICKER_PACK = settings.get_sticker_pack()

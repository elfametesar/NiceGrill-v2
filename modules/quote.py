from datetime import datetime
import re
from PIL import Image, ImageDraw, ImageFont
from telethon import TelegramClient
from telethon import types
from telethon.tl.patched import Message
from utils import get_user
from main import run
from io import BytesIO

import asyncio
import sys
import random
import string

string.printable += "ğşüİıçö"

class Quote:
    
    FONT_TITLE = ImageFont.truetype("/System/Volumes/Data/Users/elfa/NiceGrill/.tmp/Roboto-Medium.ttf", size=14, encoding="utf-16")
    FONT_REGULAR = ImageFont.truetype("/System/Volumes/Data/Users/elfa/NiceGrill/.tmp/Roboto-Regular.ttf", size=13, encoding="utf-16")
    FONT_MEDIUM = ImageFont.truetype("/System/Volumes/Data/Users/elfa/NiceGrill/.tmp/Roboto-Medium.ttf", size=13, encoding="utf-16")
    FONT_BOLD = ImageFont.truetype("/Users/elfa/Downloads/roboto/Roboto-Bold.ttf", size=13, encoding="utf-16")
    FONT_ITALIC = ImageFont.truetype("/System/Volumes/Data/Users/elfa/NiceGrill/.tmp/Roboto-Italic.ttf", size=13, encoding="utf-16")
    FONT_MONO = ImageFont.truetype("/Users/elfa/Downloads/Roboto_Mono/RobotoMono.ttf", size=12, encoding="utf-16")
    FONT_TIME = ImageFont.truetype("/System/Volumes/Data/Users/elfa/NiceGrill/.tmp/Roboto-Italic.ttf", size=11, encoding="utf-16")
    FONT_EMOJI = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", size=20)
    FONT_FALLBACK = ImageFont.truetype("/Users/elfa/Downloads/unifont_jp-15.0.06.ttf", size=13, encoding="utf-16")

    HEIGHT_MULTIPLIER = 17.8
    MINIMUM_BOX_HEIGHT = 70
    MINIMUM_BOX_WIDTH = 250
    LINE_SIZE_LIMIT = 350

    MESSAGE_COLOR = (50,50,50,255)
    TITLE_COLOR_PALETTE = ["#F07975", "#F49F69", "#F9C84A", "#8CC56E", "#6CC7DC", "#80C1FA", "#BCB3F9", "#E181AC"]
    
    async def get_entity_data(entities: list):
        if not entities:
            return {}

        entity_data = {}
        font = Quote.FONT_REGULAR
        entity_type = None
        for entity in entities:            
            if isinstance(entity, types.MessageEntityBold):
                font = Quote.FONT_BOLD
                entity_type = "bold"
            elif isinstance(entity, types.MessageEntityItalic):
                font = Quote.FONT_ITALIC
                entity_type = "italic"
            elif isinstance(entity, types.MessageEntityCode):
                font = Quote.FONT_MONO
                entity_type = "mono"
            elif (isinstance(entity, types.MessageEntityUrl) or
                  isinstance(entity, types.MessageEntityTextUrl)):
                entity_type = "url"
            elif isinstance(entity, types.MessageEntityUnderline):
                entity_type = "underline"

            offset = entity.offset
            length = entity.length
            
            entity_data.update(
                {
                    offset: (offset + length, font, entity_type)
                }
            )

        return entity_data


    async def get_profile_photo(client: TelegramClient, user_info) -> Image.Image:
        
        photo_buffer = BytesIO()
        await client.download_profile_photo(user_info, photo_buffer)
        
        if not photo_buffer.getbuffer():
            profile_photo = Image.new(
                mode="RGBA",
                size=(50, 50),
                color=random.choice(Quote.TITLE_COLOR_PALETTE)
            )
            
            profile_photo_draw = ImageDraw.Draw(profile_photo, "RGBA")
            
            temp_font = ImageFont.truetype(Quote.FONT_REGULAR.path, 25)
            
            profile_photo_draw.text(
                xy=(16, 12),
                text=user_info.first_name[0],
                font=temp_font,
                fill="white"
            )

            photo_buffer.name = "pfp.png"
            profile_photo.save(photo_buffer)

        profile_photo = Image.open(photo_buffer)
        profile_photo = profile_photo.resize((50, 50))
        profile_photo_canvas = Image.new("RGBA", (50, 50), (0, 0, 0, 0))

        profile_photo_mask = Image.new("L", profile_photo.size, 0)
        profile_photo_mask_draw = ImageDraw.Draw(profile_photo_mask)
        profile_photo_mask_draw.ellipse((0, 0, 48, 48), fill=255)

        profile_photo_canvas.paste(profile_photo, (0, 0), profile_photo_mask)

        return profile_photo_canvas

    
    async def draw_sticker(message_box: Image, profile_image: Image) ->Image.Image:
        sticker_image = Image.new(
            mode="RGBA",
            size=(
                message_box.width + profile_image.width + 10,
                message_box.height + profile_image.height
            ),
            color=(0,0,0,0)
        )
        
        sticker_image.paste(
            im=profile_image,
            box=(0,0)
        )
        
        sticker_image.paste(
            im=message_box,
            box=(profile_image.width, 3)
        )
        
        return sticker_image


    async def draw_message_box(text_image: Image, title: str) ->Image.Image:

        message_box_width = max(
            Quote.MINIMUM_BOX_WIDTH,
            text_image.width + 50
        )
        
        message_box_height = max(
            text_image.height + 50,
            Quote.MINIMUM_BOX_HEIGHT
        )

        message_box_image = Image.new(
            mode="RGBA",
            size=(round(message_box_width), round(message_box_height)),
            color=(0, 0, 0, 0)
        )

        box_drawer = ImageDraw.Draw(message_box_image)

        box_drawer.rounded_rectangle(
            xy=(0, 0, message_box_width, message_box_height),
            fill=Quote.MESSAGE_COLOR,
            radius=30
        )

        box_drawer.text(
            xy=(20, 14),
            text=title,
            fill=random.choice(Quote.TITLE_COLOR_PALETTE),
            font=Quote.FONT_TITLE
        )
        
        message_box_image.paste(
            im=text_image,
            box=(20, 38)
        )

        return message_box_image


    async def expand_text_box(image: Image, size: tuple) ->Image.Image:
        temp = Image.new(
            mode="RGB",
            size=size,
            color=Quote.MESSAGE_COLOR
        )
                
        temp.paste(
            im=image,
            box=(0,0)
        )
        
        temp_draw = ImageDraw.Draw(temp)

        return temp, temp_draw


    async def draw_text(text: str, entities: list[types.TypeMessageEntity]) ->Image.Image:
        entity_data = await Quote.get_entity_data(entities)
        text_box = Image.new(
            mode="RGB",
            size=(150, (text.count("\n") + 1) * round(Quote.HEIGHT_MULTIPLIER)),
            color=Quote.MESSAGE_COLOR
        )
        
        text_box_draw = ImageDraw.Draw(text_box)
        
        x = y = 0
        offset_tracker = end_offset = 0
        is_emoji = entity_type = is_fallback = False
        font = Quote.FONT_REGULAR

        for char in text:
            if sys.getsizeof(char) == 80:
                offset_tracker += 1
                is_emoji = True

            if offset_tracker in entity_data:
                end_offset, font, entity_type = entity_data[offset_tracker]                
            
            if offset_tracker >= end_offset and not is_emoji:
                font = Quote.FONT_REGULAR
                entity_type = ""

            if x + font.getlength(char) + 3 > Quote.LINE_SIZE_LIMIT:
                y += Quote.HEIGHT_MULTIPLIER
                x = 0

            if x + font.getlength(char) > text_box.width and text_box.width < Quote.LINE_SIZE_LIMIT:
                text_box, text_box_draw = await Quote.expand_text_box(
                    image=text_box,
                    size=(
                        text_box.width + (Quote.LINE_SIZE_LIMIT - text_box.width) // 2,
                        text_box.height
                    )
                )

            if Quote.HEIGHT_MULTIPLIER + y > text_box.height:
                text_box, text_box_draw = await Quote.expand_text_box(
                    image=text_box,
                    size=(text_box.width, round(text_box.height + Quote.HEIGHT_MULTIPLIER))
                )

            if entity_type == "url" or entity_type == "underline":
                width = font.getlength(char)
                height = font.getbbox("m")[3] + 2
                text_box_draw.line(
                    xy=(x + width, y + height, x, y + height),
                    width=1,
                    fill="#2576de" if entity_type == "url" else "white",
                )

            if char not in string.printable and not is_emoji:
                is_fallback = True
                
            if char == "\n":
                offset_tracker += 1
                x = 0
                y += Quote.HEIGHT_MULTIPLIER
                continue
            
            text_box_draw.text(
                xy=(
                    x,
                    y if not is_emoji else y - 1
                ),
                text=char,
                font=Quote.FONT_FALLBACK if is_fallback else Quote.FONT_EMOJI if is_emoji else font,
                embedded_color=True,
                fill="white" if entity_type != "url" else "#2576de",
            )
            
            x +=  Quote.FONT_FALLBACK.getlength(char) if is_fallback \
                    else Quote.FONT_EMOJI.getlength(char) if is_emoji \
                    else font.getlength(char)

            is_fallback = is_emoji = False
            offset_tracker += 1
            await asyncio.sleep(0)
        
        return text_box


    async def to_image(
            user_info, user_text: str, entities: list[types.TypeMessageEntity], client: TelegramClient, message_time=datetime.now()
    ):
        user_name = f"{user_info.first_name or ''} {user_info.last_name or ''}"
        
        text_box_image = await Quote.draw_text(user_text, entities)
        
        message_box = await Quote.draw_message_box(
            text_image=text_box_image,
            title=user_name
        )
        
        profile_image = await Quote.get_profile_photo(
            client=client,
            user_info=user_name
        )

        sticker_image = await Quote.draw_sticker(
            message_box=message_box,
            profile_image=profile_image
        )

        image_object = BytesIO()
        sticker_image.save(image_object, format="webp")
        image_object.name = "sticker.webp"
        image_object.seek(0)
        return image_object
    
    @run(command="quote")
    async def quote_replied_message(message: Message, client: TelegramClient):
        if not message.is_reply:
            await message.edit("<i>You need to reply to a message to quote</i>")
            return

        await message.delete()
        
        message_count = 1
        if message.args and message.args.isdigit():
            message_count = int(message.args)
        
        message_list = [message.replied]
        if message_count > 1:
            async for message_object in client.iter_messages(
                entity=await message.get_chat(),
                limit=message_count - 1,
                max_id=message.replied.id
            ):
                if message_object.text:
                    message_list.append(message_object)
        
        image_objects = []
        for message_object in message_list:
            image_objects.append(
                await Quote.to_image(
                    user_info=message_object.sender,
                    user_text=message_object.message,
                    entities=message_object.entities,
                    client=client,
                    message_time=message_object.date + (datetime.now() - datetime.utcnow())
                )
            )
            
        for obj in image_objects:
            await message.respond(file=obj)

    @run(command="fquote")
    async def fake_quote(message: Message, client: TelegramClient):
        if not message.args:
            await message.edit("<i>You need to input a username and a message attached to it in that order</i>")
            return
        
        arguments = message.args.split()
        if len(arguments) < 2:
            await message.edit("<i>Invalid arguments passed in, check the help page for usage</i>")
            return

        user_info, user_text = arguments[0], " ".join(arguments[1:])
        if not (user_info := await get_user(user_info, client)):
            await message.edit("<i>No user found by that description</i>")
            return
        
        await message.delete()
        
        image_object = await Quote.to_image(
            user_info=user_info,
            user_text=user_text,
            client=client,
            entities=[],
            message_time=message.date.now()
        )
        
        await message.respond(file=image_object)

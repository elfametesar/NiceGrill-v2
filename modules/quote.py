from datetime import datetime
import re
from PIL import Image, ImageDraw, ImageFont
from telethon import TelegramClient
from telethon import types
from telethon.tl.patched import Message
from utils import get_user
from main import run
from io import BytesIO
from utils import parse_markdown

import asyncio
import sys
import random
import string
import html

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

    MAX_LINE_SIZE = 56
    CUT_DELIMITER = 41
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


    async def text_wrapper(user_text: str):
        new_user_text = ""
        line_index_tracker = 0
        split_text = user_text.splitlines()
        html_remover = re.compile("<.*?>")

        for line in split_text:
            if len(re.sub(html_remover, '', line)) > Quote.MAX_LINE_SIZE:
                delimiter_mover = Quote.CUT_DELIMITER
                while line[delimiter_mover] not in string.punctuation:
                    if delimiter_mover < Quote.MAX_LINE_SIZE - 1:
                        delimiter_mover += 1
                    else:
                        break
                    await asyncio.sleep(0)

                line_one = line[:delimiter_mover + 1]
                line_two = line[delimiter_mover + 1:]

                split_text.insert(line_index_tracker + 1, line_one)
                if line_two:
                    split_text.insert(line_index_tracker + 2 , line_two)
                line_index_tracker += 1
                continue

            new_user_text += f"{line}\n"
            line_index_tracker += 1
            await asyncio.sleep(0)

        return new_user_text.strip()


    async def get_message_size(user_text: str, entities: dict={}):
        line_width = char_index_tracker = message_text_width = 0
        used_font = Quote.FONT_REGULAR
        entity_end = offset = -1
        
        entity_data = await Quote.get_entity_data(entities)

        for line in user_text.splitlines():
            for char in line:
                if sys.getsizeof(char) == 80:
                    used_font = Quote.FONT_EMOJI
                elif char_index_tracker in entity_data:
                    entity_end, used_font, _ = entity_data.get(char_index_tracker)
                    offset = char_index_tracker
                elif char_index_tracker not in range(offset, entity_end + 1):
                    used_font = Quote.FONT_REGULAR

                line_width += used_font.getlength(char)
                char_index_tracker += 1

            message_text_width = max(message_text_width, line_width)
            line_width = 0
        
        return message_text_width, entity_data


    async def get_profile_photo(client: TelegramClient, user_info):
        radius = 40
        
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
        
            

    async def message_as_image(user_info, user_text: str, client: TelegramClient, message_time=datetime.now()):
        user_name = f"{user_info.first_name or ''} {user_info.last_name or ''}"

        user_text = await Quote.text_wrapper(user_text)
        
        fake_message = await client.send_message(
            entity=777000,
            message=user_text
        )
        
        await fake_message.delete()
        
        user_text = fake_message.message

        user_name_width = Quote.FONT_TITLE.getlength(user_name)
        message_text_width, entity_data = await Quote.get_message_size(user_text, fake_message.entities)
        message_line_count = user_text.count("\n")

        message_box_height = max(
            (message_line_count + 1) * Quote.HEIGHT_MULTIPLIER + 50,
            70
        )

        message_box_width = max(
            user_name_width + 50,
            message_text_width + 50,
            150
        )
        
        image_file = Image.new(
            mode="RGBA", 
            size=(
                int(message_box_width),
                int(message_box_height)
            ),
            color=(0,0,0,0)
        )

        image_draw = ImageDraw.Draw(image_file)

        image_draw.rounded_rectangle(
            xy=(
                0,
                0,
                message_box_width,
                message_box_height
            ),
            fill=Quote.MESSAGE_COLOR,
            radius=30
        )

        image_draw.text(
            xy=(20, 14),
            text=user_name,
            font=Quote.FONT_MEDIUM,
            align="left",
            fill=random.choice(Quote.TITLE_COLOR_PALETTE)
        )

        start_pos_x = 20
        start_pos_y = 35

        entity_end = offset = -1
        store_old_font = emoji = entity_type = False

        index_tracker = 0
        for char in user_text:
            if sys.getsizeof(char) == 80:
                used_font = Quote.FONT_EMOJI
                emoji = True
                index_tracker += 1
            elif index_tracker in entity_data:
                entity_end, used_font, entity_type = entity_data.get(index_tracker)
                offset = index_tracker

            if index_tracker not in range(offset, entity_end) and not emoji:
                used_font = Quote.FONT_REGULAR
                entity_type = False
            
            if entity_type == "url" or entity_type == "underline":
                width = used_font.getlength(char)
                height = used_font.getbbox("m")[3] + 2
                image_draw.line(
                    xy=(start_pos_x + width, start_pos_y + height, start_pos_x, start_pos_y + height),
                    width=1,
                    fill="#2576de" if entity_type == "url" else "white",
                )

            if char not in string.printable and not emoji:
                store_old_font = used_font
                used_font = Quote.FONT_FALLBACK

            if char == "\n":
                start_pos_x = 20
                start_pos_y += Quote.HEIGHT_MULTIPLIER
                index_tracker += 1
                if store_old_font:
                    used_font = store_old_font
                    store_old_font = False
                continue

            image_draw.text(
                xy=(
                    start_pos_x,
                    start_pos_y if used_font is not Quote.FONT_EMOJI else start_pos_y - 1
                ),
                text=char,
                font=used_font,
                embedded_color=True,
                fill=None if entity_type != "url" else "#2576de"
            )

            start_pos_x += used_font.getlength(char)
            index_tracker += 1

            if store_old_font:
                used_font = store_old_font
                store_old_font = None
            
            await asyncio.sleep(0)
            emoji = False

        image_draw.text(
            xy=(
                image_file.size[0]-47,
                image_file.size[1]-20
            ),
            text=message_time.strftime("%H:%M"),
            font=Quote.FONT_TIME, 
            align="right",
            fill="gray"
        )
    
        profile_image = await Quote.get_profile_photo(client, user_info)
        
        new_image_file = Image.new(
            mode='RGBA',
            size=(
                profile_image.size[0] + 2 + image_file._size[0],
                profile_image.size[1] + image_file.size[1]
            ),
            color=(0,0,0,0)
        )
        
        new_image_file.paste(
            im=profile_image,
            box=(0,2),
        )
        
        new_image_file.paste(
            im=image_file,
            box=(
                profile_image.size[0] + 2,
                0
            )
        )

        image_object = BytesIO()
        new_image_file.save(image_object, format="webp")
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
                await Quote.message_as_image(
                    user_info=message_object.sender,
                    user_text=html.unescape(message_object.text),
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
        
        image_object = await Quote.message_as_image(
            user_info=user_info,
            user_text=html.unescape(user_text),
            client=client,
            message_time=message.date.now()
        )
        
        await message.respond(file=image_object)

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

class fake_message:
            
    def __init__(self, id, message: str, sender, client, entities=[]) -> None:
        self.id = id
        self.sender = sender
        self.first_name = sender.first_name
        self.last_name = sender.last_name or ""
        self.message = message
        self.client = client
        self.entities = entities


class Quote:
    """
    Turns Telegram messages into message box images. To use it, you need to have the fonts in your fonts/ folder in root
    directory first. You can use any fonts you want as long as they're supported. Module will be looking for these names:
    
        Roboto-Medium.ttf
        Roboto-Regular.ttf
        Roboto-Bold.ttf
        Roboto-Italic.ttf
        Roboto-Mono.ttf
        Unicode.ttf
        Apple Color Emoji.ttc

    """
    
    FONT_TITLE = ImageFont.truetype("fonts/Roboto-Medium.ttf", size=14, encoding="utf-16")
    FONT_REGULAR = ImageFont.truetype("fonts/Roboto-Regular.ttf", size=13, encoding="utf-16")
    FONT_MEDIUM = ImageFont.truetype("fonts/Roboto-Medium.ttf", size=13, encoding="utf-16")
    FONT_BOLD = ImageFont.truetype("fonts/Roboto-Bold.ttf", size=13, encoding="utf-16")
    FONT_ITALIC = ImageFont.truetype("fonts/Roboto-Italic.ttf", size=13, encoding="utf-16")
    FONT_BOLD_ITALIC = ImageFont.truetype("fonts/Roboto-Bold.ttf", size=13, encoding="utf-16")
    FONT_MONO = ImageFont.truetype("fonts/Roboto-Mono.ttf", size=12, encoding="utf-16")
    FONT_TIME = ImageFont.truetype("fonts/Roboto-Italic.ttf", size=11, encoding="utf-16")
    FONT_EMOJI = ImageFont.truetype("fonts/Apple Color Emoji.ttc", size=20)
    FONT_FALLBACK = ImageFont.truetype("fonts/Unicode.ttf", size=13, encoding="utf-16")

    LINE_HEIGHT = 17.8
    MINIMUM_BOX_HEIGHT = 45
    MINIMUM_BOX_WIDTH = 250
    MAXIMUM_BOX_WIDTH = 350

    MESSAGE_COLOR = (50,50,50,255)
    TITLE_COLOR_PALETTE = ["#F07975", "#F49F69", "#F9C84A", "#8CC56E", "#6CC7DC", "#80C1FA", "#BCB3F9", "#E181AC"]
    
    USER_COLORS = {}
    
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
                color=Quote.USER_COLORS[user_info.id]
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
                message_box.height + 10
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


    async def draw_title(user_name: str, user_id: int) ->Image.Image:

        width = Quote.FONT_TITLE.getlength(user_name)

        title_bar = Image.new(
            mode="RGB",
            size=(
                round(width),
                round(Quote.LINE_HEIGHT)
            ),
            color=Quote.MESSAGE_COLOR
        )

        title_bar_draw = ImageDraw.Draw(title_bar)
        
        title_bar_draw.text(
            xy=(0,0),
            text=user_name,
            font=Quote.FONT_TITLE,
            fill=Quote.USER_COLORS[user_id]
        )
        
        return title_bar

    async def break_text(text: str, font: ImageFont.ImageFont, offset: int=0) ->str:
        if font.getlength(text) < Quote.MAXIMUM_BOX_WIDTH:
            return text

        width = 0
        new_text = ""
        for char in text:
            
            if width + 30 + offset >= Quote.MAXIMUM_BOX_WIDTH:
                new_text += "..."
                break
            
            width += Quote.FONT_TITLE.getlength(char)
            new_text += char
        
        return new_text


    async def draw_reply_bar(name: str, text: str, message: Message=None) ->Image.Image:
        
        width = Quote.FONT_TITLE.getlength(name) + 15
        x_pos = 10


        reply_bar = Image.new(
            mode="RGB",
            size=(
                round(width),
                round(Quote.LINE_HEIGHT * 2)
            ),
            color=Quote.MESSAGE_COLOR
        )
        
        if message.media:
            thumb_file = BytesIO()
            is_document = False
            if message.sticker:
                text = " Sticker"
                await message.download_media(
                    thumb_file,
                    thumb=0,
                )
                thumb_file.seek(0)
            elif message.photo:
                text = " Photo"
                await message.download_media(
                    thumb_file,
                    thumb=0,
                )
                thumb_file.seek(0)
            elif message.video:
                text = " Video"
                await message.download_media(
                    thumb_file,
                    thumb=0,
                )
                thumb_file.seek(0)
            elif message.document:
                text = " Document"
                is_document = True
                
            if not is_document:
                thumb_file = Image.open(thumb_file)
                
                thumb_image = Image.new(
                    mode="RGBA",
                    size=(36, 36)
                )
                
                thumb_file.thumbnail((128,128))
                thumb_image.paste(
                    im=thumb_file,
                    box=(-16, -16)
                )

                reply_bar.paste(
                    im=thumb_image,
                    box=(5, 0)
                )
                
                x_pos += 40

        
        reply_bar_draw = ImageDraw.Draw(reply_bar)
        
        reply_bar_draw.text(
            xy=(x_pos,0),
            text=name,
            font=Quote.FONT_TITLE
        )
        
        reply_bar_draw.text(
            xy=(x_pos,Quote.LINE_HEIGHT),
            text=text,
            font=Quote.FONT_REGULAR
        )
        
        reply_bar_draw.line(
            xy=(0, 0, 0, reply_bar.height),
            width=2
        )

        return reply_bar


    async def draw_message_box(text_image: Image, title_image: Image.Image=None, reply_image: Image.Image=None) ->Image.Image:

        if title_image and reply_image:
            additional_sizes = 55 + 8
        elif title_image and not reply_image:
            additional_sizes = 10 + 8
        elif not title_image and reply_image:
            additional_sizes = 25 + 8
        else:
            additional_sizes = -2

        message_box_width = max(
            Quote.MINIMUM_BOX_WIDTH,
            title_image.width + 30 if title_image else 0,
            reply_image.width + 20 if reply_image else 0,
            text_image.width + 50
        )
        
        message_box_height = max(
            text_image.height,
            Quote.MINIMUM_BOX_HEIGHT
        ) + additional_sizes

        message_box_image = Image.new(
            mode="RGBA",
            size=(round(message_box_width), round(message_box_height)),
            color=(0, 0, 0, 0)
        )

        box_drawer = ImageDraw.Draw(message_box_image)
        
        y_pos = 7

        box_drawer.rounded_rectangle(
            xy=(0, 0, message_box_width, message_box_height),
            fill=Quote.MESSAGE_COLOR,
            radius=30
        )

        if title_image:
            y_pos += 4
            message_box_image.paste(
                im=title_image,
                box=(20, y_pos)
            )
            y_pos += title_image.height

        if reply_image:
            y_pos += 4
            message_box_image.paste(
                im=reply_image,
                box=(20, y_pos)
            )
            y_pos += reply_image.height
        
        message_box_image.paste(
            im=text_image,
            box=(20, y_pos + 4)
        )

        return message_box_image


    async def expand_text_box(image: Image, size: tuple, pos=(0,0)) ->Image.Image:
        temp = Image.new(
            mode="RGB",
            size=size,
            color=Quote.MESSAGE_COLOR
        )

        temp.paste(
            im=image,
            box=pos
        )
        
        temp_draw = ImageDraw.Draw(temp)

        return temp, temp_draw


    async def draw_text(text: str, entities: list[types.TypeMessageEntity]) ->Image.Image:
        entity_data = await Quote.get_entity_data(entities)
        text_box = Image.new(
            mode="RGB",
            size=(150, (text.count("\n") + 1) * round(Quote.LINE_HEIGHT)),
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

            if x + font.getlength(char) + 3 > Quote.MAXIMUM_BOX_WIDTH:
                y += Quote.LINE_HEIGHT
                x = 0

            if x + font.getlength(char) > text_box.width and text_box.width < Quote.MAXIMUM_BOX_WIDTH:
                text_box, text_box_draw = await Quote.expand_text_box(
                    image=text_box,
                    size=(
                        text_box.width + (Quote.MAXIMUM_BOX_WIDTH - text_box.width) // 2,
                        text_box.height
                    )
                )

            if Quote.LINE_HEIGHT * 2 + y + 1 > text_box.height:
                text_box, text_box_draw = await Quote.expand_text_box(
                    image=text_box,
                    size=(text_box.width, round(text_box.height + Quote.LINE_HEIGHT + 5))
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
                y += Quote.LINE_HEIGHT
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


    async def to_image(messages: list[Message]):
        
        only_first_pfp = True
        disable_title_bar = False
        max_width = total_height = 0
        sticker_list = []

        for message in messages:

            title_bar_image = reply_bar_image = None
            sender_name = await Quote.break_text(
                f"{message.sender.first_name} {message.sender.last_name or ''}",
                Quote.FONT_TITLE,
            )

            reply_message = ""
            if message.is_reply:
                reply_message = await message.get_reply_message()
                reply_sender_name = f"{reply_message.sender.first_name} {reply_message.sender.last_name or ''}"

                reply_sender_text = await Quote.break_text(
                    text=reply_message.message,
                    font=Quote.FONT_TITLE,
                    offset=20
                )

                reply_sender_name = await Quote.break_text(
                    text=reply_sender_name,
                    font=Quote.FONT_TITLE,
                    offset=20
                )

            text_box_image = await Quote.draw_text(message.message, message.entities)

            if not disable_title_bar:
                title_bar_image = await Quote.draw_title(
                    user_name=sender_name,
                    user_id=message.sender_id
                )

            if message.is_reply:
                reply_bar_image = await Quote.draw_reply_bar(
                    name=reply_sender_name,
                    text=reply_sender_text,
                    message=reply_message
                )

            message_box = await Quote.draw_message_box(
                text_image=text_box_image,
                title_image=title_bar_image,
                reply_image=reply_bar_image
            )
                        
            if only_first_pfp:
                profile_image = await Quote.get_profile_photo(
                    client=message.client,
                    user_info=message.sender
                )
            else:
                profile_image = Image.new(
                    mode="RGBA",
                    size=(50,50),
                    color=(0,0,0,0)
                )

            only_first_pfp = False
            disable_title_bar = True

            sticker_image = await Quote.draw_sticker(
                message_box=message_box,
                profile_image=profile_image
            )
            
            total_height += sticker_image.height
            max_width = max(max_width, sticker_image.width)

            sticker_list.append(sticker_image)
        
        
        combined_sticker = Image.new(
            mode="RGBA",
            size=(max_width, total_height),
            color=(0,0,0,0)
        )

        y = 0
        for sticker in sticker_list:
            combined_sticker.paste(
                im=sticker,
                box=(
                    max_width - sticker.width,
                    y
                )
            )
            y += sticker.height
        
        
        sticker_buffer = BytesIO()
        combined_sticker.save(sticker_buffer, format="webp")
        sticker_buffer.name = "sticker.webp"
        sticker_buffer.seek(0)

        return sticker_buffer
    
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
        
        if message.replied.sender_id not in Quote.USER_COLORS:
            Quote.USER_COLORS.update(
                {message.replied.sender_id: random.choice(Quote.TITLE_COLOR_PALETTE)}
            )
        
        if message_count > 1:
            async for message_object in client.iter_messages(
                entity=await message.get_chat(),
                limit=message_count - 1,
                max_id=message.replied.id,
                from_user=message.replied.sender
            ):
                if message_object.text:
                    message_list.append(message_object)
        

        message_list = reversed(message_list)
        sticker_buffer = await Quote.to_image(
            messages=message_list
        )

        await message.respond(file=sticker_buffer)

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

        fake_message_object = fake_message(
            id=user_info.id,
            message=user_text,
            sender=user_info,
            client=client
        )

        if fake_message_object.id not in Quote.USER_COLORS:
            Quote.USER_COLORS.update(
                {fake_message_object.id: random.choice(Quote.TITLE_COLOR_PALETTE)}
            )
        
        sticker_buffer = await Quote.to_image(
            [fake_message_object]
        )
        
        await message.respond(file=sticker_buffer)

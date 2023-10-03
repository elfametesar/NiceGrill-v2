from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as ImageType
from PIL.ImageFont import ImageFont as FontType
from telethon import TelegramClient as Client
from telethon import types
from database import quotedb
from utils import get_user, humanize, get_messages_recursively
from main import Message, run, startup
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
        self.sender_id = sender.id
        self.from_user = sender
        self.message = message
        self.document = None
        self.client = client
        self.entities = entities
        self.is_reply = False
        self.media = None

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
                if hasattr(entity, "size"):
                    font = Quote.FONT_TITLE
                else:
                    font = Quote.FONT_BOLD
                entity_type = "bold"
            elif isinstance(entity, types.MessageEntityItalic):
                font = Quote.FONT_ITALIC
                entity_type = "italic"
            elif isinstance(entity, types.MessageEntityCode):
                font = Quote.FONT_MONO
                entity_type = "mono"
            elif (isinstance(entity, types.MessageEntityUrl) or
                  isinstance(entity, types.MessageEntityMention) or
                  isinstance(entity, types.MessageEntityMentionName) or
                  isinstance(entity, types.InputMessageEntityMentionName) or
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


    async def get_profile_photo(client: Client, user_info) -> ImageType:
        
        photo_buffer = BytesIO()
        try:
            if not await client.download_profile_photo(user_info, photo_buffer):
                raise Exception
        except:
            profile_photo = Image.new(
                mode="RGBA",
                size=(50, 50),
                color=Quote.USER_COLORS[user_info.id]
            )
            
            profile_photo_draw = ImageDraw.Draw(profile_photo, "RGBA")
            
            temp_font = ImageFont.truetype(Quote.FONT_REGULAR.path, 25)
            
            profile_photo_draw.text(
                xy=(16, 12),
                text=user_info.name[0],
                font=temp_font,
                fill="white"
            )

            profile_photo.save(photo_buffer, format="png")

        photo_buffer.seek(0)
        profile_photo = Image.open(photo_buffer)
        profile_photo = profile_photo.resize((50, 50))
        profile_photo_canvas = Image.new("RGBA", (50, 50), (0, 0, 0, 0))

        profile_photo_mask = Image.new("L", profile_photo.size, 0)
        profile_photo_mask_draw = ImageDraw.Draw(profile_photo_mask)
        profile_photo_mask_draw.ellipse((0, 0, 48, 48), fill=255)

        profile_photo_canvas.paste(profile_photo, (0, 0), profile_photo_mask)

        return profile_photo_canvas

    
    async def draw_sticker(message_box: Image, profile_image: Image) ->ImageType:
        sticker_image = Image.new(
            mode="RGBA",
            size=(
                message_box.width + profile_image.width + 5,
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
            box=(profile_image.width + 5, 3)
        )
        
        return sticker_image

    async def break_text(text: str, font: FontType, offset: int=0, add_dot: bool=True) ->str:
        if font.getlength(text) < Quote.MAXIMUM_BOX_WIDTH:
            return text

        width = 0
        new_text = ""
        for char in text:
            
            if width + 30 + offset >= Quote.MAXIMUM_BOX_WIDTH:
                new_text += "..." if add_dot else ""
                break
            
            width += Quote.FONT_TITLE.getlength(char)
            new_text += char
        
        return new_text

    async def draw_reply_bar(name: str, text: str, message: Message, message_box_width: int) ->ImageType:

        thumb_file = None
        x_pos = 10

        if message.photo:
            text = text or "Photo"
        elif message.sticker:
            text =  f"{message.file.emoji} Sticker"
        elif message.gif:
            text = text or "GIF"
        elif message.video:
            text = text or "Video"
        elif message.audio:
            text = text or "🎵 Audio"
        elif message.voice:
            text = text or "Voice Message"
        elif message.document:
            text = text or message.file.name or "📎 Document"
        
        if message.photo or message.sticker or message.video:
            
            thumb_file = await message.download_media(
                BytesIO(),
                thumb=0,
            )

            thumb_file.seek(0)
            thumb_file = Image.open(thumb_file)
            
            thumb_file = thumb_file.resize((36,36), Image.NEAREST)

        reply_bar = Image.new(
            mode="RGBA",
            size=(
                message_box_width - 15,
                round(Quote.LINE_HEIGHT * 2) + 3
            ),
            color=Quote.MESSAGE_COLOR
        )

        reply_bar_draw = ImageDraw.Draw(reply_bar)

        name = await Quote.break_text(
            text=name,
            font=Quote.FONT_TITLE,
            offset=15 if not message.media else 30
        )
        
        text = await Quote.break_text(
            text=text,
            font=Quote.FONT_REGULAR,
            offset=15 if not message.media else 30
        )

        fake_entity = types.MessageEntityBold(offset=0, length=len(name))
        fake_entity.size = 0
        name_image = await Quote.draw_text(
            text=name,
            entities=[fake_entity],
            is_break_line=False
        )

        text_image = await Quote.draw_text(
            text=text,
            entities=message.entities
        )
        
        reply_bar_draw.line(
            xy=(0, 0, 0, reply_bar.height),
            width=2
        )
        
        if thumb_file:
            reply_bar.paste(
                im=thumb_file,
                box=(10, 2)
            )
            x_pos += 43
        
        reply_bar.paste(
            im=name_image,
            box=(x_pos, 2)
        )
        
        reply_bar.paste(
            im=text_image,
            box=(x_pos, 2 + round(Quote.LINE_HEIGHT))
        )
        
        return reply_bar

    async def draw_message_box(text_image: ImageType, message_box_width: int, title_image: ImageType=None, reply_image: ImageType=None, is_frame=True) ->ImageType:

        if title_image and reply_image:
            additional_sizes = 55 + 8
        elif title_image and not reply_image:
            additional_sizes = 10 + 8
        elif not title_image and reply_image:
            additional_sizes = 25 + 8
        else:
            additional_sizes = -2

        message_box_width += 40
        
        message_box_height = max(
            text_image.height + 5,
            Quote.MINIMUM_BOX_HEIGHT
        ) + additional_sizes

        message_box_image = Image.new(
            mode="RGBA",
            size=(round(message_box_width), round(message_box_height)),
            color=(0, 0, 0, 0)
        )

        box_drawer = ImageDraw.Draw(message_box_image)
        
        y_pos = 7
        
        if not is_frame:
            message_box_image.paste(
                im=text_image,
                box=(0, y_pos)
            )
            return message_box_image

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

    async def expand_text_box(image: ImageType, size: tuple, pos=(0,0)) ->ImageType:
        temp = Image.new(
            mode="RGBA",
            size=size,
            color=Quote.MESSAGE_COLOR
        )

        temp.paste(
            im=image,
            box=pos
        )
        
        temp_draw = ImageDraw.Draw(temp)

        return temp, temp_draw


    async def draw_text(text: str, entities: list[types.TypeMessageEntity], is_break_line: bool=True, color="white") ->Image.Image:
        
        if not text.strip():
            return Image.new(
                mode="RGBA",
                size=(0,10),
                color=(0,0,0,0)
            )
        
        entity_data = await Quote.get_entity_data(entities)
        text_box = Image.new(
            mode="RGBA",
            size=(150, (text.count("\n") + 1) * round(Quote.LINE_HEIGHT)),
            color=Quote.MESSAGE_COLOR
        )
        
        text_box_draw = ImageDraw.Draw(text_box)

        x = y = 0
        line_tracker = offset_tracker = end_offset = 0
        is_emoji = entity_type = is_fallback = False
        font = Quote.FONT_REGULAR

        for char in text:
            if offset_tracker >= end_offset:
                font = Quote.FONT_REGULAR
                entity_type = ""
            
            if sys.getsizeof(char) == 80:
                offset_tracker += 1
                is_emoji = True

            if offset_tracker in entity_data:
                end_offset, font, entity_type = entity_data[offset_tracker]                

            if x + font.getlength(char) + 3 > Quote.MAXIMUM_BOX_WIDTH:
                y += Quote.LINE_HEIGHT
                line_tracker = x = 0

            if x + font.getlength(char) > text_box.width and text_box.width < Quote.MAXIMUM_BOX_WIDTH:
                text_box, text_box_draw = await Quote.expand_text_box(
                    image=text_box,
                    size=(
                        text_box.width + (Quote.MAXIMUM_BOX_WIDTH - text_box.width) // 2,
                        text_box.height
                    )
                )

            if is_break_line:
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
                    fill="#a6d8f5" if entity_type == "url" else "white",
                )

            if char not in string.printable and not is_emoji:
                is_fallback = True
                
            if char == "\n":
                offset_tracker += 1
                line_tracker = x = 0
                y += Quote.LINE_HEIGHT
                entity_type = ""
                continue
            
            text_box_draw.text(
                xy=(
                    x,
                    y if not is_emoji else y - 1
                ),
                text=char,
                font=Quote.FONT_FALLBACK if is_fallback else Quote.FONT_EMOJI if is_emoji else font,
                embedded_color=True,
                fill=color if entity_type != "url" else "#a6d8f5",
            )
            
            x +=  Quote.FONT_FALLBACK.getlength(char) if is_fallback \
                    else Quote.FONT_EMOJI.getlength(char) if is_emoji \
                    else font.getlength(char)
                
            if is_break_line:
                if char in string.punctuation and line_tracker > 16 and line_tracker % 35 in range(0, 17):
                    line_tracker = x = 0
                    y += Quote.LINE_HEIGHT
                
                elif char in string.whitespace and line_tracker > 12 and line_tracker % 40 in range(0, 13):
                    line_tracker = x = 0
                    y += Quote.LINE_HEIGHT

            is_fallback = is_emoji = False
            offset_tracker += 1
            line_tracker += 1
            await asyncio.sleep(0)
        
        return text_box


    async def draw_link_preview(webpage_data: types.WebPage):
        site_name = await Quote.break_text(
            text=webpage_data.site_name,
            font=Quote.FONT_TITLE,
            offset=10,
            add_dot=False
        )
        
        description = f"{webpage_data.title}\n{webpage_data.description}"

        description = "\n".join(description[delim: delim + 52] \
            for delim in range(0, len(description), 52)) + "\n"

        link_preview_image = Image.new(
            mode="RGBA",
            size=(
                round(max(
                    Quote.FONT_TITLE.getlength(site_name),
                    Quote.FONT_REGULAR.getlength(description)
                )),
                f"{site_name}\n{description}".count("\n") * round(Quote.LINE_HEIGHT)
            ),
            color=Quote.MESSAGE_COLOR
        )
        
        link_preview_draw = ImageDraw.Draw(link_preview_image)
        
        link_preview_draw.text(
            xy=(10, 3),
            text=site_name,
            font=Quote.FONT_TITLE
        )

        link_preview_draw.text(
            xy=(10, 3 + Quote.LINE_HEIGHT),
            text=description,
            font=Quote.FONT_REGULAR
        )
        
        link_preview_draw.line(
            xy=(0, 0, 0, link_preview_image.height),
            width=2
        )
        
        return link_preview_image


    async def draw_media_document(message: Message):
        name, size = message.file.name, message.file.size
        size = await humanize(data=size)
        
        name = await Quote.break_text(
            text=name,
            font=Quote.FONT_TITLE,
            offset=50
        )

        width = Quote.FONT_TITLE.getlength(name) + 70

        document_bg = Image.new(
            mode="RGBA",
            size=(round(width), 45),
            color=Quote.MESSAGE_COLOR
        )

        document_draw = ImageDraw.Draw(document_bg)

        if not message.document.thumbs:
            document_draw.ellipse(
                xy=(0, 0, 45, 45),
                fill="#434343"
            )

            document_draw.text(
                xy=(18, 10),
                text="⬇",
                font=ImageFont.truetype(Quote.FONT_FALLBACK.path, 25),
                embedded_color=True,
                fill="white"
            )
        else:
            thumb_buffer = await message.download_media(thumb=-1, file=BytesIO())
            thumb_buffer.seek(0)
            thumb_buffer.name = "thumbnail.png"

            thumb_temp_image = Image.open(thumb_buffer)
            
            thumb_temp_image = thumb_temp_image.resize((45, 45))
            
            thumb_mask = Image.new(
                mode="L",
                size=thumb_temp_image.size,
                color=0
            )
            
            thumb_mask_draw = ImageDraw.Draw(thumb_mask)
            
            thumb_mask_draw.rounded_rectangle(
                xy=(0, 0, 45, 45),
                radius=7,
                fill=255
            )

            thumb_image = Image.new(
                mode="RGBA",
                size=thumb_temp_image.size,
                color=Quote.MESSAGE_COLOR
            )

            thumb_image.paste(
                im=thumb_temp_image,
                box=(0,0),
                mask=thumb_mask
            )

            document_bg.paste(
                im=thumb_image,
                box=(0,0)
            )
        
        document_draw.text((55, 7), name, font=Quote.FONT_TITLE, fill="white")
        document_draw.text(
            xy=(55, 25),
            text=str(size),
            font=Quote.FONT_REGULAR,
            fill="#AAAAAA"
        )

        return document_bg


    async def draw_media_mix(thumb_buffer: BytesIO, text_box_image: ImageType, is_captioned: bool):
        
            media_image = Image.open(thumb_buffer)
            
            message_box_image_temp = Image.new(
                mode="RGBA",
                size=(
                    media_image.width,
                    media_image.height + (text_box_image.height if is_captioned else 0)
                ),
                color=Quote.MESSAGE_COLOR
            )
            
            message_box_image_temp.paste(
                im=media_image,
                box=(0,0)
            )
            
            if is_captioned:
                message_box_image_temp.paste(
                    im=text_box_image,
                    box=(10, media_image.height + 10)
                )
            
            message_box_mask = Image.new(
                mode="L",
                size=message_box_image_temp.size,
                color=0
            )
            
            mask_draw = ImageDraw.Draw(message_box_mask)
            
            mask_draw.rounded_rectangle(
                xy=(0, 0, *message_box_image_temp.size),
                radius=20,
                fill=255
            )
            
            message_box_image = Image.new(
                mode="RGBA",
                size=message_box_image_temp.size,
                color=0
            )
            
            message_box_image.paste(
                im=message_box_image_temp,
                box=(0,0),
                mask=message_box_mask
            )
            
            return message_box_image


    async def draw_media(text_box_image: ImageType, message: Message):
        if not message.media:
            return text_box_image

        if (message.document or message.web_preview) and not message.sticker:
            if message.web_preview:
                media_image = await Quote.draw_link_preview(message.media.webpage)
                text_box_position = (0, 0)
                media_image_position = (0, round(message.raw_text.count("\n") or 1 * Quote.LINE_HEIGHT + 3))
            else:
                media_image = await Quote.draw_media_document(message)
                text_box_position = (0, media_image.height + 10)
                media_image_position = (0, 0)
            
            text_box_image, _ = await Quote.expand_text_box(
                image=text_box_image,
                size=(
                    max(text_box_image.width, media_image.width),
                    media_image.height + text_box_image.height + round(Quote.LINE_HEIGHT)
                ),
                pos=text_box_position
            )
            
            text_box_image.paste(
                im=media_image,
                box=media_image_position
            )

            return text_box_image
        else:
            
            thumb_buffer = BytesIO()

            try:
                await message.download_media(
                    file=thumb_buffer,
                    thumb=1
                )
            except:
                await message.download_media(
                    file=thumb_buffer,
                    thumb=0
                )
            finally:
                pass
            
            thumb_buffer.seek(0)
            
            return await Quote.draw_media_mix(
                thumb_buffer=thumb_buffer,
                text_box_image=text_box_image,
                is_captioned=bool(message.message)
            )


    async def to_image(messages: list[Message]):
        
        is_profile_photo = True
        is_title_bar = True
        max_width = total_height = 0
        sticker_list = []

        for message in messages:

            title_bar_image = reply_bar_image = None

            is_frame = True if (message.document and not message.sticker) or \
                (message.message and not message.media) or \
                message.audio or message.voice or message.web_preview else False

            sender_name = await Quote.break_text(
                message.from_user.name,
                Quote.FONT_TITLE,
            )

            text_box_image = await Quote.draw_text(
                text=message.message,
                entities=message.entities
            )

            text_box_image = await Quote.draw_media(
                text_box_image=text_box_image,
                message=message
            )

            if is_title_bar:
                fake_entity = types.MessageEntityBold(offset=0, length=len(sender_name))
                fake_entity.size = 0
                title_bar_image = await Quote.draw_text(
                    text=sender_name,
                    entities=[fake_entity],
                    color=Quote.USER_COLORS[message.from_user.id],
                    is_break_line=False
                )

            message_box_width = round(
                max(
                    Quote.FONT_TITLE.getlength(sender_name), 
                    Quote.FONT_REGULAR.getlength(message.reply_to_text.message) if message.is_reply else 0,
                    text_box_image.width
                )
            )

            message_box_width = min(message_box_width, Quote.MAXIMUM_BOX_WIDTH)

            if message.is_reply:
                reply_bar_image = await Quote.draw_reply_bar(
                    name=message.reply_to_text.from_user.name,
                    text=message.reply_to_text.message,
                    message=message.reply_to_text,
                    message_box_width=message_box_width
                )

            message_box = await Quote.draw_message_box(
                text_image=text_box_image,
                title_image=title_bar_image,
                reply_image=reply_bar_image,
                message_box_width=message_box_width,
                is_frame=is_frame
            )

            if is_profile_photo:
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

            is_profile_photo = False
            is_title_bar = False

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
    
    @run(command="q")
    async def quote_replied_message(message: Message, client: Client):
        if not message.is_reply:
            await message.edit("<i>You need to reply to a message to quote</i>")
            return

        await message.delete()
        
        message_count = 1
        if message.args and message.args.isdigit():
            message_count = int(message.args)
        
        message_list = []
        
        async for message_object in client.iter_messages(
            entity=await message.get_chat(),
            limit=message_count,
            max_id=message.reply_to_text.id + 1,
            from_user=message.reply_to_text.sender_id
        ):
            message_object = await get_messages_recursively(message_object)
            if message_object.sender.id not in Quote.USER_COLORS:
                Quote.USER_COLORS.update(
                    {message_object.sender.id: random.choice(Quote.TITLE_COLOR_PALETTE)}
                )

            message_list.append(message_object)
    
        message_list = reversed(message_list)
        sticker_buffer = await Quote.to_image(
            messages=message_list
        )

        await message.respond(file=sticker_buffer)

    @run(command="fq")
    async def fake_quote(message: Message, client: Client):
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
        
        if hasattr(user_info, "title"):
            await message.delete()
            return
        
        user_info.name = f"{user_info.first_name} {user_info.last_name or ''}".strip()

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


    @run(command="setcolor")
    async def set_message_color(message: Message, client: Client):
        if not message.args:
            Quote.MESSAGE_COLOR = (50,50,50,255)
            await message.edit("<i>Message box color has been set to default</i>")
            return

        arguments = message.args.split()
        color = None

        if len(arguments) > 3 and "".join(arguments).isdigit():
            r,g,b,a = int(arguments[0]), int(arguments[1]), int(arguments[2]), int(arguments[3])
            color = (r, g, b, a)
        elif message.args.startswith("#"):
            color = message.args
        else:
            color = message.args
        
        tester_image = Image.new(
            mode="RGBA",
            size=(50, 50)
        )
        
        tester_draw = ImageDraw.Draw(tester_image)
        
        try:
            tester_draw.text(
                xy=(0,0),
                text="a",
                fill=color
            )

            quotedb.set_message_color(color)
            Quote.MESSAGE_COLOR = color
            await message.edit(f"<i>Message box color has been set to {color}</i>")
        except Exception as e:
            await message.edit(f"<i>{e}</i>")

@startup
def load_from_database():
    Quote.MESSAGE_COLOR = quotedb.get_message_color()
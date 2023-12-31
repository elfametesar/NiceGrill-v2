from PIL import Image, ImageDraw, ImageFont, ImageFilter
from PIL.Image import Image as ImageType
from PIL.ImageFont import ImageFont as FontType
from telethon import TelegramClient as Client
from telethon import types
from database import quotedb
from nicegrill.utils import get_user, humanize, get_messages_recursively
from nicegrill import Message, run, startup
from io import BytesIO

import random
import string
import emoji

string.printable += "ğşüİıçö"


class FakeMessage:
    def __init__(self, message_id, message: str, sender, client, entities=[]) -> None:
        self.id = message_id
        self.sender = sender
        self.sender_id = sender.id
        self.from_user = sender
        self.raw_text = message
        self.document = None
        self.client = client
        self.entities = entities
        self.is_reply = False
        self.media = None
        self.photo = None
        self.video = None
        self.sticker = None
        self.audio = None
        self.voice = None


class Quote:

    FONT_TITLE = ImageFont.truetype(font="fonts/Roboto-Medium.ttf", size=14)
    FONT_REGULAR = ImageFont.truetype(font="fonts/Roboto-Regular.ttf", size=13)
    FONT_MEDIUM = ImageFont.truetype(font="fonts/Roboto-Medium.ttf", size=13)
    FONT_BOLD = ImageFont.truetype(font="fonts/Roboto-Bold.ttf", size=13)
    FONT_ITALIC = ImageFont.truetype(font="fonts/Roboto-Italic.ttf", size=13)
    FONT_BOLD_ITALIC = ImageFont.truetype(font="fonts/Roboto-Bold.ttf", size=13)
    FONT_MONO = ImageFont.truetype(font="fonts/Roboto-Mono.ttf", size=12)
    FONT_EMOJI = ImageFont.truetype(font="fonts/Apple Color Emoji.ttc",size=20)
    FONT_FALLBACK = ImageFont.truetype(font="fonts/Unicode.ttf", size=13)

    LINE_HEIGHT = 18
    MAXIMUM_BOX_WIDTH = 300
    MINIMUM_BOX_WIDTH = 80

    USER_COLORS = {}
    MESSAGE_COLOR = (50, 50, 50, 255)
    TITLE_COLOR_PALETTE = [
        "#F07975",
        "#F49F69",
        "#F9C84A",
        "#8CC56E",
        "#6CC7DC",
        "#80C1FA",
        "#BCB3F9",
        "#E181AC",
    ]

    async def draw_message_box(content_image: ImageType, is_framed: bool = True):
        frame_width = 40 if is_framed else 0
        frame_height = 20 if is_framed else 0

        message_box = Image.new(
            mode="RGBA",
            size=(
                content_image.width + frame_width,
                content_image.height + frame_height,
            ),
            color=0,
        )

        draw_box = ImageDraw.Draw(message_box)

        if is_framed:
            draw_box.rounded_rectangle(
                xy=(0, 0, *message_box.size), radius=30, fill=Quote.MESSAGE_COLOR
            )

        message_box.paste(im=content_image, box=(20, 10) if is_framed else (0, 0))

        return message_box

    async def merge_images(
        *image_args: ImageType,
        spacing: int = 0,
        vertical: bool = True,
        background_color=None,
        align: bool = False,
    ):
        if not image_args:
            return

        if background_color is None:
            background_color = Quote.MESSAGE_COLOR

        if vertical:
            heights = [image.height for image in image_args if image]
            max_height = max(heights) if not align else min(heights)
            size = (
                sum([image.width + spacing for image in image_args if image]) - spacing,
                max_height,
            )
        else:
            widths = [image.width for image in image_args if image]
            max_width = max(widths) if not align else min(widths)
            size = (
                max_width,
                sum([image.height + spacing for image in image_args if image])
                - spacing,
            )

        new_image = Image.new(mode="RGBA", size=size, color=background_color)

        x, y = (0, 0)
        for image in image_args:
            if not image:
                continue

            new_image.paste(im=image, box=(x, y))
            if vertical:
                x += image.width + spacing
            else:
                y += image.height + spacing

        return new_image

    async def get_entity_data(entities: list):
        if not entities:
            return {}

        entity_data = {}
        entity_type = None

        for entity in entities:
            if isinstance(entity, types.MessageEntityBold):
                entity_type = "bold"
            elif isinstance(entity, types.MessageEntityItalic):
                entity_type = "italic"
            elif isinstance(entity, types.MessageEntityCode) or isinstance(
                entity, types.MessageEntityPre
            ):
                entity_type = "mono"
            elif (
                isinstance(entity, types.MessageEntityUrl)
                or isinstance(entity, types.MessageEntityMention)
                or isinstance(entity, types.MessageEntityMentionName)
                or isinstance(entity, types.InputMessageEntityMentionName)
                or isinstance(entity, types.MessageEntityTextUrl)
            ):
                entity_type = "url"
            elif isinstance(entity, types.MessageEntityUnderline):
                entity_type = "underline"

            offset = entity.offset
            length = entity.length

            entity_data.update({offset: entity_type, offset + length: "regular"})

        return entity_data

    async def get_profile_photo(client: Client, user_info):
        photo_buffer = None

        try:
            photo_buffer = await client.download_profile_photo(user_info, BytesIO())
        except Exception:
            pass

        if not photo_buffer:
            profile_photo = Image.new(
                mode="RGBA", size=(50, 50), color=Quote.USER_COLORS[user_info.id]
            )

            profile_draw = ImageDraw.Draw(profile_photo, "RGBA")

            temp_font = ImageFont.truetype(Quote.FONT_REGULAR.path, 25)

            profile_draw.text(
                xy=(16, 12), text=user_info.name[0], font=temp_font, fill="white"
            )

            photo_buffer = BytesIO()

            profile_photo.save(photo_buffer, format="png")

        photo_buffer.seek(0)

        profile_photo = Image.open(photo_buffer)
        profile_photo = profile_photo.resize((50, 50))

        profile_photo_canvas = Image.new(mode="RGBA", size=(50, 50))

        profile_photo_mask = Image.new(
            mode="L",
            size=profile_photo.size,
        )

        profile_photo_mask_draw = ImageDraw.Draw(profile_photo_mask)

        profile_photo_mask_draw.ellipse(xy=(0, 0, 48, 48), fill=255)

        profile_photo_canvas.paste(
            im=profile_photo, box=(0, 0), mask=profile_photo_mask
        )

        return profile_photo_canvas

    async def shorten_text(
        text: str, font: FontType = None, offset: int = 0, is_dotted: bool = False
    ):
        if not text:
            return text

        if not font:
            font = Quote.FONT_REGULAR

        new_text = ""
        width = 0
        for char in text:
            if width + offset + (15 if is_dotted else 0) >= Quote.MAXIMUM_BOX_WIDTH:
                new_text += "..." if is_dotted else ""
                break

            width += font.getlength(char)
            new_text += char

        return new_text

    async def draw_reply_bar(message: Message, is_media: bool = False):
        thumb_file = None
        x_pos = 10
        
        text = message.raw_text.replace("\n", "    ")

        if message.photo:
            text = text or "Photo"
        elif message.sticker:
            text = f"{message.file.emoji} Sticker"
        elif message.gif:
            text = text or "GIF"
        elif message.video:
            text = text or "Video"
        elif message.audio:
            text = text or "🎵 Audio"
        elif message.voice:
            text = text or "Voice Message"
        else:
            text = text or message.file.name or "📎 Document"

        if message.document and message.document.thumbs:
            thumb_file = await message.download_media(
                BytesIO(),
                thumb=0,
            )

            thumb_file.seek(0)
            thumb_file = Image.open(thumb_file)

            if thumb_file.width > 36:
                thumb_file = thumb_file.crop(
                    box=(int(thumb_file.width / 5 * 2), 0, int(thumb_file.width / 5 * 3), thumb_file.height)
                )

            thumb_file = thumb_file.resize((36, 36), Image.NEAREST)

        name_image = await Quote.draw_text(
            text=message.from_user.name, font=Quote.FONT_TITLE
        )

        text_image = await Quote.draw_text(text=text)

        reply_bar = Image.new(
            mode="RGBA",
            size=(
                max(name_image.width, text_image.width) + (15 if message.media else 30),
                Quote.LINE_HEIGHT * 2 + 4,
            ),
            color=Quote.MESSAGE_COLOR,
        )

        reply_bar_draw = ImageDraw.Draw(reply_bar)

        reply_bar_draw.line(xy=(0, 0, 0, Quote.LINE_HEIGHT * 2), width=2)

        if thumb_file:
            try:
                reply_bar.alpha_composite(im=thumb_file, dest=(10, 2))
            except ValueError:
                reply_bar.paste(im=thumb_file, box=(10, 2))
            x_pos += 43

        reply_bar.paste(im=name_image, box=(x_pos, 2))

        reply_bar.paste(im=text_image, box=(x_pos, 2 + round(Quote.LINE_HEIGHT)))

        return reply_bar

    async def add_radius(image: ImageType, radius: int = 10):
        new_image = Image.new(mode="RGBA", size=image.size)

        mask = Image.new(mode="L", size=image.size)

        mask_draw = ImageDraw.Draw(mask)

        mask_draw.rounded_rectangle(xy=(0, 0, *image.size), radius=radius, fill=255)

        new_image.paste(im=image, box=(0, 0), mask=mask)

        return new_image

    async def draw_media_type(thumb_buffer: BytesIO, text_image: ImageType, is_sticker: bool=False):
        media_image = Image.open(thumb_buffer)
        
        if media_image.width < Quote.MAXIMUM_BOX_WIDTH and not is_sticker:
            
            new_media_image = media_image.filter(ImageFilter.BoxBlur(20))

            new_media_image = new_media_image.resize(
                (
                    Quote.MAXIMUM_BOX_WIDTH,
                    media_image.height * int(Quote.MAXIMUM_BOX_WIDTH / media_image.width)
                )
            )

            new_media_image = new_media_image.crop((0, 0, new_media_image.width, media_image.height))

            new_media_image.paste(
                im=media_image,
                box=(int(Quote.MAXIMUM_BOX_WIDTH / 2 - media_image.width/2), 0)
            )

            media_image = new_media_image

        media_image = await Quote.merge_images(
            *[image for image in [media_image, text_image] if image],
            vertical=False,
            spacing=5
        )

        media_mask = Image.new(mode="L", size=media_image.size, color=0)

        mask_draw = ImageDraw.Draw(media_mask)

        mask_draw.rounded_rectangle(xy=(0, 0, *media_mask.size), radius=10, fill=255)

        content_image = Image.new(mode="RGBA", size=media_mask.size, color=0)

        content_image.paste(im=media_image, box=(0, 0), mask=media_mask)

        return content_image

    async def draw_document(message: Message):
        name, size = message.file.name, message.file.size

        if message.document.thumbs:
            thumb_buffer = await message.download_media(thumb=-1, file=BytesIO())
            thumb_buffer.seek(0)
            thumb_buffer.name = "thumbnail.png"

            thumb_image = Image.open(thumb_buffer)

            if thumb_image.width > 45:
                thumb_image = thumb_image.crop(
                    box=(int(thumb_image.width / 5 * 2), 0, int(thumb_image.width / 5 * 3), thumb_image.height)
                )

            thumb_image = thumb_image.resize((45, 45))

            thumb_image = await Quote.add_radius(image=thumb_image, radius=7)

            y_pos = 4

        else:
            thumb_image = Image.new(
                mode="RGBA", size=(45, 45), color=Quote.MESSAGE_COLOR
            )

            download_draw = ImageDraw.Draw(thumb_image)

            download_draw.ellipse(xy=(0, 0, 45, 45), fill="#434343")

            download_draw.text(
                xy=(18, 10),
                text="⬇",
                font=ImageFont.truetype(Quote.FONT_FALLBACK.path, 25),
                embedded_color=True,
                fill="white",
            )

            y_pos = 7

        size = await humanize(data=size)
        name = await Quote.shorten_text(
            text=name, font=Quote.FONT_TITLE, offset=thumb_image.width + 10
        )

        name_image = await Quote.draw_text(text=name, font=Quote.FONT_TITLE)

        size_image = await Quote.draw_text(text=size, font=Quote.FONT_REGULAR)

        document_image = Image.new(
            mode="RGBA",
            size=(name_image.width + thumb_image.width, thumb_image.height + 6),
            color=Quote.MESSAGE_COLOR,
        )

        document_image.alpha_composite(im=thumb_image, dest=(0, 0))

        document_image.paste(im=name_image, box=(thumb_image.width + 10, y_pos))

        document_image.paste(
            im=size_image, box=(thumb_image.width + 10, y_pos + Quote.LINE_HEIGHT)
        )

        return document_image

    async def draw_link_preview(webpage_data: types.WebPage):
        site_image = await Quote.draw_text(text=webpage_data.site_name)

        description = f"{webpage_data.title}\n{webpage_data.description}"
        description_image = await Quote.draw_text(text=description)

        link_preview_image = Image.new(
            mode="RGBA",
            size=(
                max(site_image.width, description_image.width) + 10,
                site_image.height + description_image.height,
            ),
            color=Quote.MESSAGE_COLOR,
        )

        link_preview_draw = ImageDraw.Draw(link_preview_image)

        link_preview_draw.line(xy=(0, 0, 0, link_preview_image.height), width=2)

        link_preview_image.paste(im=site_image, box=(10, 0))

        link_preview_image.paste(im=description_image, box=(10, site_image.height))

        return link_preview_image

    async def draw_media(message: Message, text_image: ImageType = None):
        if message.is_media_type and not message.web_preview:
            thumb_buffer = BytesIO()

            try:
                await message.download_media(file=thumb_buffer, thumb=1)
            except:
                await message.download_media(file=thumb_buffer, thumb=0)

            thumb_buffer.seek(0)

            return await Quote.draw_media_type(
                thumb_buffer=thumb_buffer, text_image=text_image,
                is_sticker=message.sticker
            )
        else:
            if message.web_preview:
                media_image = await Quote.draw_link_preview(message.media.webpage)
                ordered_images = [text_image, media_image]
            elif hasattr(message.media, "webpage") and isinstance(message.media.webpage, types.WebPageEmpty):
                return text_image
            else:
                media_image = await Quote.draw_document(message)
                ordered_images = [media_image, text_image]

            media_image = await Quote.merge_images(
                *[image for image in ordered_images if image], spacing=5, vertical=False
            )

            return media_image

    async def to_image(message_list: list[Message]):
        sticker_image = None
        last_user = None

        for message in message_list:
            image_list = []

            message.is_media_type = (message.photo or message.video or message.sticker) and not message.web_preview
            is_framed = not message.is_media_type and (
                message.document or message.raw_text
            )

            is_titled = is_framed

            text_image = reply_image = None

            if is_titled:
                title = await Quote.shorten_text(
                    message.from_user.name, font=Quote.FONT_TITLE
                )

                title_image = await Quote.draw_text(
                    text=title,
                    font=Quote.FONT_TITLE,
                    color=Quote.USER_COLORS[message.from_user.id],
                )

                image_list.append(title_image)

            if message.is_reply:
                reply_image = await Quote.draw_reply_bar(
                    message=message.reply_to_text,
                    is_media=message.is_media_type,
                )

            if message.raw_text:
                text_image = await Quote.draw_text(
                    text=message.raw_text,
                    entities=message.entities,
                    x_offset=10 if message.is_media_type else 0,
                )

            if message.media:
                media_image = await Quote.draw_media(
                    message=message, text_image=text_image
                )

                if (
                    message.is_reply
                    and message.is_media_type
                    and reply_image.width > media_image.width
                ):
                    reply_image = reply_image.crop(
                        (0, 0, media_image.width, reply_image.height)
                    )

                    fade_effect = Image.linear_gradient("L")
                    fade_effect = fade_effect.rotate(270).resize(
                        (reply_image.width + 50, reply_image.height)
                    )
                    fade_effect = fade_effect.crop((0, 0, *reply_image.size))

                    new_reply_bar = Image.new(mode="RGBA", size=reply_image.size)

                    new_reply_bar.paste(
                        im=reply_image,
                        box=(reply_image.width - fade_effect.width, 0),
                        mask=fade_effect,
                    )

                    reply_image = new_reply_bar

                image_list.append(reply_image)
                image_list.append(media_image)
            else:
                image_list.append(reply_image)
                image_list.append(text_image)

            content_image = await Quote.merge_images(
                *image_list,
                vertical=False,
                spacing=4,
                background_color=0 if message.is_media_type else None,
            )

            message_image = await Quote.draw_message_box(
                content_image=content_image, is_framed=is_framed
            )

            if last_user != message.from_user.id:
                profile_image = await Quote.get_profile_photo(
                    client=message.client,
                    user_info=message.from_user,
                )

                last_user = message.from_user.id
            else:
                profile_image = Image.new(mode="RGBA", size=(50, 50))

            message_image = await Quote.merge_images(
                profile_image, message_image, spacing=4, background_color=0
            )

            sticker_image = await Quote.merge_images(
                sticker_image,
                message_image,
                spacing=5,
                vertical=False,
                background_color=0,
            )

        sticker_image = await Quote.merge_images(
            sticker_image, spacing=3, background_color=0
        )

        image_buffer = BytesIO()
        sticker_image.save(image_buffer, format="webp")

        image_buffer.name = "sticker.webp"
        image_buffer.seek(0)

        return image_buffer

    async def draw_text(
        text: str,
        entities: list[types.TypeMessageEntity] = [],
        font: FontType = None,
        color="white",
        x_offset: int = 0,
    ):
        text_image = Image.new(
            mode="RGBA",
            size=(Quote.MINIMUM_BOX_WIDTH, Quote.LINE_HEIGHT),
            color=Quote.MESSAGE_COLOR,
        )

        text_drawer = ImageDraw.Draw(text_image)

        entity_book = await Quote.get_entity_data(entities=entities)

        if not font:
            font = Quote.FONT_REGULAR

        x = x_offset
        y = 0

        kwargs = {"fill": color}
        entity_type = ""
        index = 0

        for char in text:

            entity_type = entity_book.get(index) or entity_type

            if entity_type == "bold":
                font = Quote.FONT_BOLD
            elif entity_type == "italic":
                font = Quote.FONT_ITALIC
            elif entity_type == "mono":
                font = Quote.FONT_MONO

            elif entity_type == "regular":
                kwargs = {"fill": color}
                font = Quote.FONT_REGULAR

            if entity_type != "url":
                kwargs = {"fill": color}

            previous_font = font
            font = Quote.FONT_EMOJI \
                if emoji.is_emoji(char) \
                else Quote.FONT_FALLBACK \
                if char not in string.printable and char != "\n" \
                else previous_font

            if char == "\n" or x + font.getlength(char) > Quote.MAXIMUM_BOX_WIDTH:
                x = x_offset
                y += Quote.LINE_HEIGHT

            if text_image.width < x + font.getlength(char) < Quote.MAXIMUM_BOX_WIDTH:
                additional_section = Image.new(
                    mode="RGBA", size=(15, text_image.height), color=Quote.MESSAGE_COLOR
                )

                text_image = await Quote.merge_images(text_image, additional_section)

                text_drawer = ImageDraw.Draw(text_image)

            if y + Quote.LINE_HEIGHT > text_image.height:
                additional_section = Image.new(
                    mode="RGBA",
                    size=(text_image.width, Quote.LINE_HEIGHT),
                    color=Quote.MESSAGE_COLOR,
                )

                text_image = await Quote.merge_images(
                    text_image, additional_section, vertical=False
                )

                text_drawer = ImageDraw.Draw(text_image)

            if entity_type == "url" or entity_type == "underline":

                width = font.getlength(char)
                height = font.getbbox("m")[3] + 2
                kwargs["fill"] = ((166, 216, 245, 255)) if entity_type == "url" else "white"

                text_drawer.line(
                    xy=(x + width, y + height, x, y + height),
                    width=1,
                    **kwargs,
                )

            if char != "\n":
                text_drawer.text(
                    xy=(x, y),
                    text=char,
                    embedded_color=True,
                    font=font,
                    **kwargs,
                )

                x += font.getlength(char)

            index += 1 if not emoji.is_emoji(char) else 2
            font = previous_font

        return text_image

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
        i = 0

        async for message_object in client.iter_messages(
            entity=await message.get_chat(),
            limit=message_count,
            max_id=message.reply_to_text.id + 1,
        ):
            i += 1
            message_object = await get_messages_recursively(message_object, recursion_limit=2)

            if message_object.sender.id not in Quote.USER_COLORS:
                Quote.USER_COLORS.update(
                    {message_object.sender.id: random.choice(Quote.TITLE_COLOR_PALETTE)}
                )

            message_list.append(message_object)

        message_list.reverse()
        sticker_buffer = await Quote.to_image(message_list=message_list)

        await message.respond(file=sticker_buffer)

    @run(command="fq")
    async def fake_quote(message: Message, client: Client):
        if not message.args:
            await message.edit(
                "<i>You need to input a username and a message attached to it in that order</i>"
            )
            return

        arguments = message.args.split()
        if len(arguments) < 2:
            await message.edit(
                "<i>Invalid arguments passed in, check the help page for usage</i>"
            )
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

        fake_message_object = FakeMessage(
            message_id=user_info.id, message=user_text, sender=user_info, client=client
        )

        if fake_message_object.id not in Quote.USER_COLORS:
            Quote.USER_COLORS.update(
                {fake_message_object.id: random.choice(Quote.TITLE_COLOR_PALETTE)}
            )

        sticker_buffer = await Quote.to_image([fake_message_object])

        await message.respond(file=sticker_buffer)

    @run(command="setcolor")
    async def set_message_color(message: Message, client: Client):
        if not message.args:
            Quote.MESSAGE_COLOR = (50, 50, 50, 255)
            await message.edit("<i>Message box color has been set to default</i>")
            return

        arguments = message.args.split()

        if len(arguments) > 3 and "".join(arguments).isdigit():
            r, g, b, a = (
                int(arguments[0]),
                int(arguments[1]),
                int(arguments[2]),
                int(arguments[3]),
            )
            color = (r, g, b, a)
        elif message.args.startswith("#"):
            color = message.args
        else:
            color = message.args

        tester_image = Image.new(mode="RGBA", size=(50, 50))

        tester_draw = ImageDraw.Draw(tester_image)

        try:
            tester_draw.text(xy=(0, 0), text="a", fill=color)

            quotedb.set_message_color(color)
            Quote.MESSAGE_COLOR = color
            await message.edit(f"<i>Message box color has been set to {color}</i>")
        except Exception as e:
            await message.edit(f"<i>{e}</i>")


@startup
def load_from_database():
    Quote.MESSAGE_COLOR = quotedb.get_message_color()

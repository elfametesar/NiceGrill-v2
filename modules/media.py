from main import run, startup, logger
from config import GOOGLE_DEV_API, GOOGLE_CX_ID
from telethon import TelegramClient
from telethon.tl.patched import Message
from google_images_search import GoogleImagesSearch
from pytube import YouTube
from googlesearch import search
from youtube_search import YoutubeSearch
from requests.exceptions import ReadTimeout, ConnectTimeout
from utils import get_full_log, strip_prefix
from utils import strip_prefix
from io import BytesIO
from bs4 import BeautifulSoup

import asyncio
import html
import json

class Media:
    
    GOOGLE_CLIENT: GoogleImagesSearch = None
    SEARCH_LIMIT = 5
    UPLOADED_IMAGES = []
    CURRENT_MESSAGE = None
    URL = "https://www.bing.com/images/search?q="


    async def simple_progress_tracker(url, progress):
        try:
            if int(progress) % 7 == 0:
                await Media.CURRENT_MESSAGE.edit(f"<b>URL:</b> <i>{url}</i>\n<b>Progress:</b> <i>{progress}%</i>")

        except:
            pass

    @run(command="yt")
    async def youtube_search(message: Message, client: TelegramClient):
        if not message.args:
            await message.edit("<i>You need to type in a keyword first</i>")
            return
        
        await message.edit(f"<i>Searching for the keyword <u>{message.args}</u> in YouTube</i>")

        results = (await asyncio.to_thread(YoutubeSearch,
            search_terms=message.args,
            max_results=Media.SEARCH_LIMIT
        )).to_dict()
        
        result_page = ""
        for result in results:
            result_page += f"""
<b>◍ {result.get('title')}</b>
<b>URL:</b> <i>https://www.youtube.com{result.get('url_suffix')}</i>
<b>Channel:</b> <i>{result.get('channel')}</i>
<b>Duration:</b> <i>{result.get("Duration")}</i>
"""
        await message.edit(result_page, link_preview=False)


    @run(command="yt(v|s)")
    async def youtube_downloader(message: Message, client: TelegramClient):
        if not message.args:
            await message.edit("<i>Enter in a valid URL first</i>")
            return
        
        audio_filter = False
        if message.cmd == "yts":
            audio_filter = True

        try:
            await message.edit("<i>Searching in YouTube for a downloadable media in the link</i>")
            youtube_search = YouTube(message.args).streams.filter(only_audio=audio_filter)
        except Exception as e:
            logger.error(e)
            await message.edit("<i>Video is unavailable</i>")
            return
        

        result = youtube_search.get_highest_resolution()
        
        if not result:
            await message.edit("<i>There is no downloadable media found in this link</i>")
            return
        
        await message.edit("<i>Downloading the video into buffer</i>")

        video_buffer = BytesIO()
        result.stream_to_buffer(video_buffer)
        video_buffer.seek(0)
        Media.CURRENT_MESSAGE = message

        await message.edit("<i>Uploading the video into telegram</i>")

        video_handle = await client.upload_file(
            file=video_buffer,
            file_name=result.default_filename,
            file_size=result.filesize,
            progress_callback=lambda received_bytes, total_bytes: 
                asyncio.get_event_loop().create_task(
                    Media.simple_progress_tracker(
                        url=message.args,
                        progress=round((received_bytes/total_bytes) * 100, 2)
                    )
                )
        )

        await message.respond(
            file=video_handle,
            message=f"<i>Here's the downloaded video for the input link {message.args}</i>",
            supports_streaming=True
        )

        await message.delete()
        

    @run(command="google")
    async def google_regular_search(message: Message, client: TelegramClient):
        await message.edit("<i>Searching..</i>")

        google_search = search(
            message.args,
            advanced=True,
            num_results=Media.SEARCH_LIMIT,
            timeout=10
        )

        try:
            result_page = ""
            for search_result in await asyncio.to_thread(list, google_search):
                result_page +=  f"""
<b>◍ {search_result.title}</b>
<i>{search_result.url}</i>

{search_result.description}
"""

        except (ReadTimeout, ConnectTimeout):
            await message.edit("<i>Time has run out for this search</i>")
            return

        except:
            await message.edit("<i>Google search API is dead</i>")
            return


        await message.edit(result_page, link_preview=False)


    @run(command="bimg")
    async def bing_image_scrape_search(message: Message, client: TelegramClient):
        if not message.args:
            await message.edit("<i>Give me a keyword to look for in Bing images</i>")
            return
        
        await message.edit("<i>Retrieving data from image search</i>")
        
        try:
            url_data = await get_full_log(Media.URL + message.args)
        except Exception as e:
            await message.edit(f"<b>Error:</b> <i>{html.escape(str(e))}</i>")
            return

        if not url_data:
            await message.edit("<i>Link cannot be retrieved</i>")
            return

        try:
            parser = await asyncio.to_thread(BeautifulSoup, url_data.text, "lxml")
        except Exception as e:
            await message.edit(f"<b>Error:</b> <i>{html.escape(str(e))}</i>")
            return

        result = parser.find_all("a", class_="iusc")

        image_urls = []

        for item in result:
            if item := item.get("m"):
                image_data_dict = json.loads(item)
                image_urls.append(image_data_dict.get("murl"))

        if not image_urls:
            await message.edit("<i>No images found, make sure you have a valid keyword</i>")
            return

        await message.edit("<i>Uploading image files to telegram</i>")

        result.clear()
        
        hit_counter = 0
        
        for image_url in image_urls:
            if hit_counter == Media.SEARCH_LIMIT:
                break

            try:
                image_bytes = (await get_full_log(image_url)).content

                if not image_bytes or image_bytes in result:
                    continue

            except Exception:
                continue

            result.append(
                await client.upload_file(
                    file=image_bytes,
                    file_name=strip_prefix(image_url) + ".png",
                    file_size=len(image_bytes)
                )
            )
            hit_counter += 1
        
        if not result:
            await message.edit("<i>No images were downloaded, therefore process has failed</i>")
            return

        try:
            await message.respond(
                file=result,
                message=f"<i>Here is the search result for the keyword <u>{message.args}</u></i>"
            )
        except:
            await message.respond("<i>Media files may be corrupted, you can retry with retry command</i>")
            Media.UPLOADED_IMAGES = result

        await message.delete()


    @run(command="gimg")
    async def google_image_search(message: Message, client: TelegramClient):
        
        if not message.args:
            await message.edit("<i>Input a search keyword first</i>")
            return
        
        search_parameters = {
            'q': message.args,
            "num": Media.SEARCH_LIMIT,
            "safe": "off"
        }
        
        Media.CURRENT_MESSAGE = await message.edit(f"<i>Searching images on google for the keyword: <u>{message.args}</u></i>")
        try:
            await asyncio.to_thread(Media.GOOGLE_CLIENT.search, search_parameters)
        except Exception as e:
            print(e)
            await message.edit(f"<i>Error: {html.escape(e)}</i>")
            return
        
        image_files = []
        image_bytes = BytesIO()

        for image in Media.GOOGLE_CLIENT.results():
            image.copy_to(image_bytes)
            image_bytes.seek(0)
            image_files.append(
                await client.upload_file(
                    file=image_bytes,
                    file_size=image_bytes.getbuffer().nbytes,
                    file_name=strip_prefix(image.url)
                )
            )
            image_bytes.seek(0)
        
        if not image_files:
            await message.edit(f"<i>No results found for {message.args}</i>")
            return
        
        await message.edit("<i>Uploading images to telegram</i>")
        
        try:
            await message.respond(
                file=image_files,
                message=f"<i>Here is the search result for the keyword <u>{message.args}</u></i>"
            )
            await message.delete()
        except:
            Media.UPLOADED_IMAGES = image_files
            await message.edit(
                "<i>Something went wrong with the file upload, you can retry with <code>reupload</code> command</i>"
            )
            return
        
    @run(command="reupload")
    async def retry_sending_images(message: Message, client: TelegramClient):
        if not Media.UPLOADED_IMAGES:
            await message.edit("<i>No photos stored in memory right now</i>")
            return
        
        await message.edit("<i>Retrying to upload the previous search</i>")

        successful = False
        for uploaded_image in Media.UPLOADED_IMAGES:
            try:
                await message.reply(
                    file=uploaded_image
                )
                successful = True
            except:
                pass

        if not successful:
            await message.edit("<i>Failed to upload the photos again, unfortunately have to delete</i>")
            Media.UPLOADED_IMAGES = []
            return
        
        await message.delete()
        
    @run(command="limit")
    async def set_photo_count(message: Message, client: TelegramClient):
        if not message.args or not message.args.isdigit():
            await message.edit("<i>Please input a valid photo count</i>")
            return
        
        try:
            Media.SEARCH_LIMIT = int(message.args) if int(message.args) > 0 else 1
        except:
            return
        
        await message.edit(f"<i>Bing photo search count updated to {Media.SEARCH_LIMIT}</i>")

@startup
def google_client_initializer():
    Media.GOOGLE_CLIENT = GoogleImagesSearch(
        GOOGLE_DEV_API,
        GOOGLE_CX_ID,
        progressbar_fn=lambda url, progress: 
            asyncio.get_event_loop().create_task(Media.simple_progress_tracker(url,progress))
        )

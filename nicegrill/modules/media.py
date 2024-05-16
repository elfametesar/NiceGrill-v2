from urllib.error import HTTPError
from nicegrill import Message, run, startup
from config import GOOGLE_DEV_API, GOOGLE_CX_ID
from telethon import TelegramClient as Client
from google_images_search import GoogleImagesSearch
from pytube import YouTube
from googlesearch import search
from youtube_search import YoutubeSearch
from requests.exceptions import ReadTimeout, ConnectTimeout
from nicegrill.utils import full_log, get_full_log, strip_prefix
from remove_bg_python.remove import remove
from io import BytesIO
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
from requests import get

import requests
import asyncio
import html
import json
import os

class Media:
    
    GOOGLE_CLIENT: GoogleImagesSearch = None
    SEARCH_LIMIT = 5
    UPLOADED_IMAGES = []
    CURRENT_MESSAGE = None
    URL = "https://www.bing.com/images/search?q="


    async def simple_progress_tracker(received_bytes=None, total_bytes=None, url=None, progress=None):
        if received_bytes:
            progress = round((received_bytes/total_bytes) * 100, 2)
        try:
            if int(progress) % 7 == 0:
                await Media.CURRENT_MESSAGE.edit(f"<b>URL:</b> <i>{url}</i>\n<b>Progress:</b> <i>{progress}%</i>")

        except:
            pass

    @run(command="rembg")
    async def remove_photo_background(message: Message, client: Client):
        if not message.is_reply or (message.is_reply and not any([message.reply_to_text.photo, message.reply_to_text.sticker])):
            await message.edit("<i>You need to reply to an image</i>")
            return
        
        if message.reply_to_text.sticker and "image" not in message.reply_to_text.sticker.mime_type:
            await message.edit("<i>You need to reply to an inanimate sticker</i>")
            return
        
        await message.edit("<i>Removing background from the image</i>")

        image_file: BytesIO = await message.reply_to_text.download_media(BytesIO())
        image_file.name = message.reply_to_text.file.name or "file.png"

        image_file = BytesIO(
            initial_bytes=remove(
                data=image_file.getvalue(),
            )
        )

        image_file.seek(0)
        image_file.name = message.reply_to_text.file.name or "file.png"

        await message.delete()
        await message.respond(
            file=image_file,
            force_document=True
        )

    @run(command="yt")
    async def youtube_search(message: Message, client: Client, only_url=False):

        if only_url:
            return YoutubeSearch(
                search_terms=message.args,
                max_results=1
        ).to_dict()

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


    @run(command="song")
    async def song_downloader(message: Message, client: Client):
        
        if not message.args:
            await message.edit("<i>You need to tell me what to search for</i>")
            return
        
        await message.edit("<i>Searching for songs</i>")
        
        opts = {
            "outtmpl": f"{message.args}.m4a",
            'format': 'm4a/bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }]
        }

        yt_client = YoutubeDL(opts)
        result = await Media.youtube_search(
            message=message,
            client=client,
            only_url=True
        )
        
        if result:
            song_url = "https://youtube.com" + result[0].get("url_suffix")
        else:
            await message.edit(f"No song found with keyword {message.args}</i>")
            return        
        
        await message.edit("<i>Song found, downloading it rn</i>")
        yt_client.download(song_url)
        
        await message.edit("<i>Uploading the song to Telegram</i>")
        await client.send_file(
            entity=message.chat,
            file=message.args + ".m4a",
            voice_note=True
        )

        os.remove(message.args + ".m4a")
        await message.delete()


    @run(command="ytv")
    async def youtube_downloader(message: Message, client: Client):
        if not message.args:
            await message.edit("<i>Enter in a valid URL first</i>")
            return


        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://ssyoutube.com',
            'priority': 'u=1, i',
            'referer': 'https://ssyoutube.com/',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }

        json_data = {
            'url': message.args,
            'ts': requests.get("https://ssyoutube.com/msec").json().get("msec"),
            '_ts': 1715778806518,
            '_tsc': 0,
            '_s': '5d9ff383d1c43ca0ebd95475f718dde014443dec86950d088f2389d80077b3b6',
        }

        await message.edit("<i>Searching in YouTube for a downloadable media in the link</i>")

        try:
            response = requests.post('https://api.ssyoutube.com/api/convert', headers=headers, json=json_data)
        except Exception as e:
            await message.edit(f"<i>Video cannot be fetched</i>\n<b>Error: </b><i>{e}</i>")
            return
        
        if not response.ok:
            await message.edit(f"<i>There is no downloadable media found in this link</i>\n<b>Reason: </b><i>{response.reason}</i>")
            return

        await message.edit("<i>Downloading the video into buffer</i>")

        menu = ""
        url = ""
        quality = 0
        for item in response.json().get("url"):
            if item.get("qualityNumber") > quality and not item.get("no_audio"):
                url = item.get("url")

            menu += f'<a href={item.get("url")}>{item.get("subname")}.{item.get("ext")} - {item.get("attr").get("title")}</a>\n'

        menu = await full_log(menu)

        video_buffer = BytesIO(requests.get(url).content)
        video_buffer.seek(0)
        video_buffer.name = "video.mp4"

        await message.edit("<i>Uploading the video into telegram</i>")
        await message.delete()
        await message.respond(
            message=f"<i>All Qualities:\n{menu.text}</i>",
            file=video_buffer
        )

    @run(command="google")
    async def google_regular_search(message: Message, client: Client):
        await message.edit("<i>Searching..</i>")

        google_search = await asyncio.to_thread(
            search,
            query=message.args,
            stop=Media.SEARCH_LIMIT
        )

        print("tested")

        try:
            result_page = ""


            for link in await asyncio.to_thread(list, google_search):
                r = get(link)
                soup = BeautifulSoup(r.content, "lxml")

                title = soup.find("title").text
                desc = ""
                desc_tag = soup.find("meta", {"name": "description"})

                if desc_tag:
                    desc = desc_tag.get("content").strip()

                result_page +=  f"""
<b>◍ {title}</b>
<i>{link}</i>
{desc}
"""

        except (ReadTimeout, ConnectTimeout):
            await message.edit("<i>Time has run out for this search</i>")
            return

        except HTTPError:
            await message.edit("<i>Too many requests</i>")
            return

        except Exception as e:
            await message.edit(f"{e}\n\n<i>Google search API is dead</i>")
            return

        await message.edit(result_page, link_preview=False)


    @run(command="bimg")
    async def bing_image_scrape_search(message: Message, client: Client):
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
    async def google_image_search(message: Message, client: Client):
        
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
    async def retry_sending_images(message: Message, client: Client):
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
    async def set_photo_count(message: Message, client: Client):
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

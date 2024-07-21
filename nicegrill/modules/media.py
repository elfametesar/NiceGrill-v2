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

from httpx import ReadTimeout, ConnectTimeout, HTTPError
from googlesearch import search as GoogleSearch
from remove_bg_python.remove import remove
from elfrien.types.patched import Message
from youtube_search import YoutubeSearch
from nicegrill.utils import get_bin_url
from elfrien.client import Client
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
from nicegrill import on
from io import BytesIO

import asyncio
import httpx
import html
import json
import os

class Media:

    SEARCH_LIMIT = 5
    UPLOADED_IMAGES = []
    URL = "https://www.bing.com/images/search?q="


    async def simple_progress_tracker(
        received_bytes: int,
        total_bytes: int,
        url: str,
        message: Message
    ):
        if received_bytes:
            progress = round((received_bytes/total_bytes) * 100, 2)
        try:
            if int(progress) % 7 == 0:
                await message.edit(f"<b>URL:</b> <i>{url}</i>\n<b>Progress:</b> <i>{progress}%</i>")

        except:
            pass

    @on(pattern="rembg")
    async def remove_photo_background(client: Client, message: Message):
        if not message.reply_to_text or (message.reply_to_text and not any([message.reply_to_text.photo, message.reply_to_text.sticker])):
            await message.edit("<i>You need to reply to an image</i>")
            return
        
        if message.reply_to_text.sticker and "image" not in message.reply_to_text.sticker.mime_type:
            await message.edit("<i>You need to reply to an inanimate sticker</i>")
            return
        
        await message.edit("<i>Removing background from the image</i>")

        image_file: BytesIO = await message.reply_to_text.download()
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
            files=image_file,
            force_type="Document"
        )
    

    @on(pattern="(yts|ytsearch)")
    async def youtube_search(client: Client, message: Message):

        if not message.raw_args:
            await message.edit("<i>You need to type in a keyword first</i>")
            return
        
        await message.edit(f"<i>Searching for the keyword <u>{message.raw_args}</u> in YouTube</i>")

        results = (await asyncio.to_thread(YoutubeSearch,
            search_terms=message.raw_args,
            max_results=Media.SEARCH_LIMIT
        )).to_dict()

        result_page = ""
        for result in results:
            result_page += f"""
<b>◍ {result.get('title')}</b>
<b>URL:</b> <i>https://www.youtube.com{result.get('url_suffix')}</i>
<b>Channel:</b> <i>{result.get('channel')}</i>
<b>Duration:</b> <i>{result.get("duration")}</i>
"""
        await message.edit(result_page, link_preview=False)
    
    @on(pattern="song")
    async def song_downloader(client: Client, message: Message):
        
        if not message.raw_args:
            await message.edit("<i>You need to tell me what to search for</i>")
            return
        
        await message.edit("<i>Searching for songs</i>")
        
        opts = {
            "outtmpl": f"{message.raw_args}.m4a",
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
            await message.edit(f"No song found with keyword {message.raw_args}</i>")
            return        
        
        await message.edit("<i>Song found, downloading it rn</i>")
        yt_client.download(song_url)
        
        await message.edit("<i>Uploading the song to Telegram</i>")
        await message.respond(
            files=message.raw_args + ".m4a",
            force_type="VoiceNote"
        )

        os.remove(message.raw_args + ".m4a")
        await message.delete()


    @on(pattern="(ytdlv|ytdlvideo)")
    async def youtube_downloader(client: Client, message: Message):
        if not message.raw_args:
            await message.edit("<i>Enter in a valid URL first</i>")
            return

        headers = {
            'next-action': '471020c2dbefc5c2bc0360aa22dff3a58efa53e7',
            'next-url': '/en/free-tools/youtube-video-downloader',
            'origin': 'https://quicktok.ai',
            'priority': 'u=1, i',
            'referer': 'https://quicktok.ai/free-tools/youtube-video-downloader/',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }


        await message.edit("<i>Searching in YouTube for a downloadable media in the link</i>")

        try:
            response = httpx.post(
                url='https://quicktok.ai/free-tools/youtube-video-downloader/',
                headers=headers,
                data=f'["{message.raw_args}"]'
            )
        except Exception as e:
            await message.edit(f"<i>Video cannot be fetched</i>\n<b>Error: </b><i>{e}</i>")
            return

        if not response.ok:
            await message.edit(f"<i>There is no downloadable media found in this link</i>\n<b>Reason: </b><i>{response.reason}</i>")
            return

        url = response.text.find("https://")
        url = response.text[url: -3]

        await message.edit("<i>Downloading the video into buffer</i>")

        video_buffer = BytesIO(httpx.get(url=url).content)
        video_buffer.seek(0)

        await message.edit("<i>Uploading the video into telegram</i>")

        await message.delete()
        await message.respond(
            files=video_buffer,
            force_type="Video",
            supports_streaming=True
        )

    @on(pattern="google")
    async def google_regular_search(client: Client, message: Message):
        await message.edit("<i>Searching..</i>")

        google_search = GoogleSearch(
            query=message.raw_args,
            stop=Media.SEARCH_LIMIT
        )

        try:
            result_page = ""


            for link in await asyncio.to_thread(list, google_search):
                r = httpx.get(link)
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
            await message.edit("<i>Time has on out for this search</i>")
            return

        except HTTPError:
            await message.edit("<i>Too many requests</i>")
            return

        except Exception as e:
            await message.edit(f"{e}\n\n<i>Google search API is dead</i>")
            return

        await message.edit(
            result_page,
            link_preview=False
        )


    @on(pattern="bimg")
    async def bing_image_scrape_search(client: Client, message: Message):
        if not message.raw_args:
            await message.edit("<i>Give me a keyword to look for in Bing images</i>")
            return

        await message.edit("<i>Retrieving data from image search</i>")

        try:
            url_data = await get_bin_url(Media.URL + message.raw_args)
        except Exception as e:
            await message.edit(f"<b>Error:</b> <i>{html.escape(str(e))}</i>")
            return

        if not url_data:
            await message.edit("<i>Link cannot be retrieved</i>")
            return

        try:
            parser = BeautifulSoup(
                url_data.text,
                "lxml"
            )
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
                image_bytes = (await get_bin_url(image_url)).content

                if not image_bytes or image_bytes in result:
                    continue

            except Exception:
                continue

            result.append(
                await client.upload_file(
                    file=image_bytes,
                    file_name=os.path.basename(image_url) + ".png"
                )
            )
            hit_counter += 1

        if not result:
            await message.edit("<i>No images were downloaded, therefore process has failed</i>")
            return

        try:
            await message.respond(
                files=result,
                message=f"<i>Here is the search result for the keyword <u>{message.raw_args}</u></i>"
            )
        except:
            await message.respond("<i>Media files may be corrupted, you can retry with retry pattern</i>")
            Media.UPLOADED_IMAGES = result

        await message.delete()

    @on(pattern="reupload")
    async def retry_sending_images(client: Client, message: Message):
        if not Media.UPLOADED_IMAGES:
            await message.edit("<i>No photos stored in memory right now</i>")
            return
        
        await message.edit("<i>Retrying to upload the previous search</i>")

        successful = False
        for uploaded_image in Media.UPLOADED_IMAGES:
            try:
                await message.reply(
                    files=uploaded_image
                )
                successful = True
            except:
                pass

        if not successful:
            await message.edit("<i>Failed to upload the photos again, unfortunately have to delete</i>")
            Media.UPLOADED_IMAGES = []
            return
        
        await message.delete()
        
    @on(pattern="limit")
    async def set_photo_count(client: Client, message: Message):
        if not message.raw_args or not message.raw_args.isdigit():
            await message.edit("<i>Please input a valid photo count</i>")
            return
        
        try:
            Media.SEARCH_LIMIT = int(message.raw_args) if int(message.raw_args) > 0 else 1
        except:
            return
        
        await message.edit(f"<i>Bing photo search count updated to {Media.SEARCH_LIMIT}</i>")


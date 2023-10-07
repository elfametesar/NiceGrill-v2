import html

from nicegrill import Message, run
from telethon import TelegramClient as Client
from telethon.types import MessageEntityUrl
from nicegrill.modules.downloader import Downloader
from pyFunloader import Funload
from httpx import post

import asyncio
import os.path

class Mirror:

    API = "https://pixeldrain.com/api/file/"

    async def upload_to_mirror(file_data):

        return await asyncio.to_thread(
            post,
            url=Mirror.API,
            files={
                "file": file_data,
            },
            follow_redirects=True
        )

    @run(command="mirror")
    async def mirror_file(message: Message, client: Client):
        url_or_file = message.args

        if message.is_reply:
            _, url_or_file = message.get_entities_text(MessageEntityUrl)

        if not url_or_file:
            await message.edit("<i>You haven't provided a URL or a file name to mirror</i>")
            return

        if not os.path.exists(url_or_file):
            action = Funload(
                url=url_or_file,
                block=True,
                progress_bar=True,
                in_memory=True
            )

            await message.edit("<i>Downloading...</i>")

            await action.start()

            await Downloader.regular_progress_bar(
                DownloadAction=action,
                message=message
            )

            url_or_file = action.memory_file.getbuffer().tobytes()

            await message.edit("<i>File has been downloaded, uploading to the mirror host now..</i>")
            await asyncio.sleep(1)
        else:
            with open(url_or_file, "rb+") as fd:
                url_or_file = fd.read()

        await message.edit("<i>Uploading</i>")

        try:
            response = await Mirror.upload_to_mirror(
                file_data=url_or_file
            )
        except Exception as e:
            await message.edit(f"<i>Error: {html.escape(str(e))}")
            return

        if response:
            await message.edit(
                "<i>Your file has been uploaded to the mirror host\n"
                f"You can access it through: </i>{Mirror.API}{response.json().get("id")}",
                link_preview=True
            )
        else:
            await message.edit(
                f"<i>Something went wrong uploading your file to host: \n{response.reason_phrase}</i>")

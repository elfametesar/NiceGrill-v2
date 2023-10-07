import html

from nicegrill import Message, run
from telethon import TelegramClient as Client
from nicegrill.modules.downloader import Downloader
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

        if not url_or_file and not message.is_reply:
            await message.edit("<i>You haven't provided a URL or a file name to mirror</i>")
            return

        if not os.path.exists(url_or_file):

            url_or_file = await Downloader.download_file(message=message, client=client)

            await message.edit("<i>File has been downloaded, uploading to the mirror host now..</i>")
            await asyncio.sleep(1)

        await message.edit("<i>Uploading</i>")

        with open(url_or_file, "rb+") as fd:
            try:
                response = await Mirror.upload_to_mirror(
                    file_data=fd.read()
                )
            except Exception as e:
                await message.edit(f"<i>Error: {html.escape(str(e))}</i>")
                return

        if response:
            await message.edit(
                "<i>Your file has been uploaded to the mirror host\n"
                f"You can access it through: </i>{Mirror.API}{response.json().get('id')}",
                link_preview=False
            )
        else:
            await message.edit(
                f"<i>Something went wrong uploading your file to host: \n{response.reason_phrase}</i>")

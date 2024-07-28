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

from elfrien.types.patched import (
    Message, TextEntityTypeUrl, TextEntityTypeTextUrl
)
from nicegrill.utils import humanize
from elfrien.client import Client
from nicegrill import on, startup
from pyFunloader import Funload
from database import settings
from datetime import datetime

import asyncio
import glob
import html
import os

class Downloader:

    DOWNLOAD_QUEUE = {}
    FLOOD_CONTROL = 7
    PROGRESS_BAR = "○" * 20
    DOWNLOAD_PATH = None

    async def telegram_progress_bar(
        file_name: str,
        received_bytes: int,
        total_bytes: int,
        message: Message,
        start_time: int
    ):
        percentage = round((received_bytes / total_bytes) * 20, 2)

        speed = ((received_bytes) // max((datetime.now() - start_time).seconds, 1))

        message.text = f"""
<b>File Name:</b> <i>{{}}</i>
<b>Size:</b> <i>{humanize(data=total_bytes)}</i>
<b>Speed:</b> <i>{humanize(data=speed)}/s</i>
<b>Time Passed:</b> <i>{humanize(data=(datetime.now() - start_time).seconds, time=True)}</i>
<b>Downloaded:</b> <i>{humanize(data=received_bytes or 1)}</i>
<b>Estimated:</b> <i>{humanize(data=total_bytes // speed, time=True)}</i>
<b>Status:</b> <i>{{}}</i>
<i>{'●' * int(percentage)}{Downloader.PROGRESS_BAR[int(percentage):]}</i>"""

        await message.edit(
            message.text.format(file_name, "Downloading")
        )

    async def regular_progress_bar(DownloadAction: Funload, message: Message):
        while True:
            custom_percentage = round((DownloadAction.downloaded / (DownloadAction.file_size or 1)) * 20, 2)
            custom_percentage = min(custom_percentage, 20)

            try:
                await message.edit(
                    f"""
<b>File Name: </b> <i>{DownloadAction.destination}</i>
<b>Size: </b> <i>{humanize(DownloadAction.file_size)}</i>
<b>Speed: </b> <i>{DownloadAction.speed}</i>
<b>Time Passed: </b> <i>{DownloadAction.elapsed_time}</i>
<b>Downloaded: </b> <i>{humanize(DownloadAction.downloaded)}</i>
<b>Estimated: </b> <i>{DownloadAction.estimate}</i>
<b>Status: </b> <i>{DownloadAction.status}</i>
<i>{'⚈' * int(custom_percentage)}{Downloader.PROGRESS_BAR[int(custom_percentage):]}</i>
"""
                )
            except Exception:
                pass

            if DownloadAction.status == "Downloaded":
                return

            await asyncio.sleep(2)

    @on(pattern="(up|upload)")
    async def upload_file(client: Client, message: Message):
        """
        Uploads specified files to Telegram.

        Usage:
        .upload <file_paths>    # Uploads the specified file(s) to Telegram
        """
        if not message.raw_args:
            await message.edit("<i>Point to files in your file system</i>")
            return

        await message.edit("<i>Uploading the file(s) to Telegram</i>")
        files = []
        for file in message.raw_args.split():
            for file_match in glob.glob(file):
                if os.path.isdir(file_match):
                    continue

                if os.path.islink(file_match):
                    continue

                if not os.access(file_match, os.R_OK):
                    continue

                if os.stat(file_match).st_size == 0:
                    continue

                files.append(file_match)

        if not files:
            await message.edit("<i>Specified files are not valid</i>")
            return

        try:
            await message.respond(
                files=files,
                message="<i>Here's your uploaded file(s))</i>",
                supports_streaming=True,
                force_type="Document"
            )
        except Exception as e:
            await message.respond(f"<i>{e}</i>")

        await message.delete()

    async def telegram_download_file(client: Client, message: Message):

        if not os.path.exists(Downloader.DOWNLOAD_PATH):
            os.makedirs(Downloader.DOWNLOAD_PATH)

        start_time = datetime.now()

        return await message.reply_to_text.download(
            progress_callback=Downloader.telegram_progress_bar,
            progress_args={
                "message": message,
                "start_time": start_time
            },
            path=Downloader.DOWNLOAD_PATH + (message.reply_to_text.file.name or ""),
            wait_time=2
        )

    async def regular_download_file(client: Client, message: Message, urls):

        try:
            if not os.path.exists(Downloader.DOWNLOAD_PATH):
                os.makedirs(Downloader.DOWNLOAD_PATH)

            for url in urls:
                DownloadAction = Funload(
                    destination=Downloader.DOWNLOAD_PATH,
                    url=url,
                    progress_bar=True,
                    block=False
                )
                await DownloadAction.start()

                Downloader.DOWNLOAD_QUEUE[message.id] = DownloadAction

                await Downloader.regular_progress_bar(
                    DownloadAction=DownloadAction,
                    message=message
                )

                if message.id in Downloader.DOWNLOAD_QUEUE:
                    del Downloader.DOWNLOAD_QUEUE[message.id]

                return DownloadAction.destination

        except Exception as e:
            await message.edit(f"<i>Error: {html.escape(str(e))}</i>")

    @on(pattern="(dl|download)")
    async def download_file(client: Client, message: Message):
        """
        Downloads a file from Telegram or a specified URL.

        Usage:
        .download           # Downloads the file in the replied-to message
        .download <url>     # Downloads the file from the specified URL
        """
        if message.reply_to_text and message.reply_to_text.file:
            await message.edit("<i>Download is starting...</i>")
            file_name = message.reply_to_text.file.name or "Unknown"

            task = asyncio.create_task(
                Downloader.telegram_download_file(
                    message=message,
                    client=client
                )
            )

            task.stop = task.cancel
            Downloader.DOWNLOAD_QUEUE[message.id] = task

            try:
                file_name = await task
            except asyncio.CancelledError:
                await message.edit(
                    message.text
                    .format(file_name, "Stopped")
                )
                return

            if message.id in Downloader.DOWNLOAD_QUEUE:
                del Downloader.DOWNLOAD_QUEUE[message.id]

            if message.cmd:
                await message.edit(
                    message.text
                    .replace("⚆", "⚈")
                    .format(file_name, "Finished")
                )

            return file_name

        elif message.reply_to_text or message.raw_args:
            await message.edit("<i>Download is starting...</i>")
            urls = message.get_entities_text(TextEntityTypeUrl)

            if message.reply_to_text:
                urls.extend(message.reply_to_text.get_entities_text(TextEntityTypeUrl))
                urls.extend(
                    [link.url for link in message.reply_to_text.get_entities(TextEntityTypeTextUrl)]
                )

            if not urls:
                await message.edit("<i>There are no URLs to parse in your input</i>")
                return

            return await Downloader.regular_download_file(client, message, urls)

        elif not message.raw_args or not message.reply_to_text:
            await message.edit("<i>You need to either input/reply to a URL or a message that contains media</i>")
            return


    @on(pattern="clear")
    async def clear_downloads(client: Client, message: Message):
        """
        Clears the download folder.

        Usage:
        .clear              # Clears all files in the download folder
        """
        os.system(f"rm -rf {Downloader.DOWNLOAD_PATH}/* 2>&-")
        await message.edit("<i>Download folder has been cleared out</i>")

    @on(pattern="setpath")
    async def set_download_path(client: Client, message: Message):
        """
        Sets the download path for future downloads.

        Usage:
        .setpath <path>     # Sets the specified path as the download directory
        """
        if not message.raw_args:
            await message.edit("<i>Input a valid path for your downloads to go in</i>")
            return

        download_path = message.raw_args.rstrip("/") + "/"

        if os.path.exists(download_path):
            if not os.access(message.raw_args, os.W_OK):
                await message.edit("<i>This path is not suitable for your downloads</i>")
                return

        else:
            try:
                await message.edit("<i>This path doesn't exist in your filesystem, creating it for you</i>")
                await asyncio.sleep(1.5)
                os.makedirs(message.raw_args)
            except Exception as e:
                await message.edit(f"<i>Error: {e}</i>")
                return

        settings.set_download_path(download_path)
        Downloader.DOWNLOAD_PATH = download_path

        await message.edit(f"<i>New directory for your downloads is set to {message.raw_args}</i>")

    @on(pattern="(stop|pause|resume|retry)")
    async def control_download(client: Client, message: Message):
        """
        Controls the state of a running download.

        Usage:
        .stop               # Stops the running download
        .pause              # Pauses the running download
        .resume             # Resumes the paused download
        .retry              # Retries the failed download
        """
        if not message.reply_to_text:
            await message.edit("<i>You need to reply to a message running a download action first</i>")
            return

        if message.reply_to_text.id not in Downloader.DOWNLOAD_QUEUE:
            await message.edit("<i>No download action on this message</i>")
            return

        task: asyncio.Task | Funload = Downloader.DOWNLOAD_QUEUE[message.reply_to_text.id]

        try:
            if message.cmd == "stop":
                Downloader.DOWNLOAD_QUEUE[message.reply_to_text.id].stop()
                result = "<i>Download action successfully stopped</i>"
            elif message.cmd == "pause":
                task.pause()
                result = "<i>Download action paused</i>"
            elif message.cmd == "resume":
                task.resume()
                result = "<i>Download resumes where it was left off</i>"
            elif message.cmd == "retry":
                result = "<i>Download action restarting</i>"
                asyncio.create_task(task.retry())

            await message.edit(result)
        except Exception as e:
            print(e)
            if isinstance(task, asyncio.Task):
                await message.edit(f"<i>Telegram downloads do not support {message.cmd}</i>")
            else:
                await message.edit(f"<i>Error: {e}</i>")

@startup
def load_from_database():
    Downloader.DOWNLOAD_PATH = settings.get_download_path() or "../downloads"
    Downloader.DOWNLOAD_PATH = Downloader.DOWNLOAD_PATH.rstrip("/") + "/"

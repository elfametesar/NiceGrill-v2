from datetime import datetime
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl
from telethon import TelegramClient as Client
from database import settingsdb
from pyFunloader import Funload
from nicegrill import Message, run, startup
from nicegrill.utils import humanize

import asyncio
import os
import glob
import html


class Downloader:

    DOWNLOAD_QUEUE = {}
    FLOOD_CONTROL = 7
    PROGRESS_BAR = "○" * 20
    DOWNLOAD_PATH = None

    async def telegram_progress_bar(message: Message, received_bytes, total_bytes, file_name, start_time):
        percentage = round((received_bytes / total_bytes) * 20, 2)

        speed = ((received_bytes) // max((datetime.now() - start_time).seconds, 1))

        message.text = f"""
<b>File Name:</b> <i>{{}}</i>
<b>Size:</b> <i>{await humanize(data=total_bytes)}</i>
<b>Speed:</b> <i>{await humanize(data=speed)}/s</i>
<b>Time Passed:</b> <i>{await humanize(data=received_bytes // speed, time=True)}</i>
<b>Downloaded:</b> <i>{await humanize(data=received_bytes)}</i>
<b>Estimated:</b> <i>{await humanize(data=total_bytes // speed, time=True)}</i>
<b>Status:</b> <i>{{}}</i>
<i>{'●' * int(percentage)}{Downloader.PROGRESS_BAR[int(percentage):]}</i>"""

        if percentage < 99:
            if Downloader.FLOOD_CONTROL > 12:
                Downloader.FLOOD_CONTROL = 0
                await message.edit(
                    message.text.format(file_name, "Downloading")
                )
            else:
                Downloader.FLOOD_CONTROL += 1
        else:
            await asyncio.sleep(1)

    async def regular_progress_bar(DownloadAction: Funload, message: Message):
        while True:
            custom_percentage = round((DownloadAction.downloaded / (DownloadAction.file_size or 1)) * 20, 2)
            custom_percentage = min(custom_percentage, 20)

            try:
                await message.edit(
                    f"""
<b>File Name: </b> <i>{DownloadAction.destination}</i>
<b>Size: </b> <i>{await humanize(DownloadAction.file_size)}</i>
<b>Speed: </b> <i>{DownloadAction.speed}</i>
<b>Time Passed: </b> <i>{DownloadAction.elapsed_time}</i>
<b>Downloaded: </b> <i>{await humanize(DownloadAction.downloaded)}</i>
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

    @run(command="(up|upload)")
    async def upload_file(message: Message, client: Client):
        if not message.args:
            await message.edit("<i>Point to files in your file system</i>")
            return

        await message.edit("<i>Uploading the file(s) to Telegram</i>")
        files = []
        for file in message.args.split():
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
            await client.send_file(
                entity=message.chat,
                file=files,
                caption="<i>Here's your uploaded file(s))</i>",
                video_note=True,
                voice_note=True,
                supports_streaming=True,
                nosound_video=True
            )
        except Exception as e:
            await message.respond(f"<i>{e}</i>")

        await message.delete()

    async def telegram_download_file(message: Message, client: Client, file_name):
        await message.edit("<i>Download is starting...</i>")

        if not os.path.exists(Downloader.DOWNLOAD_PATH):
            os.makedirs(Downloader.DOWNLOAD_PATH)

        start_time = datetime.now()

        return await client.download_media(
            message=message.reply_to_text,
            progress_callback=lambda received_bytes, total_bytes:
            asyncio.create_task(
                Downloader.telegram_progress_bar(
                    message=message,
                    file_name=file_name,
                    total_bytes=total_bytes,
                    received_bytes=received_bytes,
                    start_time=start_time
                )
            ),
            file=Downloader.DOWNLOAD_PATH
        )

    async def regular_download_file(message: Message, client: Client, urls):
        await message.edit("<i>Download is starting...</i>")
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

    @run(command="(dl|download)")
    async def download_file(message: Message, client: Client):
        if message.is_reply and message.reply_to_text.file:
            file_name = message.reply_to_text.file.name or "Unknown"

            task = asyncio.create_task(
                Downloader.telegram_download_file(
                    message=message,
                    client=client,
                    file_name=file_name
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

            await message.edit(
                message.text
                .format(file_name, "Finished")
                .replace("⚆", "⚈")
            )

            return file_name

        elif message.is_reply or message.args:
            urls = [link for _, link in message.get_entities_text(MessageEntityUrl)]

            if message.is_reply:
                urls.extend(
                    [link for _, link in message.reply_to_text.get_entities_text(MessageEntityUrl)]
                )
                urls.extend(
                    [link.url for link, _ in message.reply_to_text.get_entities_text(MessageEntityTextUrl)]
                )

            if not urls:
                await message.edit("<i>There are no URLs to parse in your input</i>")
                return

            return await Downloader.regular_download_file(message, client, urls)

        elif not message.args or not message.is_reply:
            await message.edit("<i>You need to either input/reply to a URL or a message that contains media</i>")
            return


    @run(command="clear")
    async def clear_downloads(message: Message, client: Client):
        os.system(f"rm -rf {Downloader.DOWNLOAD_PATH}/* 2>&-")
        await message.edit("<i>Download folder has been cleared out</i>")

    @run(command="setpath")
    async def set_download_path(message: Message, client: Client):
        if not message.args:
            await message.edit("<i>Input a valid path for your downloads to go in</i>")
            return

        download_path = message.args.rstrip("/") + "/"

        if os.path.exists(download_path):
            if not os.access(message.args, os.W_OK):
                await message.edit("<i>This path is not suitable for your downloads</i>")
                return

        else:
            try:
                await message.edit("<i>This path doesn't exist in your filesystem, creating it for you</i>")
                await asyncio.sleep(1.5)
                os.makedirs(message.args)
            except Exception as e:
                await message.edit(f"<i>Error: {e}</i>")
                return

        settingsdb.set_download_path(download_path)
        Downloader.DOWNLOAD_PATH = download_path

        await message.edit(f"<i>New directory for your downloads is set to {message.args}</i>")

    @run(command="(stop|pause|resume|retry)")
    async def control_download(message: Message, client: Client):
        if not message.is_reply:
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
            if isinstance(task, asyncio.Task):
                await message.edit(f"<i>Telegram downloads do not support {message.cmd}</i>")
            else:
                await message.edit(f"<i>Error: {e}</i>")


@startup
def load_from_database():
    Downloader.DOWNLOAD_PATH = settingsdb.get_download_path() or "../downloads"
    Downloader.DOWNLOAD_PATH = Downloader.DOWNLOAD_PATH.rstrip("/") + "/"

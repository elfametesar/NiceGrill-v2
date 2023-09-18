from datetime import datetime
from telethon.tl.patched import Message
from telethon.tl.types import MessageEntityUrl
from telethon import TelegramClient
from database import settingsdb
from pySmartDL import SmartDL
from main import run, startup
from utils import human_readables

import asyncio
import os
import glob
import re

class Downloader:

    DOWNLOAD_QUEUE = {}
    FLOOD_CONTROL = 7
    PROGRESS_BAR = "⚆" * 20
    DOWNLOAD_PATH = None


    async def telegram_progress_bar(message, received_bytes, total_bytes, file_name, start_time):
        percentage = round((received_bytes / total_bytes) * 20, 2)

        speed = ((received_bytes) // max((datetime.now() - start_time).seconds, 1))
        
        message.text = f"""
<b>File Name:</b> <i>{{}}</i>
<b>Size:</b> <i>{await human_readables(data=total_bytes)}</i>
<b>Speed:</b> <i>{await human_readables(speed)}/s</i>
<b>Time Passed:</b> <i>{await human_readables(seconds=received_bytes//speed)}</i>
<b>Downloaded:</b> <i>{await human_readables(received_bytes)}</i>
<b>Estimated:</b> <i>{await human_readables(seconds=total_bytes//speed)}</i>
<b>Status:</b> <i>{{}}</i>
<i>{'⚈' * int(percentage)}{Downloader.PROGRESS_BAR[int(percentage):]}</i>"""
        
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


    async def regular_progress_bar(DownloadAction, message: Message, start_time):
        file_name = file_size = ""
        while True:
            status = DownloadAction.get_status().capitalize()
                
            if message.id not in Downloader.DOWNLOAD_QUEUE:
                status = "Stopped"

            if not file_name:
                file_name = await asyncio.to_thread(DownloadAction.get_dest)
            if not file_size:
                file_size = await asyncio.to_thread(DownloadAction.get_final_filesize, human=True)

            download_speed, time_passed, received_data, estimated_time, progress_bar = \
                await asyncio.gather(
                    asyncio.to_thread(DownloadAction.get_speed, human=True),
                    asyncio.to_thread(datetime.now),
                    asyncio.to_thread(DownloadAction.get_dl_size, human=True),
                    asyncio.to_thread(DownloadAction.get_eta, human=True),
                    asyncio.to_thread(DownloadAction.get_progress_bar)
                )
            progress_bar = progress_bar.replace('-', '⚆')\
                                       .replace('#', '⚈')\
                                       .replace('[', '')\
                                       .replace(']', '')

            time_passed = str(time_passed - start_time)[0:-7]
            
            await message.edit(
                f"""
<b>File Name: </b> <i>{file_name}</i>
<b>Size: </b> <i>{file_size}</i>
<b>Speed: </b> <i>{download_speed}</i>
<b>Time Passed: </b> <i>{time_passed}</i>
<b>Downloaded: </b> <i>{received_data}</i>
<b>Estimated: </b> <i>{estimated_time}</i>
<b>Status: </b> <i>{status}</i>
{progress_bar}
"""
            )
            
            if status == "Stopped" or status == "Finished":
                break
            
            await asyncio.sleep(2)


    @run(command="(up|upload)")
    async def upload_file(message: Message, client: TelegramClient):
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
            await message.edit("<i>Inputted files are not valid</i>")
            return

        try:
            await message.respond(
                file=files,
                message="<i>Here's your uploaded file(s))</i>"
            )
        except Exception as e:
            await message.respond(f"<i>{e}</i>")

        await message.delete()


    async def telegram_download_file(message: Message, client: TelegramClient, file_name):
        await message.edit("<i>Download is starting...</i>")
        
        if not os.path.exists(Downloader.DOWNLOAD_PATH):
            os.makedirs(Downloader.DOWNLOAD_PATH)
        
        start_time = datetime.now()

        return await client.download_media(
            message=message.replied,
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

    async def regular_download_file(message: Message, client: TelegramClient, urls):
        await message.edit("<i>Download is starting...</i>")
        try:
            if not os.path.exists(Downloader.DOWNLOAD_PATH):
                os.makedirs(Downloader.DOWNLOAD_PATH)

            for url in urls:
                DownloadAction = SmartDL(
                    urls=url, 
                    dest=Downloader.DOWNLOAD_PATH,
                    progress_bar=False,
                    threads=os.cpu_count()
                )
                DownloadAction.start(blocking=False)

                Downloader.DOWNLOAD_QUEUE[message.id] = DownloadAction

                await Downloader.regular_progress_bar(
                    DownloadAction=DownloadAction,
                    message=message,
                    start_time=datetime.now()
                )

                if message.id in Downloader.DOWNLOAD_QUEUE:
                    del Downloader.DOWNLOAD_QUEUE[message.id]
            
        except Exception as e:
            await message.edit(f"<i>Error: {e}</i>")


    @run(command="(dl|download)")
    async def download_file(message: Message, client: TelegramClient):
        if message.is_reply and message.replied.media:
            file_name = "unknown"
            if message.replied.document:
                if file_name := re.search("file_name='(.*?)'", str(message.replied.document)):
                    file_name = file_name.group(1)
                else:
                    file_name = "unknown"
            
            task = asyncio.create_task(
                Downloader.telegram_download_file(
                    message,
                    client,
                    file_name
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

        elif message.is_reply or message.args:
            urls = message.get_entities_text(MessageEntityUrl)

            if message.is_reply:
                urls.extend(
                    message.replied.get_entities_text(MessageEntityUrl)
                )
            
            urls = [x[1] for x in urls]

            if not urls:
                await message.edit("<i>There are no URLs to parse in your input</i>")
                return

            await Downloader.regular_download_file(message, client, urls)
        
        elif not message.args or not message.is_reply:
            await message.edit("<i>You need to either input/reply to a URL or a message that contains media</i>")
            return

    @run(command="clear")
    async def clear_downloads(message: Message, client: TelegramClient):
        os.system(f"rm -rf {Downloader.DOWNLOAD_PATH}/* 2>&-")
        await message.edit("<i>Download folder has been cleared out</i>")


    @run(command="setpath")
    async def set_download_path(message: Message, client: TelegramClient):
        if not message.args:
            await message.edit("<i>Input a valid path for your downloads to go in</i>")
            return
        
        absolute_path = os.path.abspath(message.args)
        
        if os.path.exists(absolute_path):
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
        
        settingsdb.set_download_path(message.args)
        Downloader.DOWNLOAD_PATH = message.args

        await message.edit(f"<i>New directory for your downloads is set to {message.args}</i>")


    @run(command="(stop|pause|resume)")
    async def control_download(message: Message, client: TelegramClient):
        if not message.is_reply:
            await message.edit("<i>You need to reply to a message running a download action first</i>")
            return
        
        if message.replied.id not in Downloader.DOWNLOAD_QUEUE:
            await message.edit("<i>No download action on this message</i>")
            return
        
        task = Downloader.DOWNLOAD_QUEUE[message.replied.id]
        
        try:
            if message.cmd == "stop":
                Downloader.DOWNLOAD_QUEUE[message.replied.id].stop()
                del Downloader.DOWNLOAD_QUEUE[message.replied.id]
                result = "<i>Download action successfully stopped</i>"
            elif message.cmd == "pause":
                task.pause()
                result = "<i>Download action paused</i>"
            elif message.cmd == "resume":
                task.unpause()
                result = "<i>Download resumes where it was left off</i>"

            await message.edit(result)
        except Exception as e:
            if isinstance(task, asyncio.Task):
                await message.edit(f"<i>Telegram downloads do not support {message.cmd}</i>")
            else:
                await message.edit(f"<i>Error: {e}</i>")

@startup
def load_from_database():
    Downloader.DOWNLOAD_PATH = settingsdb.get_download_path() or "downloads"
    Downloader.DOWNLOAD_PATH = Downloader.DOWNLOAD_PATH.rstrip("/") + "/"

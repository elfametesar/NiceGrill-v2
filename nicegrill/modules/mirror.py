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

from google_auth_oauthlib.flow import InstalledAppFlow
from nicegrill.modules.downloader import Downloader
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from telethon import TelegramClient as Client
from googleapiclient.discovery import build
from httpx import post as post2, BasicAuth
from nicegrill.utils import ProcessManager
from elfrien.types.patched import Message
from config import PIXELDRAIN_API_KEY
from requests import post
from nicegrill import on

import urllib.parse
import mimetypes
import asyncio
import os.path
import html

class Mirror:

    PIXEL_API = "https://pixeldrain.com/api/file/"
    FILEIO_API = "https://file.io"
    GOFILE_API = "https://store4.gofile.io/contents/uploadFile"
    GDRIVE_URL = "https://drive.google.com/file/d/{}/view?usp=sharing"

    async def authenticate(message: Message):

        creds = None
        scopes = ['https://www.googleapis.com/auth/drive']

        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', scopes)

        if creds and not creds.valid:
            creds.refresh(Request())

        elif not creds:
            if not os.path.isfile("client_secret.json"):
                raise FileNotFoundError("You need client_secret.json to run this, obtain it from Google Cloud")

            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', scopes, redirect_uri="http://localhost/authorize/")

            auth_url, _ = flow.authorization_url()

            if not message.is_private:
                await message.edit("<b>Bot response: </b><i>Check your private chat</i>")

            message = await message.client.send_message(
                message=f"<i>You need to do Google Auth before you can continue. "
                f"Your auth URL sent to your private chat for privacy reasons. "
                f"Complete the auth process and reply to this message with </i><code>.input your_auth_code</code>. <i>"
                f"You can find the authentication code in the final URL after completing the process."
                f"It comes after 'code='. Here is the authentication link: </i>\n\n{html.escape(auth_url)}",
                entity='me'
            )

            fetch_code = asyncio.create_task(
                asyncio.to_thread(input)
            )

            ProcessManager.add_process(
                message_id=message.id,
                process=fetch_code
            )

            code = urllib.parse.unquote(await fetch_code)

            flow.fetch_token(code=code)
            creds = flow.credentials

            ProcessManager.remove_process(message.id)

            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        return build('drive', 'v3', credentials=creds)

    async def get_file(client: Client, message: Message):

        url_or_file = message.args

        if not url_or_file and not message.reply_to_text:
            await message.edit("<i>You haven't provided a URL or a file name to mirror</i>")
            return

        if not os.path.exists(url_or_file):
            await message.edit("<i>Downloading...</i>")

            message.cmd = ''
            url_or_file = await Downloader.download_file(client=client, message=message)

            if not url_or_file:
                await message.edit("<i>Mirroring has been cancelled</i>")
                return

            await message.edit("<i>File has been downloaded, uploading to mirror host now..</i>")
            await asyncio.sleep(1)

        return url_or_file

    @on(pattern="gdrive")
    async def mirror_to_gdrive(client: Client, message: Message):
        """
        Uploads a file to Google Drive and provides the download link.

        Usage:
        .gdrive <url or file>   # Uploads the given URL or file to Google Drive
        """

        url_or_file = await Mirror.get_file(message=message, client=client)

        if not url_or_file:
            return

        await message.edit("<i>Uploading...</i>")

        try:
            service = await Mirror.authenticate(message=message)

            metadata = {
                "name": os.path.basename(url_or_file)
            }

            permissions = {
                'value': 'default',
                'type': 'anyone',
                'role': 'reader'
            }

            media = MediaFileUpload(
                filename=url_or_file,
                resumable=True,
                chunksize=4000000
            )

            file = service.files().create(
                body=metadata,
                media_body=media,
                fields='id'
            )
            
            file = await asyncio.to_thread(file.execute)

            service.permissions().create(
                body=permissions,
                fileId=file.get('id'),
                fields="id"
            ).execute()

            await message.edit(
                "<i>File has been uploaded to your Google Drive.\n"
                f"You can access it via: </i>\n" +
                Mirror.GDRIVE_URL.format(file.get('id'))
            )

        except Exception as e:
            await message.edit(f"<i>Error: {html.escape(str(e))}</i>")
            return

    async def upload_to_pixeldrain(file_data):

        return await asyncio.to_thread(
            post2,
            url=Mirror.PIXEL_API,
            files={
                "file": file_data,
            },
            follow_redirects=True,
            auth=BasicAuth(
                username="",
                password=PIXELDRAIN_API_KEY
            )
        )

    @on(pattern="gofile")
    async def mirror_to_gofile(client: Client, message: Message):
        """
        Uploads a file to Gofile and provides the download link.

        Usage:
        .gofile <url or file>   # Uploads the given URL or file to Gofile
        """
        url_or_file = await Mirror.get_file(message=message, client=client)

        if not url_or_file:
            return

        await message.edit("<i>Uploading</i>")

        files = {
            'file': (url_or_file, open(url_or_file, 'rb'), mimetypes.guess_type(url_or_file))
        }

        response = post(
            url=Mirror.GOFILE_API,
            files=files
        )

        if response.ok:
            await message.edit(
                "<i>Your file has been uploaded to the mirror host\n"
                f"You can access it through: </i>{response.json().get('data').get('downloadPage')}",
                link_preview=False
            )
        else:
            await message.edit(
                f"<i>Something went wrong uploading your file to host: \n{response.reason}</i>")

    @on(pattern="pixel")
    async def mirror_to_pixeldrain(client: Client, message: Message):
        """
        Uploads a file to Pixeldrain and provides the download link.

        Usage:
        .pixel <url or file>   # Uploads the given URL or file to Pixeldrain
        """
        url_or_file = await Mirror.get_file(message=message, client=client)

        if not url_or_file:
            return

        await message.edit("<i>Uploading</i>")

        with open(url_or_file, "rb+") as fd:
            try:
                response = await Mirror.upload_to_pixeldrain(
                    file_data=fd.read()
                )
            except Exception as e:
                await message.edit(f"<i>Error: {html.escape(str(e))}</i>")
                return

        if response:
            await message.edit(
                "<i>Your file has been uploaded to the mirror host\n"
                f"You can access it through: </i>{Mirror.PIXEL_API}{response.json().get('id')}",
                link_preview=False
            )
        else:
            await message.edit(
                f"<i>Something went wrong uploading your file to host: \n{response.reason_phrase}</i>")

    @on(pattern="fileio")
    async def mirror_to_fileio(client: Client, message: Message):
        """
        Uploads a file to Anonfiles and provides the download link.

        Usage:
        .fileio <url or file>   # Uploads the given URL or file to Anonfiles
        """
        url_or_file = await Mirror.get_file(message=message, client=client)

        if not url_or_file:
            return

        await message.edit("<i>Uploading</i>")

        with open(url_or_file, "rb+") as fd:
            response = await asyncio.to_thread(
                post,
                url=Mirror.FILEIO_API,
                files={"file": fd},
                allow_redirects=True
            )

            if response:
                await message.edit(
                    "<i>Your file has been uploaded to the mirror host\n"
                    f"You can access it through: </i>{response.json().get('link')}",
                    link_preview=False
                )
            else:
                await message.edit(
                    f"<i>Something went wrong uploading your file to host: \n{response.reason_phrase}</i>")

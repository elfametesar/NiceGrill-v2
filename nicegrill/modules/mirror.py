from nicegrill import Message, run
from telethon import TelegramClient as Client
from nicegrill.modules.downloader import Downloader
from nicegrill.modules.compiler import Compiler
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from httpx import post

import asyncio
import os.path
import html
import urllib.parse

class Mirror:

    API = "https://pixeldrain.com/api/file/"
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

            Compiler.PROCESSES.update(
                {message.id: fetch_code}
            )

            code = urllib.parse.unquote(await fetch_code)

            flow.fetch_token(code=code)
            creds = flow.credentials

            del Compiler.PROCESSES[message.id]

            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        return build('drive', 'v3', credentials=creds)

    async def get_file(message: Message, client: Client):

        url_or_file = message.args

        if not url_or_file and not message.is_reply:
            await message.edit("<i>You haven't provided a URL or a file name to mirror</i>")
            return

        if not os.path.exists(url_or_file):
            await message.edit("<i>Downloading...</i>")

            url_or_file = await Downloader.download_file(message=message, client=client)

            await message.edit("<i>File has been downloaded, uploading to PixelDrain now..</i>")
            await asyncio.sleep(1)

        return url_or_file

    @run(command="gdrive")
    async def mirror_to_gdrive(message: Message, client: Client):

        url_or_file = await Mirror.get_file(message=message, client=client)

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
            post,
            url=Mirror.API,
            files={
                "file": file_data,
            },
            follow_redirects=True
        )

    @run(command="pixel")
    async def mirror_to_pixeldrain(message: Message, client: Client):
        url_or_file = await Mirror.get_file(message=message, client=client)

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
                f"You can access it through: </i>{Mirror.API}{response.json().get('id')}",
                link_preview=False
            )
        else:
            await message.edit(
                f"<i>Something went wrong uploading your file to host: \n{response.reason_phrase}</i>")

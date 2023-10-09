from telethon import TelegramClient
from telethon.sessions import StringSession
from config import API_ID, API_HASH, SESSION, MONGO_URI
from database import settingsdb
from io import StringIO

import asyncio
import importlib
import glob
import sys
import os

class NiceGrill:
    def __init__(self):
        self.client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

    def read_stdout(self):
        output = sys.stdout.getvalue()
        sys.stdout.seek(os.SEEK_END)
        sys.stdout.truncate(0)
        sys.stdout.seek(0)
        return output

    def write_stdout(self, func):
        def inner(args):
            print(args, end="", file=sys.__stdout__)
            func(args)
        return inner

    async def redirect_pipes(self):

        sys.stdout = StringIO()
        sys.stdout.read = self.read_stdout
        sys.stdout.write = self.write_stdout(sys.stdout.write)
        
        read, write = os.pipe()

        stdin_read = os.fdopen(
            fd=read,
            mode="r",
            buffering=True
        )

        stdin_write = os.fdopen(
            fd=write,
            mode="w",
            buffering=True
        )

        stdin_read.write = stdin_write.write
        stdin_read.writelines = stdin_write.writelines

        sys.stdin = stdin_read

    async def import_modules(self):
        for module in glob.glob("nicegrill/modules/*.py"):
            module = module.replace("/", ".")[:-3]

            if module == "nicegrill.modules.help":
                continue

            try:
                importlib.import_module(module)
                print(f"Module is loaded: {module.replace('nicegrill.modules.', '').title()}")
            except Exception as e:
                print(f"\nModule {module.replace('nicegrill.modules.', '').title()} not loaded: {e}\n")

        importlib.import_module("nicegrill.modules.help")

    async def restart_handler(self):
        if restart_info := settingsdb.get_restart_details():
            try:
                await self.client.edit_message(
                    entity=restart_info["Chat"],
                    text="<i>Restarted</i>",
                    message=restart_info["Message"]
                )
            except:
                pass

    async def initialize_bot(self):

        await self.client.connect()

        self.client.parse_mode = 'html'
        self.client.me = await self.client.get_me()
        self.client._loop = asyncio.get_event_loop()

        await self.redirect_pipes()

        await asyncio.gather(
            self.import_modules(),
            self.restart_handler()
        )

        print(f"\nLogged in as {self.client.me.first_name}\n")

        await self.client.run_until_disconnected()


if not API_ID or not API_HASH or not SESSION or not MONGO_URI:
    print(
"""
Your API_HASH, API_ID, SESSION or MONGO_URI cannot be empty, add to your shell configuration:

export API_HASH='YOUR_API_HASH'
export API_ID='YOUR_API_ID'
export SESSION='YOUR_STRING_SESSION'
export MONGO_URI='YOUR_MONGO_URI'
""")
    exit(1)

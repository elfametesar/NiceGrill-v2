from telethon import TelegramClient
from telethon.sessions import StringSession
from config import API_ID, API_HASH, SESSION, MONGO_URI
from database import settingsdb

import asyncio
import importlib
import glob
import sys
import os


class Stream:

    def __init__(self):
        self.__buffer = ""

    def read(self) -> str:
        while not (output := self.__buffer):
            pass

        self.__buffer = ""
        print(output, file=sys.__stdout__)
        return output
    
    def readline(self) -> str:
        self.__buffer = self.__buffer.rstrip()
        return self.read()

    def write(self, input_value: str) -> int:
        self.__buffer += input_value
        print(input_value, end="", file=sys.__stdout__)
        return len(input_value)
    
    def flush(self):
        self.__buffer += "\n"
    
    def input(self, prompt: str="") -> str:
        return prompt + self.read()

    @property
    def is_empty(self):
        return not self.__buffer
    
    def clear(self):
        self.__buffer = ""


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

    async def import_modules(self):
        module_list = glob.glob("nicegrill/modules/*.py")
        module_list.remove("nicegrill/modules/help.py")
        module_list.append("nicegrill/modules/help.py")

        for module in module_list:

            module = module.replace("/", ".")[:-3]

            try:
                importlib.import_module(module)
                print(f"Module is loaded: {module.replace('nicegrill.modules.', '').title()}")
            except Exception as e:
                print(f"\nModule {module.replace('nicegrill.modules.', '').title()} not loaded: {e}\n")

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

        sys.stdout = Stream()
        sys.stdin = sys.stdout
        __builtins__["input"] = sys.stdout.input

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

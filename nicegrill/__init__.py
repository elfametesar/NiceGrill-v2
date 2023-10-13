import telethon
from nicegrill.utils import get_messages_recursively, Message
from config import API_ID, API_HASH, SESSION, MONGO_URI
from database import blacklistdb, settingsdb
from telethon.events import NewMessage, MessageEdited
from telethon import TelegramClient
from telethon.sessions import StringSession
from database import settingsdb
from exrex import generate

import re
import logging
import asyncio
import importlib
import sys
import glob
import os


stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.ERROR)

logging.basicConfig(
    handlers=[logging.FileHandler("error.txt", mode='w+'), stream_handler],
    level=logging.ERROR,
    format='%(asctime)s\n\n%(message)s'
)

log = logging.getLogger(__name__)

HELP_MENU_DATA = {}
HELP_MENU_CAPTION = "<b>•\tHELP\t•</b>".expandtabs(47)
HELP_MENU = HELP_MENU_CAPTION

bad_chat_list = blacklistdb.get_all_blacklisted()
prefix = settingsdb.get_prefix()

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


async def error_handler(message: Message):
    log.exception("")

    await message.edit("<b>Loading..</b>")
    await message.respond(
        file="error.txt",
        message="<b>NiceGrill has crashed. Command was </b>"
                f"<code>{message.cmd}</code><b>.\n"
                "Check logs for more information.</b>"
    )
    
    await message.delete()

    with open('../error.txt', 'w'):
        pass

def update_help_data(function, command: str):
    global HELP_MENU_DATA, HELP_MENU

    try:
        class_name = function.__qualname__.split(".")[-2]
    except:
        class_name = "No Name"
    
    if class_name not in HELP_MENU:
        HELP_MENU = f"{HELP_MENU[:-2]}</i>\n\n<b>⬤ {class_name}:</b>\n"

    try:
        regex_parse = generate(command, command)
        for result in regex_parse:
            HELP_MENU += f"<i>{result}, "
            HELP_MENU_DATA.update({result: function.__doc__})
    except:
        pass

def return_func(func, command="", prefix=prefix, recurse_messages=True):
    async def wrapper(message: Message, command=command):
        if recurse_messages:
            try:
                message = await get_messages_recursively(
                    message=message.message,
                    command=command,
                    prefix=prefix
                )
            except Exception as e:
                print(e)
                pass

        try:
            if command == "blacklist" or command == "whitelist":
                await func(message, nicegrill.client)
                return

            if message.chat_id not in bad_chat_list:
                await func(message, nicegrill.client)

        except:
            if message.is_private:
                await error_handler(message)

    return wrapper


def event_watcher(
        incoming=True, outgoing=True, forwards=False, custom_event=None,
        pattern=".*", blacklist=None, users=None, chats=None,):
    
    def inner(func):
        wrapper = return_func(func)
        nicegrill.client.add_event_handler(
            callback=wrapper,
            event=NewMessage(
                pattern=pattern,
                incoming=incoming,
                outgoing=outgoing,
                forwards=forwards,
                chats=chats,
                blacklist_chats=blacklist,
                from_users=users,
                func=custom_event
            )
        )
        nicegrill.client.add_event_handler(
            callback=wrapper,
            event=MessageEdited(
                pattern=pattern,
                incoming=incoming,
                outgoing=outgoing,
                forwards=forwards,
                chats=chats,
                blacklist_chats=blacklist,
                from_users=users,
                func=custom_event
            )
        )
        return func

    return inner

def chat_watcher(custom_event=None, chats=None):
    
    def inner(func):
        wrapper = return_func(func, recurse_messages=False)

        nicegrill.client.add_event_handler(
            callback=wrapper,
            event=telethon.events.ChatAction(
                chats=chats,
                func=custom_event
            )
        )

        return func

    return inner


def run(
        command=None, prefix=prefix, incoming=False, outgoing=True,
        forwards=False, blacklist=None, users=None, chats=None, custom_event=None):

    escaped_prefix = re.escape(prefix)

    def inner(func, command=command):
        wrapper = return_func(func, command, prefix)
        
        update_help_data(
            function=func,
            command=command
        )

        nicegrill.client.add_event_handler(
            callback=wrapper,
            event=NewMessage(
                pattern=escaped_prefix + command + r"($| |\n)",
                incoming=incoming,
                outgoing=outgoing,
                forwards=forwards,
                chats=chats,
                blacklist_chats=blacklist,
                from_users=users,
                func=custom_event
            )
        )
        nicegrill.client.add_event_handler(
            callback=wrapper,
            event=MessageEdited(
                pattern=escaped_prefix + command + r"($| |\n)",
                incoming=incoming,
                outgoing=outgoing,
                forwards=forwards,
                chats=chats,
                blacklist_chats=blacklist,
                from_users=users,
                func=custom_event
            )
        )

        return func

    return inner

def classhelp(class_object):
    HELP_MENU_DATA.update({class_object.__name__.lower(): class_object.__doc__})

def startup(func):
    func()


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


nicegrill = NiceGrill()
asyncio.run(nicegrill.initialize_bot())
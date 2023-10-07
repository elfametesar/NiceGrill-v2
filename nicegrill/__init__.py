from database import blacklistdb, settingsdb
from nicegrill.utils import get_messages_recursively, Message
from telethon.events import NewMessage, MessageEdited
from exrex import generate
from nicegrill.__main__ import NiceGrill

import re
import logging
import asyncio

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

async def error_handler(message: Message):
    log.exception("")

    await message.edit("<b>Loading..</b>")
    await message.respond(
        file="error.txt",
        message="<b> has crashed. Command was </b>"
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


def return_func(func, command="", prefix=prefix):
    async def wrapper(message: Message, command=command):
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
            if message.sender_id == nicegrill.client.me.id:
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


nicegrill = NiceGrill()
asyncio.run(nicegrill.initialize_bot())
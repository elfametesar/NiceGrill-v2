from telethon.sync import TelegramClient, events
from database import blacklistdb, settingsdb
from init import client
from exrex import generate

import utils
import logging
import re
import asyncio

HELP_MENU_DATA = {}
HELP_MENU_CAPTION = "<b>•\tHELP\t•</b>".expandtabs(40)
HELP_MENU = HELP_MENU_CAPTION

logging.basicConfig(
    filename="error.txt",
    level=logging.ERROR,
    format='%(asctime)s  %(name)s  %(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)
file_handler = logging.FileHandler("error.txt")
file_handler.setLevel(logging.ERROR)
formatter = logging.Formatter(
    '%(asctime)s  %(name)s  %(levelname)s: %(message)s'
)


async def error_handler(message):
    logger.exception("")
    await message.edit("<b>Loading..</b>")
    await message.respond(
        file="error.txt",
        message=f"<b>NiceGrill has crashed. Command was </b>"
                f"<code>{message.cmd}</code><b>.\n"
                "Check logs for more information.</b>"
    )
    await message.delete()

    with open('error.txt', 'w'):
        pass


bad_chat_list = blacklistdb.get_all_blacklisted() or []
prefix = settingsdb.get_prefix() or "."


def return_func(func, command="", prefix=prefix):
    async def wrapper(message, command=command):
        message.replied = await message.get_reply_message()

        if command:
            message.args = utils.get_arg(message)
        else:
            message.args = message.message.message
        if prefix:
            get_cmd = re.search(command + r"($| |\n)", message.message.message)
            if get_cmd:
                command = get_cmd.group(0).strip()

        try:

            message.cmd = command
            message.prefix = prefix

            if command == "blacklist" or command == "whitelist":
                await func(message, client)
                return

            if message.chat_id not in bad_chat_list:
                await func(message, client)

        except:
            if message.sender_id == client.ME.id:
                await error_handler(message)
            else:
                pass

    return wrapper


def event_watcher(
        incoming=True, outgoing=True, forwards=False,
        pattern=".*", blacklist=None, users=None, chats=None):
    
    def inner(func):
        wrapper = return_func(func)
        client.add_event_handler(
            callback=wrapper,
            event=events.NewMessage(
                pattern=pattern,
                incoming=incoming,
                outgoing=outgoing,
                forwards=forwards,
                chats=chats,
                blacklist_chats=blacklist,
                from_users=users
            )
        )
        client.add_event_handler(
            callback=wrapper,
            event=events.MessageEdited(
                pattern=pattern,
                incoming=incoming,
                outgoing=outgoing,
                forwards=forwards,
                chats=chats,
                blacklist_chats=blacklist,
                from_users=users
            )
        )
        return func

    return inner


def run(
        command=None, prefix=prefix, incoming=False, outgoing=True,
        forwards=False, blacklist=None, users=None, chats=None):
    escaped_prefix = re.escape(prefix)
    def inner(func, command=command):
        global HELP_MENU_DATA, HELP_MENU
        wrapper = return_func(func, command, prefix)
        
        if not command:
            command = func.__name__

        try:
            class_name = func.__qualname__.split(".")[-2]
        except:
            class_name = "No Name"
        
        if class_name not in HELP_MENU:
            HELP_MENU = f"{HELP_MENU[:-2]}</i>\n\n<b>⬤ {class_name}:</b>\n"

        try:
            regex_parse = generate(command, command)
            for result in regex_parse:
                HELP_MENU += f"<i>{result}, "
                HELP_MENU_DATA.update({result: func.__doc__})
        except:
            pass

        client.add_event_handler(
            callback=wrapper,
            event=events.NewMessage(
                pattern=escaped_prefix + command + r"($| |\n)",
                incoming=incoming,
                outgoing=outgoing,
                forwards=forwards,
                chats=chats,
                blacklist_chats=blacklist,
                from_users=users
            )
        )
        client.add_event_handler(
            callback=wrapper,
            event=events.MessageEdited(
                pattern=escaped_prefix + command + r"($| .*|\n)",
                incoming=incoming,
                outgoing=outgoing,
                forwards=forwards,
                chats=chats,
                blacklist_chats=blacklist,
                from_users=users
            )
        )

        return func

    return inner

def startup(func):
    func()

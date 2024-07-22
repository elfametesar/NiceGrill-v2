from elfrien.events import NewMessage, MessageEdited, ServiceMessage
from elfrien.types.patched import Message
from nicegrill.__main__ import NiceGrill
from database import blacklist, settings
from traceback import format_exception
from typing import Coroutine, Callable
from elfrien.client import Client

import logging
import asyncio
import exrex
import re

log = logging.getLogger(__name__)

HELP_MENU_CAPTION = "<b>•\tHELP\t•</b>".expandtabs(47)
HELP_MENU = HELP_MENU_CAPTION
HELP_BOOK = "<b>•\tHELP\t•</b>".expandtabs(47)
HELP_BOOK_DATA = {}

bad_chat_list = blacklist.get_all_blacklisted()
prefix = settings.get_prefix()

def update_help_data(function, command: str):
    global HELP_BOOK_DATA, HELP_BOOK

    try:
        class_name = function.__qualname__.split(".")[-2]
    except:
        if not command:
            return

        class_name = "No Name"

    if class_name not in HELP_BOOK:
        HELP_BOOK = f"{HELP_BOOK[:-2]}</i>\n\n<b>⬤ {class_name}:</b>\n"

    try:
        regex_parse = exrex.generate(command, command)
        for result in regex_parse:
            HELP_BOOK += f"<i>{result}, "
            HELP_BOOK_DATA.update({result: function.__doc__})
    except:
        pass


def wrapper(func, name):
    async def inner_content(client: Client, message: Message):
        try:
            if message.chat_id not in bad_chat_list or (message.chat_id in bad_chat_list and message.cmd in ["blacklist", "whitelist"]):
                await asyncio.ensure_future(
                    coro_or_future=func(client, message)
                )

        except Exception as e:
            log.exception(format_exception(e))

            if message.cmd:
                await message.edit("<b>Loading..</b>")
                await message.respond(
                    files="error.txt",
                    message="<b>NiceGrill has crashed. Command was </b>"
                            f"<code>{message.cmd}</code><b>.\n"
                            "Check logs for more information.</b>"
                )

                await message.delete()
                with open('../error.txt', 'w'):
                    pass

    inner_content.__name__ = name
    return inner_content

def on(
    pattern: str,
    prefix: str = prefix or ".",
    incoming: bool = False,
    outgoing: bool = True,
    condition: Callable | Coroutine = None,
    users: list[int] = [],
    chats: list[int] = [],
    blacklist_chats: list[int] = [],
):
    prefix = "^" + re.escape(prefix)
    def inner_function(func):

        update_help_data(
            function=func,
            command=pattern
        )

        func_name = func.__name__
        func = wrapper(func=func, name=func_name)

        nicegrill.client.add_event_handler(
            event=NewMessage(
                prefix=prefix,
                pattern=pattern + r"($| |\n)",
                incoming=incoming,
                outgoing=outgoing,
                users=users,
                chats=chats,
                blacklist_chats=blacklist_chats,
                func=condition
            ),
            callback=func
        )
        nicegrill.client.add_event_handler(
            event=MessageEdited(
                prefix=prefix,
                pattern=pattern + r"($| |\n)",
                incoming=incoming,
                outgoing=outgoing,
                users=users,
                chats=chats,
                blacklist_chats=blacklist_chats,
                func=condition
            ),
            callback=func
        )
        return func

    return inner_function

def on_service(
    condition: Callable | Coroutine = None,
    chats: list[int] = [],
    blacklist_chats: list[int] = [],
):
    def inner_function(func):
        nicegrill.client.add_event_handler(
            event=ServiceMessage(
                chats=chats,
                blacklist_chats=blacklist_chats,
                func=condition
            ),
            callback=func
        )
        return func
    
    return inner_function

def startup(func):
    func()


nicegrill = NiceGrill()
asyncio.run(nicegrill.initialize_bot())
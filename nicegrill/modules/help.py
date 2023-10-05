from nicegrill import Message, run, HELP_MENU, HELP_MENU_DATA, HELP_MENU_CAPTION
from telethon import TelegramClient as Client

import html

class Help:

    @run(command="help")
    async def display_help_menu(message: Message, client: Client):
        if message.args:
            await Help.help_display_command(message, client)
            return
        
        await message.edit(HELP_MENU[:-2] + "</i>")

    async def help_display_command(message: Message, client: Client):
        if message.args in HELP_MENU_DATA:
            if help_info := HELP_MENU_DATA[message.args]:
                await message.edit(
f"""{HELP_MENU_CAPTION}

<b>Class/Command:</b>
<i>{message.args}</i>

<b>Definition:</b>
<i>{html.escape(help_info)}</i>"""
                )
            else:
                await message.edit("<i>No help found for this command</i>")
        else:
            await message.edit(f"<i>Command <u>{message.args}</u> does not exist</i>")

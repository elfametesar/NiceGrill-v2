from telethon.client import TelegramClient
from telethon.sessions import StringSession
from config import API_ID, API_HASH, SESSION, MONGO_URI
from database import settingsdb

import asyncio
import importlib
import glob


async def import_modules():
    for module in glob.glob("modules/*.py"):
        module = module.replace("/", ".")[:-3]
        importlib.import_module(module)
        print(f"Module is loaded: {module.replace('modules.', '').title()}")


async def restart_handler():
    if restart_info := settingsdb.get_restart_details():
        try:
            await client.edit_message(
                entity=restart_info["Chat"],
                text="<i>Restarted</i>",
                message=restart_info["Message"]
            )
        except:
            pass


async def initializer(client: TelegramClient):
    
    await client.connect()

    client.parse_mode = 'html'
    client.ME = await client.get_me()

    await asyncio.gather(
        import_modules(),
        restart_handler()
    )

    print(f"\nLogged in as {client.ME.first_name}\n")
    await client.run_until_disconnected()

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

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

asyncio.run(
    initializer(client)
)


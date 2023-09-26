from telethon.client import TelegramClient
from telethon.sessions import StringSession
from config import API_ID, API_HASH, SESSION, MONGO_URI
from database import settingsdb
from io import StringIO

import asyncio
import importlib
import glob
import sys
import os

preserved_stdout = sys.stdout

def read_stdout():
    output = sys.stdout.getvalue()
    sys.stdout.seek(os.SEEK_END)
    sys.stdout.truncate(0)
    sys.stdout.seek(0)
    return output


def write_stdout(func):
    def inner(args):
        print(args, end="", file=preserved_stdout)
        func(args)
    return inner


async def redirect_pipes():

    sys.stdout = StringIO()
    sys.stdout.read = read_stdout
    sys.stdout.write = write_stdout(sys.stdout.write)
    sys.stderr = sys.stdout

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


async def import_modules():
    for module in glob.glob("modules/*.py"):
        module = module.replace("/", ".")[:-3]

        try:
            importlib.import_module(module)
            print(f"Module is loaded: {module.replace('modules.', '').title()}")
        except Exception as e:
            print(f"\nModule {module.replace('modules.', '')} not loaded: {e}\n", file=sys.stderr)


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


async def initialize_bot(client: TelegramClient):
    
    await client.connect()

    client.parse_mode = 'html'
    client.me = await client.get_me()

    await asyncio.gather(
        import_modules(),
        restart_handler()
    )

    await redirect_pipes()

    print(f"\nLogged in as {client.me.first_name}\n")
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
    initialize_bot(client)
)


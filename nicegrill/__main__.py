from elfrien.types.functions import CreateNewSupergroupChat
from elfrien.utils import async_stdstream
from elfrien.types.patched import Message
from config import API_ID, API_HASH
from elfrien.client import Client
from database import settings

import importlib
import logging
import glob
import sys

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.ERROR)

logging.basicConfig(
    handlers=[logging.FileHandler("error.txt", mode='w+'), stream_handler],
    level=logging.ERROR,
    format='%(asctime)s\n\n%(message)s'
)

log = logging.getLogger(__name__)

class NiceGrill:

    def __init__(
        self,
        api_id: int = API_ID,
        api_hash: str = API_HASH
    ):
        self.client = Client(
            api_id=api_id,
            api_hash=api_hash
        )

    def import_modules(self):
        module_list = glob.glob("nicegrill/modules/*.py")

        for module in module_list:

            module = module.replace("/", ".")[:-3]

            try:
                importlib.import_module(module)
                print(f"Module is loaded: {module.replace('nicegrill.modules.', '').title()}")
            except Exception as e:
                print(f"Module {module.replace('nicegrill.modules.', '').title()} not loaded: {e}")

    async def restart_handler(self):
        if restart_info := settings.get_restart_details():
            try:
                await self.client.load_chats(limit=200)
                await self.client.edit_message(
                    entity=restart_info["Chat"],
                    text="<i>Restarted</i>",
                    message=restart_info["Message"]
                )
            except Exception as e:
                pass

    async def initialize_bot(self):
        await self.client.login()
        self.client.parse_mode = 'HTML'

        if not settings.get_storage_channel():
            created_private_channel = await self.client(
                CreateNewSupergroupChat(
                    title="NiceGrill Storage Database",
                    description="Reserved for bot usage, do not manually edit.",
                    is_channel=True,
                    for_import=False,
                    is_forum=False,
                    message_auto_delete_time=0
                )
            )

            channel_id = created_private_channel.updates[1].channel_id
            settings.set_storage_channel(channel_id)

        self.import_modules()
        await self.restart_handler()

        print(f"\nLogged in as {self.client.me.first_name}")

        sys.stdout = async_stdstream(to_terminal=True)
        sys.stderr = async_stdstream()
        sys.stdin = async_stdstream()

        __builtins__["input"] = sys.stdin.input

        await self.client.run()

#    This file is part of NiceGrill.

#    NiceGrill is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    NiceGrill is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with NiceGrill.  If not, see <https://www.gnu.org/licenses/>.

from nicegrill import Message, on, startup
from database import snippets, settings
from elfrien.client import Client

class Snippets:

    SAVED_SNIPPETS = {}
    IS_OTHERS_ALLOWED = False
    STORAGE_CHANNEL = ""

    @on(pattern="addsnip")
    async def save_a_snip(client: Client, message: Message):

        if message.reply_to_text:

            if message.reply_to_text.media:
                try:
                    fwd_message = await client.forward_to(
                        from_chat=message.chat,
                        to_chat=Snippets.STORAGE_CHANNEL,
                        message_ids=message.reply_to_text.id
                    )
                except Exception as e:
                    await message.edit(f"<i>{e}</i>")
                    return

                snip_text = "media_id=" + str(fwd_message.messages[0].id)
            else:
                snip_text = message.reply_to_text.text

            if not snip_text:
                await message.edit("<i>There is no value to be saved in replied message</i>")
                return

            if message.raw_args:
                snip_name = message.raw_args
            elif " " not in snip_text:
                snip_name = snip_text[:snip_text.find(" ")]
            else:
                await message.edit("<i>You need to give this snippet a name</i>")
                return
        else:
            args = message.raw_args.split(maxsplit=1)

            if len(args) < 2:
                await message.edit("<i>You didn't provide enough arguments</i>")
                return
            
            snip_name, snip_text = args

        snippets.save_snip(
            snippet_name=snip_name,
            snippet_value=snip_text
        )

        Snippets.SAVED_SNIPPETS[snip_name] = snip_text

        await message.edit(f"<i>{snip_name} has been saved into your snippets, you can call it with ${snip_name}</i>")

    @on(pattern="delsnip")
    async def delete_a_snip(client: Client, message: Message):
        if not message.raw_args:
            await message.edit("<i>You need to tell me what snippet to delete</i>")
            return
        
        if message.raw_args not in Snippets.SAVED_SNIPPETS:
            await message.edit("<i>You have no snippet with that name</i>")
            return
        
        if "media_id=" in Snippets.SAVED_SNIPPETS[message.raw_args]:
            await client.delete_messages(
                entity=Snippets.STORAGE_CHANNEL,
                message_ids=[
                    int(Snippets.SAVED_SNIPPETS[message.raw_args][9:])
                ]
            )

        del Snippets.SAVED_SNIPPETS[message.raw_args]

        snippets.delete_data(f"SavedSnippet.{message.raw_args}")

        await message.edit(f"<i>{message.raw_args} has been deleted from your snippet list</i>")

    @on(pattern="snipsforall")
    async def allow_others(client: Client, message: Message):
        snippets.allow_others(not Snippets.IS_OTHERS_ALLOWED)
        Snippets.IS_OTHERS_ALLOWED = not Snippets.IS_OTHERS_ALLOWED

        if Snippets.IS_OTHERS_ALLOWED:
            await message.edit("<i>Your snippets are now open to everyone</i>")
        else:
            await message.edit("<i>Your snippets are now closed to everyone</i>")

    @on(pattern="snips")
    async def list_all_snippets(client: Client, message: Message):
        if not Snippets.SAVED_SNIPPETS:
            await message.edit("<i>You have no saved snippets</i>")
            return
        
        snip_menu = "<b>Snippets: </b>\n\n"

        for snip in Snippets.SAVED_SNIPPETS.keys():
            snip_menu += f"<i> · {snip}\n"
        
        await message.edit(snip_menu + "</i>")

    @on(prefix="", pattern=r"\$.*")
    async def read_snippets(client: Client, message: Message):
        if message.raw_text[1:] in Snippets.SAVED_SNIPPETS:
            snippet = ""
            if message.is_self or Snippets.IS_OTHERS_ALLOWED:
                snippet = Snippets.SAVED_SNIPPETS.get(message.raw_text[1:])
            
            if "media_id=" in snippet:

                try:
                    await client.forward_to(
                        from_chat=Snippets.STORAGE_CHANNEL,
                        to_chat=message.chat,
                        message_ids=[int(snippet[9:])],
                    )
                except Exception:
                    pass
            else:
                await message.respond(snippet)
    
        await message.delete()
    
@startup
def load_from_database():
    Snippets.IS_OTHERS_ALLOWED = snippets.is_others_allowed()
    Snippets.SAVED_SNIPPETS = snippets.get_all_snips()
    Snippets.STORAGE_CHANNEL = settings.get_storage_channel()
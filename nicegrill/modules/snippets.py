from nicegrill import Message, run, event_watcher, startup
from telethon import TelegramClient as Client
from database import snippetsdb


class Snippets:

    SAVED_SNIPPETS = {}
    IS_OTHERS_ALLOWED = False

    @run(command="addsnip")
    async def save_a_snip(message: Message, client: Client):

        if message.is_reply:
            snip_text = message.reply_to_text.text

            if not snip_text:
                await message.edit("<i>There is no value to be saved in replied message</i>")
                return
            
            if message.args:
                snip_name = message.args
            elif " " not in snip_text:
                snip_name = snip_text[:snip_text.find(" ")]
            else:
                await message.edit("<i>You need to give this snippet a name</i>")
                return
        else:
            args = message.args.split(maxsplit=1)

            if len(args) < 2:
                await message.edit("<i>You didn't provide enough arguments</i>")
                return
            
            snip_name, snip_text = args
        
        snippetsdb.save_snip(
            snippet_name=snip_name,
            snippet_value=snip_text
        )

        Snippets.SAVED_SNIPPETS[snip_name] = snip_text

        await message.edit(f"<i>{snip_name} has been saved into your snippets, you can call it with ${snip_name}</i>")

    @run(command="delsnip")
    async def delete_a_snip(message: Message, client: Client):
        if not message.args:
            await message.edit("<i>You need to tell me what snippet to delete</i>")
            return
        
        if message.args not in Snippets.SAVED_SNIPPETS:
            await message.edit("<i>You have no snippet with that name</i>")
            return
        
        del Snippets.SAVED_SNIPPETS[message.args]
        snippetsdb.delete_data(f"SavedSnippet.{message.args}")

        await message.edit(f"<i>{message.args} has been deleted from your snippet list</i>")

    @run(command="snipsforall")
    async def allow_others(message: Message, client: Client):
        snippetsdb.allow_others(not Snippets.IS_OTHERS_ALLOWED)
        Snippets.IS_OTHERS_ALLOWED = not Snippets.IS_OTHERS_ALLOWED

        if Snippets.IS_OTHERS_ALLOWED:
            await message.edit("<i>Your snippets are now open to everyone</i>")
        else:
            await message.edit("<i>Your snippets are now closed to everyone</i>")

    @run(command="snips")
    async def list_all_snippets(message: Message, client: Client):
        if not Snippets.SAVED_SNIPPETS:
            await message.edit("<i>You have no saved snippets</i>")
            return
        
        snip_menu = "<b>Snippets: </b>\n\n"

        for snip in Snippets.SAVED_SNIPPETS.keys():
            snip_menu += f"<i> - {snip}\n"
        
        await message.edit(snip_menu + "</i>")

    @event_watcher(pattern="\\$.*")
    async def read_snippets(message: Message, client: Client):
        if message.raw_text[1:] in Snippets.SAVED_SNIPPETS:
            if message.sender_id == client.me.id:
                await message.edit(
                    Snippets.SAVED_SNIPPETS.get(message.raw_text[1:])
                )
            elif Snippets.IS_OTHERS_ALLOWED:
                await message.reply(
                    Snippets.SAVED_SNIPPETS.get(message.raw_text[1:])
                )
    
@startup
def load_from_database():
    Snippets.IS_OTHERS_ALLOWED = snippetsdb.is_others_allowed()
    Snippets.SAVED_SNIPPETS = snippetsdb.get_all_snips()
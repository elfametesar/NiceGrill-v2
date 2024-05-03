from nicegrill import Message, run, event_watcher, startup
from telethon import TelegramClient as Client
from database import snippetsdb, settingsdb


class Snippets:

    SAVED_SNIPPETS = {}
    IS_OTHERS_ALLOWED = False
    STORAGE_CHANNEL = ""

    @run(command="addsnip")
    async def save_a_snip(message: Message, client: Client):

        if message.is_reply:

            if message.reply_to_text.media:
                try:
                    fwd_message = await message.reply_to_text.forward_to(
                        entity=Snippets.STORAGE_CHANNEL,
                        messages=message.reply_to_text
                    )
                except Exception:
                    await message.edit("<i>Storage database could not be retrieved. Try again</i>")
                    return

                snip_text = "media_id=" + str(fwd_message.id)
            else:
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
        
        if "media_id=" in Snippets.SAVED_SNIPPETS[message.args]:
            await client.delete_messages(
                entity=Snippets.STORAGE_CHANNEL,
                message_ids=[
                    Snippets.SAVED_SNIPPETS[message.args][9:]
                ]
            )

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
            snip_menu += f"<i> · {snip}\n"
        
        await message.edit(snip_menu + "</i>")

    @event_watcher(pattern="\\$.*")
    async def read_snippets(message: Message, client: Client):
        if message.raw_text[1:] in Snippets.SAVED_SNIPPETS:
            snippet = ""
            if message.sender_id == client.me.id or Snippets.IS_OTHERS_ALLOWED:
                snippet = Snippets.SAVED_SNIPPETS.get(message.raw_text[1:])
            
            await message.delete()
            if "media_id=" in snippet:
                print(snippet[9:])
                message_list = await client.get_messages(
                    entity=Snippets.STORAGE_CHANNEL,
                    ids=[int(snippet[9:])]
                )
                try:
                    await message.respond(
                        message_list[0]
                    )
                except Exception:
                    pass
            else:
                await message.respond(snippet)
    
@startup
def load_from_database():
    Snippets.IS_OTHERS_ALLOWED = snippetsdb.is_others_allowed()
    Snippets.SAVED_SNIPPETS = snippetsdb.get_all_snips()
    Snippets.STORAGE_CHANNEL = settingsdb.get_storage_channel()
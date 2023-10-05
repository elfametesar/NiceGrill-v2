from telethon import TelegramClient as Client
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
from telethon.errors.rpcerrorlist import UserAdminInvalidError, UserIdInvalidError, ChatAdminRequiredError, ParticipantIdInvalidError, MessageIdInvalidError
from nicegrill import Message, run
from nicegrill.utils import get_user

class Admin:

    BAN = ChatBannedRights(
        until_date=None,
        view_messages=True,
        send_messages=True,
        send_media=True,
        send_stickers=True,
        send_gifs=True,
        send_games=True,
        send_inline=True,
        embed_links=True
    )

    UNBAN = ChatBannedRights(
        until_date=None,
        send_messages=None,
        send_media=None,
        send_stickers=None,
        send_gifs=None,
        send_games=None,
        send_inline=None,
        embed_links=None
    )
    
    @run(command="(ban|dban|unban)")
    async def ban_user(message: Message, client: Client):
        user = message.args
        
        if message.is_reply:
            user = message.reply_to_text.from_user
        else:
            if not user:
                await message.edit(f"<i>Who do you want to {message.cmd}?</i>")
                return
            
            user = await get_user(user=message.args, client=client)

        if not user:
            await message.edit("<i>Cannot find this user</i>")
            return

        try:
            await message.client(
                EditBannedRequest(
                    channel=message.chat,
                    participant=user,
                    banned_rights=Admin.BAN if message.cmd == "ban" else Admin.UNBAN,
                )
            )
            await message.edit(f"<i>{message.cmd.title()}ned {user.first_name}</i>")
        except TypeError:
            await message.edit("<i>You need to be in a chat to do this</i>")
        except UserAdminInvalidError:
            await message.edit("<i>You're either not an admin or that's more admin than you</i>")
        except (UserIdInvalidError, ParticipantIdInvalidError):
            await message.edit("<i>Specified user is a no go</i>")
        except ChatAdminRequiredError:
            await message.edit(f"<i>Oh honey, I'm not admin enough to {message.cmd} this user</i>")
        
        if message.cmd == "dban":
            await message.delete()

    @run(command="kick")
    async def kick_user(message: Message, client: Client):
        user = message.args
        
        if message.is_reply:
            user = message.reply_to_text.from_user
        else:
            if not user:
                await message.edit("<i>Who do you want to kick?</i>")
                return
            
            user = await get_user(user=message.args, client=client)

        if not user:
            await message.edit("<i>Cannot find this user</i>")
            return

        try:
            await client.kick_participant(
                entity=message.chat,
                user=user
            )
            await message.edit(f"<i>Kicked {user.first_name}</i>")
        except TypeError:
            await message.edit("<i>You need to be in a chat to do this</i>")
            return
        except UserAdminInvalidError:
            await message.edit("<i>You're either not an admin or that's more admin than you</i>")
        except (UserIdInvalidError, ParticipantIdInvalidError):
            await message.edit("<i>Specified user is a no go</i>")
        except ChatAdminRequiredError:
            await message.edit("<i>Oh honey, I'm not admin enough to kick this user</i>")

    @run(command="(mute|unmute)")
    async def mute_user(message: Message, client: Client):
        user = message.args

        if message.is_reply:
            user = message.reply_to_text.from_user
        else:
            if not user:
                await message.edit(f"<i>Who do you want to {message.cmd}?</i>")
                return

            user = await get_user(user=message.args, client=client)

        if not user:
            await message.edit("<i>Cannot find this user</i>")
            return

        try:
            await client(
                EditBannedRequest(
                    channel=await client.get_input_entity(message.chat_id),
                    participant=user,
                    banned_rights=ChatBannedRights(
                        until_date=366,
                        send_messages=True if message.cmd == "mute" else False
                    )
                )
            )
            await message.edit(f"<i>{message.cmd.title()}d {user.first_name}</i>")
        except TypeError as e:
            await message.edit("<i>You need to be in a chat to do this</i>")
        except UserAdminInvalidError:
            await message.edit("<i>You're either not an admin or that's more admin than you</i>")
        except (UserIdInvalidError, ParticipantIdInvalidError):
            await message.edit("<i>Specified user is a no go</i>")
        except ChatAdminRequiredError:
            await message.edit(f"<i>Oh honey, I'm not admin enough to {message.cmd} this user</i>")

    @run(command="(pin|lpin|unpin)")
    async def pin_message(message: Message, client: Client):
        if not message.is_reply:
            await message.respond(f"<i>You need to reply to a message to {message.cmd} it</i>")
            return

        try:
            if message.cmd == "unpin":
                await message.reply_to_text.unpin()
            else:
                await message.reply_to_text.pin(
                    notify=True if message.cmd == "lpin" else False
                )
        except MessageIdInvalidError:
            await message.edit(f"<i>This message cannot be {message.cmd}ned</i>")
            return

        await message.delete()
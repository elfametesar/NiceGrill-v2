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

from elfrien.types.errors.variants import (
    UserAdminInvalidError, InvalidUserId,
    InsufficientPermissions, UserNotParticipant,
    InvalidMessageType, InvalidChatType
)
from elfrien.types.tl import (
    ChatMemberStatusMember, ChatMemberStatusAdministrator,
    ChatAdministratorRights, MessageSenderUser
)
from elfrien.types.functions import SetChatMemberStatus
from elfrien.types.errors.base import NotFoundError
from nicegrill.utils import get_user, parse_kwargs
from nicegrill import Message, on
from elfrien.client import Client

class Admin:
    
    @on(pattern="(ban|dban|unban)")
    async def ban_user(client: Client, message: Message):
        user = message.raw_args
        
        if message.reply_to_text:
            user = message.reply_to_text.sender
        else:
            if not user:
                await message.edit(f"<i>Who do you want to {message.cmd}?</i>")
                return
            
            user = await get_user(user=message.raw_args, client=client)

        if not user:
            await message.edit("<i>Cannot find this user</i>")
            return

        if message.cmd == "dban":
            await message.delete()

        try:
            await client.ban_participant(
                entity=message.chat,
                user=user
            ) if message.cmd in ["ban", "dban"] else (
                await client.unban_participant(
                    entity=message.chat,
                    user=user
                )
            )
            await message.edit(f"<i>{message.cmd.title()}ned {user.name}</i>")
        except (TypeError, ValueError):
            await message.edit("<i>You need to be in a chat to do this</i>")
        except InvalidChatType as e:
            await message.edit(f"<i>{e}</i>")
        except (InvalidUserId, UserNotParticipant):
            await message.edit("<i>Specified user is a no go</i>")
        except (InsufficientPermissions,UserAdminInvalidError):
            await message.edit(f"<i>Oh honey, I'm not admin enough to {message.cmd} this user</i>")

    @on(pattern="promote")
    async def promote_user(client: Client, message: Message):
        """
        is_anonymous=False,
        can_delete_stories=True,
        can_edit_stories=True,
        can_post_stories=True,
        can_manage_video_chats=True,
        can_promote_members=True,
        can_manage_topics=True,
        can_pin_messages=True,
        can_restrict_members=True,
        can_invite_users=True,
        can_delete_messages=True,
        can_edit_messages=True,
        can_post_messages=True,
        can_change_info=True,
        can_manage_chat=True

        You can set any of these permissions by simply adding to the command as example below:

            .promote <user> can_delete_messages=False

        By default, all set to True except is_anonymous
        """
        user = message.raw_args

        message.raw_args, kwargs = parse_kwargs(
            command=message.raw_args,
            defaults={
                "is_anonymous": True,
                "can_delete_stories": True,
                "can_edit_stories": True,
                "can_post_stories": True,
                "can_manage_video_chats": True,
                "can_promote_members": True,
                "can_manage_topics": True,
                "can_pin_messages": True,
                "can_restrict_members": True,
                "can_invite_users": True,
                "can_delete_messages": True,
                "can_edit_messages": True,
                "can_post_messages": True,
                "can_change_info": True,
                "can_manage_chat": True,
            }
        )

        custom_title = kwargs.pop("title", "Admin")
        if message.reply_to_text:
            user = message.reply_to_text.sender
        else:
            if not user:
                await message.edit("<i>Who do you want to kick?</i>")
                return

            user = await get_user(user=message.raw_args, client=client)

        if not user:
            await message.edit("<i>Cannot find this user</i>")
            return

        try:
            await client(
                SetChatMemberStatus(
                    chat_id=message.chat_id,
                    member_id=MessageSenderUser(user.id),
                    status=ChatMemberStatusAdministrator(
                        rights=ChatAdministratorRights(
                            **kwargs
                        ),
                        custom_title=custom_title,
                        can_be_edited=False
                    )
                )
            )
            await message.edit(f"<i>Promoted {user.name}</i>")
        except (TypeError, ValueError):
            await message.edit("<i>You need to be in a chat to do this</i>")
        except InvalidUserId:
            await message.edit("<i>Specified user is a no go</i>")
        except (InsufficientPermissions,UserAdminInvalidError):
            await message.edit(f"<i>Oh honey, I'm not admin enough to {message.cmd} this user</i>")

    @on(pattern="demote")
    async def demote_user(client: Client, message: Message):
        user = message.raw_args

        if message.reply_to_text:
            user = message.reply_to_text.sender
        else:
            if not user:
                await message.edit("<i>Who do you want to kick?</i>")
                return

            user = await get_user(user=message.raw_args, client=client)

        if not user:
            await message.edit("<i>Cannot find this user</i>")
            return

        try:
            await client(
                SetChatMemberStatus(
                    chat_id=message.chat_id,
                    member_id=MessageSenderUser(user.id),
                    status=ChatMemberStatusMember()
                )
            )
            await message.edit(f"<i>Demoted {user.name}</i>")
        except (TypeError, ValueError):
            await message.edit("<i>You need to be in a chat to do this</i>")
        except InvalidUserId:
            await message.edit("<i>Specified user is a no go</i>")
        except (InsufficientPermissions,UserAdminInvalidError):
            await message.edit(f"<i>Oh honey, I'm not admin enough to {message.cmd} this user</i>")

    @on(pattern="kick")
    async def kick_user(client: Client, message: Message):
        user = message.raw_args
        
        if message.reply_to_text:
            user = message.reply_to_text.sender
        else:
            if not user:
                await message.edit("<i>Who do you want to kick?</i>")
                return

            user = await get_user(user=message.raw_args, client=client)

        if not user:
            await message.edit("<i>Cannot find this user</i>")
            return

        try:
            await client.kick_participant(
                entity=message.chat,
                user=user
            )
            await message.edit(f"<i>Kicked {user.name}</i>")
        except (TypeError, ValueError):
            await message.edit("<i>You need to be in a chat to do this</i>")
        except InvalidUserId:
            await message.edit("<i>Specified user is a no go</i>")
        except (InsufficientPermissions,UserAdminInvalidError):
            await message.edit(f"<i>Oh honey, I'm not admin enough to {message.cmd} this user</i>")

    @on(pattern="(mute|unmute)")
    async def mute_user(client: Client, message: Message):
        user = message.raw_args

        if message.reply_to_text:
            user = message.reply_to_text.sender
        else:
            if not user:
                await message.edit(f"<i>Who do you want to {message.cmd}?</i>")
                return

            user = await get_user(user=message.raw_args, client=client)

        if not user:
            await message.edit("<i>Cannot find this user</i>")
            return

        try:
            await client.mute_user(
                entity=message.chat,
                user=user
            ) if message.cmd == "mute" else (
                await client.unmute_user(
                    entity=message.chat,
                    user=user
                )
            )
            await message.edit(f"<i>{message.cmd.title()}d {user.name}</i>")
        except (TypeError, ValueError):
            await message.edit("<i>You need to be in a chat to do this</i>")
        except (InvalidUserId, UserNotParticipant):
            await message.edit("<i>Specified user is a no go</i>")
        except (InsufficientPermissions,UserAdminInvalidError):
            await message.edit(f"<i>Oh honey, I'm not admin enough to {message.cmd} this user</i>")

    @on(pattern="(pin|lpin|unpin)")
    async def pin_message(client: Client, message: Message):
        if not message.reply_to_text:
            await message.respond(f"<i>You need to reply to a message to {message.cmd} it</i>")
            return

        try:
            if message.cmd == "unpin":
                await message.reply_to_text.unpin()
            else:
                await message.reply_to_text.pin(
                    notify_all=True if message.cmd == "lpin" else False
                )
            
            await message.delete()
        except (InvalidMessageType, NotFoundError):
            await message.edit(f"<i>This message cannot be {message.cmd}ned</i>")
            return

        await message.delete()
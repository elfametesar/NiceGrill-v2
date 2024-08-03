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

from nicegrill.events import AndEvent, UserChatEvent, RealUserEvent
from elfrien.types.patched import Message
from nicegrill import on, startup
from elfrien.client import Client
from database import antipm


class AntiPM:

    PM_BLOCKER = False
    WARNING_LIMIT = 3
    NOTIFICATIONS = True
    SUPER_BLOCK = False
    APPROVED_USERS = []

    WARNS = {}
    WARNING_MESSAGE = (
        ""
        "<b>I have not allowed you to PM, please ask or say whatever"
        " it is in a group chat.\n\n"
        "I'm letting you off the hook for this time but be warned that "
        "you will be blocked if you continue sending messages.</b>"
    )

    BLOCK_MESSAGE = (
        "<b>I have warned you, however, you did not stop "
        "spamming my chat. Therefore, you have been blocked, good luck!</b>"
    )

    @on(pattern="antipm")
    async def antipm_switch(client: Client, message: Message):
        antipm.set_antipm(not AntiPM.PM_BLOCKER)
        AntiPM.PM_BLOCKER = not AntiPM.PM_BLOCKER

        antipm.set_antipm(AntiPM.PM_BLOCKER)
        await message.edit(f"<i>AntiPM has been set to {AntiPM.PM_BLOCKER}</i>")

    @on(pattern="bless")
    async def approve_user(client: Client, message: Message):
        """Allows that person to PM you, you can either reply to user,
        type their username or use this in their chat"""
        if not (user := await AntiPM.get_user(client, message)):
            await message.edit("<i>You need to input a valid user id</i>")
            return

        if user.id == client.me.id:
            await message.edit(
                "<i>Why would you wanna bless yourself? "
                "Rhetorical question: Because you're an approval whore</i>"
            )
            return

        if user.id in AntiPM.APPROVED_USERS:
            await message.edit("<i>User is already blessed</i>")
        else:
            AntiPM.APPROVED_USERS.append(user.id)
            antipm.approve_user(user.id)

            await message.edit(
                f"<i>Blessed <a href=tg://user?id={user.id}><i>{user.name}</a>, they can PM you now</i>"
            )

    @on(pattern="curse")
    async def disapprove_user(client: Client, message: Message):
        """Prevents that person to PM you, you can either reply to user,
        type their username or use this in their chat"""
        if not (user := await AntiPM.get_user(client, message)):
            await message.edit("<i>You need to input a valid user id</i>")
            return

        if user.id == client.me.id:
            await message.edit(
                "<i>Why would you wanna curse yourself? "
                "Rhetorical question: Because you're a disappointment to everyone</i>"
            )
            return

        if user.id not in AntiPM.APPROVED_USERS:
            await message.edit("<i>User is already cursed</i>")
        else:
            AntiPM.APPROVED_USERS.remove(user.id)
            antipm.disapprove_user(user.id)

            await message.edit(
                f"<i>Cursed <a href=tg://user?id={user.id}><i>{user.name}</a>, they cannot PM you anymore</i>"
            )

    @on(pattern="block")
    async def block_user(client: Client, message: Message):
        """Simply blocks the person.. duh!!"""
        if not (user := await AntiPM.get_user(client, message)):
            await message.edit("<i>No user found</i>")
            return

        if user.id == client.me.id:
            await message.edit(
                "<i>Why would you wanna block yourself? "
                "Do you really hate yourself that much?</i>"
            )
            return

        await client.block_user(user=user.id)

        if user.id in AntiPM.APPROVED_USERS:
            AntiPM.APPROVED_USERS.remove(user.id)
            antipm.disapprove_user(AntiPM.APPROVED_USERS)

        await message.edit(
            f"<a href=tg://user?id={user.id}><i>{user.name}</a> has been blocked</i>"
        )

    @on(pattern="unblock")
    async def unblock_user(client: Client, message: Message):
        """Simply blocks the person..duh!!"""
        if not (user := await AntiPM.get_user(client, message)):
            await message.edit("<i>No user found</i>")
            return

        if user.id == client.me.id:
            await message.edit(
                "<i>Why would you use unblock on yourself? "
                "Are you having a mental spasm?</i>"
            )
            return

        await client.unblock_user(user=user)

        await message.edit(
            f"<a href=tg://user?id={user.id}><i>{user.name}</a> has been unblocked</i>"
        )

    async def get_user(client: Client, message: Message):
        user = message.args

        if user.isdigit():
            user = int(user)

        if message.reply_to_text:
            user = message.reply_to_text.sender_id

        if not user:
            user = await message.get_chat()
            if hasattr(user, "first_name"):
                return user

            return False

        try:
            user = await client.get_entity(user)

            if not hasattr(user, "first_name"):
                raise Exception
            else:
                return user
        except Exception as e:
            print(e)
            return False

    @on(pattern="notif")
    async def notifications_for_pms(client: Client, message: Message):
        """Ah this one again...It turns on/off tag notification
        sounds from unwanted PMs. It auto-sends a
        a message in your name until that user gets blocked or approved"""
        antipm.set_notifications(not AntiPM.NOTIFICATIONS)
        AntiPM.NOTIFICATIONS = not AntiPM.NOTIFICATIONS

        if AntiPM.NOTIFICATIONS:
            await message.edit("<i>Notifications from cursed PMs unmuted</i>")
        else:
            await message.edit("<i>Notifications from cursed PMs muted</i>")

    @on(pattern="setlimit")
    async def set_warning_limit(client: Client, message: Message):
        """This one sets a max. message limit for unwanted
        PMs and when they go beyond it, bamm!"""
        if not message.args.isdigit():
            await message.edit("<i>Limit value has to be a number</i>")
            return
        else:
            AntiPM.WARNING_LIMIT = max(1, int(message.args))
            antipm.set_warning_limit(AntiPM.WARNING_LIMIT)
            await message.edit("<i>Max. PM message limit successfully updated</i>")

    @on(pattern="sblock")
    async def super_block(client: Client, message: Message):
        """If unwanted users spams your chat, the chat
        will be deleted when the idiot passes the message limit"""
        antipm.set_superblock(not AntiPM.SUPER_BLOCK)
        AntiPM.SUPER_BLOCK = not AntiPM.SUPER_BLOCK

        if AntiPM.SUPER_BLOCK:
            await message.edit("<i>Chats from cursed parties will be removed</i>")
        else:
            await message.edit(
                "<i>Chats from cursed parties will not be removed anymore</i>"
            )

    @on(
        prefix="",
        pattern=".*",
        condition=AndEvent(UserChatEvent, RealUserEvent),
        incoming=True,
        outgoing=False,
    )
    async def check_personal_messages(client: Client, message: Message):
        if AntiPM.PM_BLOCKER:
            if message.chat.id in AntiPM.APPROVED_USERS:
                return

            if not AntiPM.NOTIFICATIONS:
                await message.mark_read()

            if message.chat.id in AntiPM.WARNS:
                AntiPM.WARNS[message.chat.id] += 1
                async for message in client.iter_messages(
                    entity=message.chat,
                    from_user=client.me,
                    query="have not allowed you to PM, please ask or say whatever it is in a group chat",
                    limit=1,
                ):
                    await message.delete()
            else:
                AntiPM.WARNS[message.chat.id] = 1

            await message.reply(AntiPM.WARNING_MESSAGE)
            if AntiPM.WARNS[message.chat.id] == AntiPM.WARNING_LIMIT:
                AntiPM.WARNS[message.chat.id] = 0

                await message.reply(AntiPM.BLOCK_MESSAGE)
                await client.block_user(user=message.chat)

            if AntiPM.SUPER_BLOCK:
                await client.delete_chat(entity=message.chat)


@startup
def load_from_database():
    AntiPM.PM_BLOCKER = antipm.is_antipm()
    AntiPM.WARNING_LIMIT = antipm.get_warning_limit()
    AntiPM.NOTIFICATIONS = antipm.is_notifications()
    AntiPM.APPROVED_USERS = antipm.get_all_approved()
    AntiPM.SUPER_BLOCK = antipm.is_superblock()

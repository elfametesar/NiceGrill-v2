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


from telethon import functions, TelegramClient as Client

from main import Message, run, event_watcher, startup
from database import antipmdb


class AntiPM:
    PM_BLOCKER = False
    WARNING_LIMIT = 3
    NOTIFICATIONS = True
    SUPER_BLOCK = False
    APPROVED_USERS = []

    WARNS = {}
    WARNING_MESSAGE = "" \
                      "<b>I have not allowed you to PM, please ask or say whatever" \
                      " it is in a group chat or at least ask for my permission to PM\n\n" \
                      "I'm letting you off the hook for this time but be warned that " \
                      "you will be blocked & reported spam if you continue.</b>"

    BLOCK_MESSAGE = \
        "<b>I have warned you several times now. However, you did not stop " \
        "spamming my chat. Therefore, you have been blocked and reported " \
        "as spam. Good luck!</b>"


    @run(command="antipm")
    async def antipm_switch(message: Message, client: Client):
        antipmdb.set_antipm(not AntiPM.PM_BLOCKER)
        AntiPM.PM_BLOCKER = not AntiPM.PM_BLOCKER

        antipmdb.set_antipm(AntiPM.PM_BLOCKER)
        await message.edit(f"<i>AntiPM has been set to {AntiPM.PM_BLOCKER}</i>")


    @run(command="approve")
    async def approve_user(message: Message, client: Client):
        """Allows that person to PM you, you can either reply to user,
type their username or use this in their chat"""
        if not (user := await AntiPM.get_user(message, client)):
            await message.edit("<i>You need to input a valid user id</i>")
            return

        if user.id == client.me.id:
            await message.edit(
                "<i>Why would you wanna approve yourself? "
                "Rhetorical question: Because you're an approval whore</i>"
            )
            return

        if user.id in AntiPM.APPROVED_USERS:
            await message.edit("<i>User is already approved</i>")
        else:
            AntiPM.APPROVED_USERS.append(user.id)
            antipmdb.approve_user(user.id)

            await message.edit(
                f"<a href=tg://user?id={user.id}><i>{user.first_name}</a> is approved to PM you now</i>")


    @run(command="disapprove")
    async def disapprove_user(message: Message, client: Client):
        """Prevents that person to PM you, you can either reply to user,
type their username or use this in their chat"""
        if not (user := await AntiPM.get_user(message, client)):
            await message.edit("<i>You need to input a valid user id</i>")
            return

        if user.id == client.me.id:
            await message.edit(
                "<i>Why would you wanna disapprove yourself? "
                "Rhetorical question: Because you're a disappointment to everyone</i>"
            )
            return

        if user.id not in AntiPM.APPROVED_USERS:
            await message.edit("<i>User is already disapproved</i>")
        else:
            AntiPM.APPROVED_USERS.remove(user.id)
            antipmdb.disapprove_user(user.id)

            await message.edit(
                f"<a href=tg://user?id={user.id}><i>{user.first_name}</a> is disapproved to PM you</i>")


    @run(command="block")
    async def block_user(message: Message, client: Client):
        """Simply blocks the person.. duh!!"""
        if not (user := await AntiPM.get_user(message, client)):
            await message.edit("<i>No user found</i>")
            return

        if user.id == client.me.id:
            await message.edit(
                "<i>Why would you wanna block yourself? "
                "Do you really hate yourself that much?</i>"
            )
            return

        await client(functions.contacts.BlockRequest(id=user.id))

        if user.id in AntiPM.APPROVED_USERS:
            AntiPM.APPROVED_USERS.remove(user.id)
            antipmdb.disapprove_user(AntiPM.APPROVED_USERS)

        await message.edit(
            f"<a href=tg://user?id={user.id}><i>{user.first_name}</a> has been blocked</i>"
        )


    @run(command="unblock")
    async def unblock_user(message: Message, client: Client):
        """Simply blocks the person..duh!!"""
        if not (user := await AntiPM.get_user(message, client)):
            await message.edit("<i>No user found</i>")
            return

        if user.id == client.me.id:
            await message.edit(
                "<i>Why would you use unblock on yourself? "
                "Are you having a mental spasm?</i>"
            )
            return

        await message.client(functions.contacts.UnblockRequest(id=user.id))

        await message.edit(
            f"<a href=tg://user?id={user.id}><i>{user.first_name}</a> has been unblocked</i>"
        )


    async def get_user(message: Message, client: Client):
        user = message.args

        if user.isdigit():
            user = int(user)

        if message.is_reply:
            user = message.reply_to_message.sender_id

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

    @run(command="notif")
    async def notifications_for_pms(message: Message, client: Client):
        """Ah this one again...It turns on/off tag notification
sounds from unwanted PMs. It auto-sends a
a message in your name until that user gets blocked or approved"""
        antipmdb.set_notifications(not AntiPM.NOTIFICATIONS)
        AntiPM.NOTIFICATIONS = not AntiPM.NOTIFICATIONS

        if AntiPM.NOTIFICATIONS:
            await message.edit("<i>Notifications from unapproved PMs unmuted</i>")
        else:
            await message.edit("<i>Notifications from unapproved PMs muted</i>")


    @run(command="setlimit")
    async def set_warning_limit(message: Message, client: Client):
        """This one sets a max. message limit for unwanted
PMs and when they go beyond it, bamm!"""
        if not message.args.isdigit():
            await message.edit("<i>Limit value has to be a number</i>")
            return
        else:
            AntiPM.WARNING_LIMIT = max(1, int(message.args))
            antipmdb.set_warning_limit(AntiPM.WARNING_LIMIT)
            await message.edit("<i>Max. PM message limit successfully updated</i>")


    @run(command="sblock")
    async def super_block(message: Message, client: Client):
        """If unwanted users spams your chat, the chat
will be deleted when the idiot passes the message limit"""
        antipmdb.set_superblock(not AntiPM.SUPER_BLOCK)
        AntiPM.SUPER_BLOCK = not AntiPM.SUPER_BLOCK

        if AntiPM.SUPER_BLOCK:
            await message.edit("<i>Chats from unapproved parties will be removed</i>")
        else:
            await message.edit("<i>Chats from unapproved parties will not be removed anymore</i>")


    @event_watcher()
    async def check_personal_messages(message: Message, client: Client):
        if message.sender_id == client.me.id:
            return

        if message.is_private and AntiPM.PM_BLOCKER:
            user = await message.get_chat()

            if user.id in AntiPM.APPROVED_USERS:
                return

            if user.bot:
                return

            if not AntiPM.NOTIFICATIONS:
                await client.send_read_acknowledge(user)

            
            if user.id in AntiPM.WARNS:
                AntiPM.WARNS[user.id] += 1
                async for message in client.iter_messages(
                    entity=user,
                    from_user=client.me,
                    search="have not allowed you to PM, please ask or say whatever it is in a group chat",
                    limit=1
                ):
                    await message.delete()
            else:
                AntiPM.WARNS[user.id] = 1

            await message.reply(AntiPM.WARNING_MESSAGE)
            if AntiPM.WARNS[user.id] == AntiPM.WARNING_LIMIT:
                AntiPM.WARNS[user.id] = 0

                await message.reply(AntiPM.BLOCK_MESSAGE)

                await message.client(functions.messages.ReportSpamRequest(peer=user))
                await message.client(functions.contacts.BlockRequest(id=user))

            if AntiPM.SUPER_BLOCK:
                await client.delete_dialog(entity=user, revoke=True)


@startup
def load_from_database():
    AntiPM.PM_BLOCKER = antipmdb.is_antipm()
    AntiPM.WARNING_LIMIT = antipmdb.get_warning_limit()
    AntiPM.NOTIFICATIONS = antipmdb.is_notifications()
    AntiPM.APPROVED_USERS = antipmdb.get_all_approved()
    AntiPM.SUPER_BLOCK = antipmdb.is_superblock()

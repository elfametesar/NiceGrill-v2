from elfrien.types.patched import MessageChatAddMembers
from nicegrill import Message

TextEvent = lambda client, message: message.raw_text
MediaEvent = lambda client, message: message.media
PhotoEvent = lambda client, message: message.photo
VideoEvent = lambda client, message: message.video
VideoNoteEvent = lambda client, message: message.video_note
GifEvent = lambda client, message: message.gif
VoiceEvent = lambda client, message: message.voice_note
AudioEvent = lambda client, message: message.audio
DocumentEvent = lambda client, message: message.document
DiceEvent = lambda client, message: message.dice
PollEvent = lambda client, message: message.poll
ReplyEvent = lambda client, message: message.reply_to_text

PrivateChatEvent = lambda client, message: message.is_private
UserChatEvent = lambda client, message: message.is_private and not message.is_self
GroupChatEvent = lambda client, message: message.is_group
ChannelEvent = lambda client, message: message.is_channel
RealUserEvent = lambda client, message: (
    getattr(message.sender, "type", False) != "bot" and not message.is_self
)
BotEvent = lambda client, message: getattr(message.chat, "bot", False)
ChatJoinEvent = lambda client, message: isinstance(
    message.service, MessageChatAddMembers
)


def AndEvent(*args):
    def call_events(client, message: Message):
        return all(lambda_expr(client, message) for lambda_expr in args)

    return call_events


def OrEvent(*args):
    def call_events(client, message: Message):
        return any(lambda_expr(client, message) for lambda_expr in args)

    return call_events

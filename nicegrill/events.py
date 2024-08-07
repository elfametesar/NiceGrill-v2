from nicegrill import Message, nicegrill

TextEvent = lambda message: message.message.message
MediaEvent = lambda message: message.media
PhotoEvent = lambda message: message.photo
VideoEvent = lambda message: message.video
VideoNoteEvent = lambda message: message.video_note
GifEvent = lambda message: message.gif
VoiceEvent = lambda message: message.voice
AudioEvent = lambda message: message.audio
DocumentEvent = lambda message: message.document
DiceEvent = lambda message: message.dice
PollEvent = lambda message: message.poll
ReplyEvent = lambda message: message.is_reply

PrivateChatEvent = lambda message: message.is_private
UserChatEvent = lambda message: message.is_private and message.chat_id != nicegrill.client.me.id
GroupChatEvent = lambda message: message.is_group
ChannelEvent = lambda message: message.is_channel
RealUserEvent = lambda message: (
    hasattr(message.sender, "bot") and not message.sender.bot and message.sender.id != nicegrill.client.me.id
)
BotEvent = lambda message: getattr(message.sender, "bot", False)
ChatJoinEvent = lambda message: message.user_joined

def AndEvent(*args):
    def call_events(message: Message):
        return all(lambda_expr(message) for lambda_expr in args)

    return call_events

def OrEvent(*args):
    def call_events(message: Message):
        return any(lambda_expr(message) for lambda_expr in args)

    return call_events

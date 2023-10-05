from nicegrill import Message

TextEvent = lambda message: message.raw_text
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

PrivateChatEvent = lambda message: getattr(message, "is_private")
UserChatEvent = lambda message: getattr(message, "is_private", False) and getattr(message.sender, "is_self", False)
GroupChatEvent = lambda message: getattr(message, "is_group", False)
ChannelEvent = lambda message: getattr(message, "is_channel", False)
RealUserEvent = lambda message: not getattr(message.sender, "bot", False)
BotEvent = lambda message: getattr(message.sender, "bot", False)

def AndEvent(*args):
    def call_events(message: Message):
        return all(lambda_expr(message) for lambda_expr in args)

    return call_events

def OrEvent(*args):
    def call_events(message: Message):
        return any(lambda_expr(message) for lambda_expr in args)

    return call_events

from telethon.sync import TelegramClient
from telethon.sessions import StringSession


API_ID = input("Enter your API ID:")
API_HASH = input("Enter your API HASH:")

if not API_ID or not API_HASH:
    print("You haven't passed in the required information.")
    exit(1)

if not API_ID.isdigit():
    print("API ID has to be a numeric value")
    exit(1)

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    string = client.session.save()
    print("Save this string session somewhere secure and use it any time. Do not share it")
    print(string)
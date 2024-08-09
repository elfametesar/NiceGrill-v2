from elfrien.types.patched import Message
from elfrien.client import Client
from bs4 import BeautifulSoup
from nicegrill import on
from httpx import get

import re

DEVICES_DATA_URL = (
    "https://raw.githubusercontent.com/androidtrackers/"
    "certified-android-devices/master/by_model.json"
)

MAGISK_URLS = {
    "Stable": "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/stable.json",
    "Beta": "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/beta.json",
    "Canary": "https://raw.githubusercontent.com/topjohnwu/magisk-files/master/canary.json",
}


class Android:

    @on(pattern="magisk")
    async def get_magisk(client: Client, message: Message):
        """Fetch latest Magisk releases."""
        releases = "<b>Latest Magisk Releases:</b>\n\n"
        for name, url in MAGISK_URLS.items():
            data = get(url).json()
            version = data["magisk"]["version"]
            download_link = data["magisk"]["link"]
            releases += f"{name}: <a href='{download_link}'>v{version}</a>\n"

        await message.edit(releases)

    @on(pattern="device")
    async def get_device_info(client: Client, message: Message):
        """Retrieve basic Android device info by codename or model."""
        query = message.raw_args or (message.reply_to_text.text if message.reply_to_text else None)

        if not query:
            await message.edit("<code>Usage: .device -codename- / -model-</code>")
            return

        devices = get(DEVICES_DATA_URL).json()
        found_devices = [device for device in devices if device["device"] == query or device["model"] == query]

        if found_devices:
            reply = f"Search results for {query}:\n\n"
            for device in found_devices:
                reply += (
                    f"{device['brand']} {device['name']}\n"
                    f"<b>Codename</b>: <code>{device['device']}</code>\n"
                    f"<b>Model</b>: {device['model']}\n\n"
                )
        else:
            reply = f"<code>Couldn't find info about {query}!</code>\n"

        await message.edit(reply)

    @on(pattern="codename")
    async def get_device_codename(client: Client, message: Message):
        """Retrieve mobile device codename by brand or model."""
        query = message.raw_args

        if not query:
            await message.edit("<i>Usage: .codename -brand- -device-</i>")
            return

        devices = get(DEVICES_DATA_URL).json()
        result = ""

        for key, value in devices.items():
            if query.lower() in str(value).lower() or query.lower() in key.lower():
                for device in value:
                    result += (
                        f"<b>Brand:</b> <i>{device.get('brand')}</i>\n"
                        f"<b>Model:</b> <i>{device.get('name')}</i>\n"
                        f"<b>Codename:</b> <i>{device.get('device')}</i>\n"
                    )

                await message.edit(result)
                return

        await message.edit("<i>Model not found</i>")

    @on(pattern="specs")
    async def get_device_specs(client: Client, message: Message):
        """Retrieve mobile device specifications."""
        if not message.raw_args or " " not in message.raw_args:
            await message.edit("<i>Usage: .specs -brand- -device-</i>")
            return

        brand, model = message.raw_args.split(maxsplit=1)
        await message.edit("<i>Searching for device...</i>")

        brand_page = BeautifulSoup(
            get("https://www.devicespecifications.com/en/brand-more").content, "html.parser"
        )

        brand_link = brand_page.find("a", text=re.compile(brand, re.IGNORECASE))
        if not brand_link:
            await message.edit("<i>Device brand not found</i>")
            return

        model_page = BeautifulSoup(
            get(brand_link["href"]).content, "html.parser"
        )

        model_link = model_page.find("a", text=re.compile(model, re.IGNORECASE))
        if not model_link:
            await message.edit("<i>Device model not found</i>")
            return

        specs_page = BeautifulSoup(
            get(model_link["href"]).content, "html.parser"
        )

        specs_table = specs_page.find("div", {"id": "model-brief-specifications"})
        if not specs_table:
            await message.edit("<i>Specifications not found</i>")
            return

        specs = f"<b>Specifications for {model_link.text}:</b>\n"
        for line in specs_table.get_text(separator="\n").splitlines():
            if line.strip() == "Add for comparison":
                break
            specs += f"<b>{line.strip()}</b> " if specs.endswith("\n") else f"<i>{line.strip()}</i>\n"

        await message.edit(specs)

    @on(pattern="twrp")
    async def get_twrp(client: Client, message: Message):
        """Fetch TWRP download link for an Android device."""
        codename = message.raw_args or (message.reply_to_text.text.split()[0] if message.reply_to_text else None)

        if not codename:
            await message.edit("<code>Usage: .twrp <codename></code>")
            return

        response = get(f"https://dl.twrp.me/{codename}/")
        if response.status_code == 404:
            await message.edit(f"<i>Couldn't find TWRP downloads for {codename}!</i>")
            return

        page = BeautifulSoup(response.content, "html.parser")
        download_link = page.find("table").find("tr").find("a")
        size = page.find("span", {"class": "filesize"}).text
        date = page.find("em").text.strip()

        reply = (
            f"<b>Latest TWRP for {codename}:</b>\n"
            f"<a href='https://dl.twrp.me{download_link['href']}'><i>{download_link.text} - {size}</i></a>\n"
            f"<b>Updated:</b> <i>{date}</i>\n"
        )
        await message.edit(reply)

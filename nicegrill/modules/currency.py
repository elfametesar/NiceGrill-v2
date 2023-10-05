from telethon import TelegramClient as Client
from nicegrill import Message, run
from requests import get

import json

class Currency:
    
    API = "https://free.currconv.com/api/v7/convert?q={from_cur}_{to_cur}&compact=ultra&apiKey=6803cf79e6a6376859d0"
    
    @run(command="cur")
    async def convert_currency(message: Message, client: Client):
        if not message.args:
            await message.edit("<i>You need to specify an amount to convert</i>")
            return

        await message.edit("<i>Converting specified currency</i>")

        amount = "".join([char for char in message.args if char.isdigit() or char == "."])

        arguments = message.args.replace(amount, '')

        if amount:
            try:
                source_currency, target_currency = arguments.split(maxsplit=2)
            except ValueError:
                await message.edit("<i>You need to use this format: 1 USD EUR</i>")
                return

            source_currency = source_currency.strip().upper()
            target_currency = target_currency.strip().upper()

            amount = float(amount)

        result = get(Currency.API.format(from_cur=source_currency, to_cur=target_currency))
        result = json.loads(result.text)

        base_amount = result.get(f"{source_currency}_{target_currency}".upper())

        if not base_amount:
            await message.edit("<i>There is no result for your currency query</i>")
        else:
            await message.edit(f"<i>{amount} {source_currency} is {round(base_amount * amount, 2):,} {target_currency}</i>")
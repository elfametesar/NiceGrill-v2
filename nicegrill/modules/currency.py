from telethon import TelegramClient as Client
from nicegrill import Message, run
from currency_rate.converter import Converter

import asyncio

class Currency:
    
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

        result = await asyncio.to_thread(
            Converter().rate,
            source_currency,
            target_currency,
            amount
        )

        if not result:
            await message.edit("<i>There is no result for your currency query</i>")
        else:
            await message.edit(f"<i>{amount} {source_currency} is {round(float(result), 2):,} {target_currency}</i>")

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

from elfrien.types.patched import Message
from weather import Weather as wtr
from elfrien.client import Client
from nicegrill import on, startup
from database import weather

import logging

log = logging.getLogger(__name__)

class Weather:

    CITY = None

    @on(pattern="weather", incoming=True)
    async def weather(client: Client, message: Message):
        """Shows the weather of specified city"""
        city = message.raw_args.strip()

        if not message.is_self:
            message.edit = message.reply

        if not Weather.CITY and not city:
            await message.edit("<i>Enter a city name first</i>")
            return

        city = city if city else Weather.CITY

        weather = wtr.find(city)

        try:
            await message.edit(
                    f"<b>City:</b> <i>{weather['weather']['city']}</i>\n"
                    f"<b>Temperature:</b> <i>{round(weather['weather']['temp'])}°C</i>\n"
                    f"<b>Pressure:</b> <i>{weather['weather']['pressure']} hPa</i>\n"
                    f"<b>Humidity:</b> <i>{weather['weather']['humidity']}%</i>\n"
                    f"<b>Latency:</b> <i>{weather['weather']['lat']}</i>\n"
                    f"<b>Status:</b> <i>{weather['main']}</i>\n"
                    f"<b>Description:</b> <i>{weather['description'].capitalize()}</i>\n"
                    f"<b>Wind Speed:</b> <i>{weather['wind']['speed']} m/s</i>\n")
        except Exception as e:
            if "status" in weather:
                await message.edit(f"<i>{weather['status'].capitalize()}</i>")
            else:
                log.exception(
                    f"""
        APIT:
        
        {weather}
        
        Error:
        
        {e}"""
                )
                await message.edit("<i>Bot api might be dead, sent the error into logger</i>")


    @on(pattern="setcity")
    async def set_city(client: Client, message: Message):
        """Sets a default city so that you don't have to type it everytime"""
        if not message.raw_args:
            weather.set_city_name("")
            await message.edit("<i>Saved city name removed</i>")
            return

        weather.set_city_name(message.raw_args)
        Weather.CITY = message.raw_args

        await message.edit("<i>Successfully saved</i>")

@startup
def load_from_database():
    Weather.CITY = weather.get_city_name()


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

from database.redis import AsyncRedis, SyncRedis


async def blacklist_chat(chat_id: int):
    return await AsyncRedis.hset(
        "Blacklist", mapping={
            chat_id: "Blacklisted"
        }
    )

def get_all_blacklisted():
    return [*SyncRedis.hgetall(
        "Blacklist"
    ).keys()]

async def whitelist_chat(chat_id: int):
    return await AsyncRedis.hdel(
        "Blacklist", chat_id
    )
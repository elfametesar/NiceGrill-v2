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

from database.redis import AsyncRedis


async def set_antipm(switch: bool):
    return await AsyncRedis.hset(
        "AntiPM", mapping={
            "AntiPM Status": switch
        }
    )


async def approve_user(user_id: int):
    return await AsyncRedis.hset(
        "AntiPM", mapping={
            user_id: "Approved"
        }
    )


async def set_warning_limit(limit: int):
    return await AsyncRedis.hset(
        "AntiPM", mapping={
            "Warning Limit": limit
        }
    )


async def set_notifications(switch: bool):
    return await AsyncRedis.hset(
        "AntiPM", mapping={
            "Notifications": switch
        }
    )


async def set_super_block(switch: bool):
    return await AsyncRedis.hset(
        "AntiPM", mapping={
            "Super Blocking": switch
        }
    )


async def get_all_approved():
    return (await AsyncRedis.hgetall(
        "AntiPM"
    )).keys()


async def is_antipm():
    return await AsyncRedis.hget(
        "AntiPM", "AntiPM Status"
    )


async def get_warning_limit():
    return await AsyncRedis.hget(
        "AntiPM", "Warning Limit"
    )


async def is_superblock():
    return await AsyncRedis.hget(
        "AntiPM", "Super Blocking"
    )


async def is_notifications():
    return await AsyncRedis.hget(
        "AntiPM", "Notifications"
    )


async def disapprove_user(user_id: int):
    return await AsyncRedis.hdel(
        "AntiPM", user_id
    )

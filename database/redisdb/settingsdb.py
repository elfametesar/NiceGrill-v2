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


async def set_download_path(download_path: str):
    return await AsyncRedis.hset(
        "Settings", mapping={
            "Download Path": download_path
        }
    )

async def set_shell_mode(switch: bool):
    return await AsyncRedis.hset(
        "Settings", mapping={
            "Shell Mode": switch
        }
    )

async def set_prefix(prefix: str):
    return await AsyncRedis.hset(
        "Settings", mapping={
            "Prefix": prefix
        }
    )

async def set_restart_details(chat_id: int, message_id: int):
    return await AsyncRedis.hset(
        "Settings", mapping={
            "Restart Chat": chat_id, 
            "Restart Message": message_id
        }
    )

async def get_download_path():
    return await AsyncRedis.hget(
        "Settings", "Download Path"
    )

async def is_shell():
    return await AsyncRedis.hget(
        "Settings", "Shell Mode"
    )

def get_prefix():
    return SyncRedis.hget(
        "Settings", "Prefix"
    )

def get_restart_details():
    settings_data = await AsyncRedis.hgetall(
        "Settings"
    )
    return {
        "Chat": settings_data.get("Restart Chat"),
        "Message": settings_data.get("Restart Message")
    }
    
async def remove_restart_details():
    return await AsyncRedis.hdel(
        "Settings", "Restart Chat", "Restart Message"
    )

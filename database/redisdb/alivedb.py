from database.redis import AsyncRedis

async def set_alive_name(name):
    return await AsyncRedis.hset(
        "Alive", mapping={
            "Name": name
        }
    )

async def set_alive_message(message):
    return await AsyncRedis.hset(
        "Alive", mapping={
            "Message": message
        }
    )

async def get_alive_name():
    return await AsyncRedis.hget("Alive", "Name")

async def get_alive_message():
    return await AsyncRedis.hget("Alive", "Message")

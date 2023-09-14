from database.redis import AsyncRedis

async def set_city_name(city):
    await AsyncRedis.hset(
        "Weather", mapping={
            "City": city
        }
    )

async def get_city_name():
    return (await AsyncRedis.hget("Weather", "City")).decode()

async def delete_city():
    await AsyncRedis.hdel("Weather", "City")
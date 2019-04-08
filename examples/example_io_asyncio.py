import asyncio
from time import time

from aiohttp import ClientSession


async def how_is_the_wheather(client, city="Florianopolis"):
    api_key = "375a06b25f772c2d95634034dd1e57f6"
    api_url = ("http://api.openweathermap.org/data/2.5/"
               f"weather?q={city}&units=metric&APPID={api_key}")
    async with client.get(api_url) as r:
        wheather = await r.json()
        return wheather.get("main", {}).get("temp", "0.0")


async def main(loop):
    cities = [
        "Florianópolis", "São Paulo", "New York", "Pouso Alegre", "Palhoça",
        "São José", "Campinas", "Buenos Aires", "London"
    ]
    requests = []

    async with ClientSession() as session:
        for city in cities:
            requests.append(how_is_the_wheather(session, city))
        temps = await asyncio.gather(*requests)

        for city, temp in zip(cities, temps):
            print(f"Temperatura em {city} é de {temp} ºC")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    initial_time = time()
    loop.run_until_complete(main(loop))
    elapsed_time = time() - initial_time
    print(f"Total Time: {elapsed_time}")

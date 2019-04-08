from time import time

import requests


def how_is_the_wheather(city="Florianopolis"):
    api_key = "375a06b25f772c2d95634034dd1e57f6"
    api_url = ("http://api.openweathermap.org/data/2.5/"
               f"weather?q={city}&units=metric&APPID={api_key}")

    response = requests.get(api_url)

    wheather = response.json()

    return wheather.get("main", {}).get("temp", "0.0")


if __name__ == "__main__":
    initial_time = time()
    cities = [
        "Florianópolis", "São Paulo", "New York", "Pouso Alegre", "Palhoça",
        "São José", "Campinas", "Buenos Aires", "London"
    ]
    for city in cities:
        temp = how_is_the_wheather(city)
        print(f"Temperatura em {city} é de {temp} ºC")
    elapsed_time = time() - initial_time
    print(f"Total time: {elapsed_time}")

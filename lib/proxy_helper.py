import requests
import random

WEBSHARE_API_KEY = ""


def get_proxy():
    response = requests.get("https://proxy.webshare.io/api/proxy/list/?page=1",
                            headers={"Authorization": WEBSHARE_API_KEY})
    proxy_list = response.json()['results']
    selected = random.choice(proxy_list)
    proxy = f"http://{selected['username']}:{selected['password']}@{selected['proxy_address']}:{selected['ports']['http']}"
    return proxy

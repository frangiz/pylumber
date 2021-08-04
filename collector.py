# collects all prices and stores in db. Should be run nightly. 

import requests
import json
from pathlib import Path
from typing import Dict
from bs4 import BeautifulSoup
from requests_html import HTMLSession


Path("dumps").mkdir(exist_ok=True)

urls = []
with open("sources.txt", "r") as f:
    urls = f.readlines()

for url in urls:
    if url.startswith("#"):
        continue
    provider = url.split(".se")[0].split(".")[-1]
    cached_name = provider +"-" +url.strip().split("/")[-1]
    if not Path("dumps", cached_name).exists():
        with open(Path("dumps", cached_name), "w") as f:
            session = HTMLSession()
            resp = session.get(url.strip())
            resp.html.render()
            f.writelines(resp.html.html)


def get_optimera_product(filename: str) -> Dict[str, str]:
    content = ""
    with open(Path("dumps", filename), "r") as f:
        content = "".join(f.readlines())

    marker = r"'products':["
    try:
        start = content.index(marker)
        end = content.index("}", start)
        product = json.loads(content[start + len(marker): end + 1].replace("'", "\""))
        return {
            "name": product["name"],
            "price": product["price"],
            "variant": product["variant"]
        }
    except ValueError as e:
        print(f"{e} for file {filename}")
        raise e


def get_woody_product(filename: str) -> Dict[str, str]:
    content = ""
    with open(Path("dumps", filename), "r") as f:
        content = "".join(f.readlines())
    soup = BeautifulSoup(content, "html.parser")

    product = {
        "name": soup.title.text,
        "price": 0.0,
        "variant": ""
    }
    price = float(soup.find("div", class_="inner-price base-unit").findChild(class_="price").text.replace(" kr", "").replace(",", "."))
    product["price"] = price

    return product

for file in Path("dumps").glob("*"):
    if file.name.startswith("optimera"):
        print(get_optimera_product(file.name))
    if file.name.startswith("woody"):
        print(get_woody_product(file.name))
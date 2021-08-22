# collects all prices and stores in db. Should be run nightly. 

from datetime import datetime
import json
from pathlib import Path
from typing import Dict
from bs4 import BeautifulSoup
import requests
import logging
from urllib.parse import quote

script_path = Path(__file__).parent.absolute()
Path(script_path, "dumps").mkdir(exist_ok=True)

logger = logging.getLogger("collector")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
fh = logging.FileHandler("collector.log", encoding="utf-8")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

lumber_sources = []
with open(Path(script_path, "lumber_sources.json"), "r") as f:
    lumber_sources = json.load(f)


def get_url_content(url: str) -> str:
    if url.startswith("#"):
            return
    provider = url.split(".se")[0].split(".")[-1]

    # Check if the file is cached
    cached_name = provider +"-" +url.strip().split("/")[-1]
    #if Path("dumps", cached_name).exists():
        #with open(Path("dumps", cached_name), "r") as f:
            #return "".join(f.readlines())

    # File is not cached, load it from the internet
    resp = requests.get(url.strip())

    # Dump the result
    with open(Path(script_path, "dumps", cached_name), "w") as f:
        f.writelines(resp.text)

    return resp.text


def get_optimera_product(url: str) -> Dict[str, str]:
    content = get_url_content(url)
    marker = r"'products':["
    try:
        start = content.index(marker)
        end = content.index("}", start)
        product = json.loads(content[start + len(marker): end + 1].replace("'", "\""))
        return {
            "source": "optimera",
            "description": product["name"],
            "price": product["price"]
        }
    except ValueError as e:
        logger.warning(f"{e} for url {url}")
        raise e


def get_woody_product(url: str) -> Dict[str, str]:
    content = get_url_content(url)
    soup = BeautifulSoup(content, "html.parser")

    product = {
        "source": "woody",
        "description": soup.title.text,
        "price": 0.0
    }
    id = id = soup.find("div", class_="inner-price base-unit").parent.get("data-partnersku")
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    data = {"ProductId":[],"partnersku":[str(id).replace(" ", "+")]}
    data = json.dumps(data).replace(" ", "")
    data = "products="+quote(data).replace("%2B", "+")
    api_url = "https://fellessonsbygghandel.woody.se/api/externalprice/priceinfos"
    res = requests.post(api_url, data=data, headers=headers)
    product["price"] = float(res.json()["partnerskus"][0]["Price"].replace(",", "."))

    return product


for group in lumber_sources:
    print(f"{group['name']}")
    for url in group["urls"]:
        product = {}
        try:
            if "optimera" in url:
                product = get_optimera_product(url)
            if "woody" in url:
                product = get_woody_product(url)
            product["date"] = datetime.utcnow().date().isoformat()
            product["group_name"] = group["name"]
            product["url"] = url
            print(product)
            logger.debug(product)
            resp = requests.post(url="http://localhost:5000/api/pricedproduct", json=product)
        except Exception as e:
            logger.warning(f"Got exception {e} for url {url}")
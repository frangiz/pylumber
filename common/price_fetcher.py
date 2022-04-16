from bs4 import BeautifulSoup
from urllib.parse import quote
import requests
from pathlib import Path
from typing import Dict
import json


class PriceFetcher:
    def __init__(self):
        self.script_path = Path(__file__).parent.parent.absolute()
        Path(self.script_path, "dumps").mkdir(exist_ok=True)

    def get_url_content(self, url: str) -> str:
        resp = requests.get(url.strip())

        # Dump the response in a file in case we need to go on a bug hunt.
        provider = url.split(".se")[0].split(".")[-1]
        cached_name = f"{provider}-" + url.strip().split("/")[-1]
        with open(Path(self.script_path, "dumps", cached_name), "w") as f:
            f.writelines(resp.text)

        return resp.text


    def get_optimera_price(self, url: str) -> Dict[str, str]:
        content = self.get_url_content(url)
        marker = r"'products':["
        start = content.index(marker)
        end = content.index("}", start)
        product = json.loads(content[start + len(marker): end + 1].replace("'", "\""))
        return float(product["price"])


    def get_woody_price(self, url: str) -> Dict[str, str]:
        content = self.get_url_content(url)
        soup = BeautifulSoup(content, "html.parser")

        id = id = soup.find("div", class_="inner-price base-unit").parent.get("data-partnersku")
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"ProductId":[],"partnersku":[str(id).replace(" ", "+")]}
        data = json.dumps(data).replace(" ", "")
        data = "products="+quote(data).replace("%2B", "+")
        api_url = "https://fellessonsbygghandel.woody.se/api/externalprice/priceinfos"
        res = requests.post(api_url, data=data, headers=headers)
        return float(res.json()["partnerskus"][0]["Price"].replace(",", ".").replace("\xa0", ""))


    def get_byggmax_price(self, url: str) -> Dict[str, str]:
        content = self.get_url_content(url)
        soup = BeautifulSoup(content, "html.parser")

        for script_tag in soup.find_all("script", type="application/ld+json"):
            tag_data = json.loads(script_tag.string)
            if type(tag_data) != list:
                continue
            product_types = list(filter(lambda item: item.get("@type", None) == "Product", tag_data))

            def fix_url(the_url):
                quoted_chars = {
                    'å': quote('å'),
                    'ä': quote('ä'),
                    'ö': quote('ö')
                }
                for k, v in quoted_chars.items():
                    the_url = the_url.replace(k, v)
                return the_url

            # We have one product on the page, so return the price.
            if len(product_types) == 1 and fix_url(product_types[0]["offers"].get("url", None)).startswith(url):
                return product_types[0]["offers"]["price"]
            # We have multiple products on the same page selectable by dropdowns.
            for item in product_types:
                if fix_url(item["offers"].get("url", None)) == url:
                    return item["offers"]["price"]
        raise RuntimeError("No price found, probably something wrong with the html.")

    def get_bauhaus_price(self, url: str) -> float:
        content = self.get_url_content(url)
        soup = BeautifulSoup(content, "html.parser")
        base_tag = soup.find("div", class_="price-box price-final_price")

        return float(base_tag.find(lambda tag: tag.name=="meta" and tag.attrs.get("itemprop", "") == "price").attrs.get("content"))

    def get_price(self, store: str, url: str) -> float:
        if store == "optimera":
            return self.get_optimera_price(url)
        elif store == "woody":
            return self.get_woody_price(url)
        elif store == "byggmax":
            return self.get_byggmax_price(url)
        elif store == "bauhaus":
            return self.get_bauhaus_price(url)
        raise ValueError(f"Store {store} not known.")
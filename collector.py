# collects all prices and stores in db. Should be run nightly. 

from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List
from bs4 import BeautifulSoup
import requests
import logging
from urllib.parse import quote
import traceback
import ssl
import smtplib
from app.resources import PriceCreateModel


def get_url_content(url: str) -> str:
    resp = requests.get(url.strip())

    # Dump the response in a file in case we need to go on a bug hunt.
    provider = url.split(".se")[0].split(".")[-1]
    cached_name = provider +"-" +url.strip().split("/")[-1]
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
        return float(product["price"])
    except ValueError as e:
        logger.warning(f"{e} for url {url}")
        raise e


def get_woody_product(url: str) -> Dict[str, str]:
    content = get_url_content(url)
    soup = BeautifulSoup(content, "html.parser")

    id = id = soup.find("div", class_="inner-price base-unit").parent.get("data-partnersku")
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    data = {"ProductId":[],"partnersku":[str(id).replace(" ", "+")]}
    data = json.dumps(data).replace(" ", "")
    data = "products="+quote(data).replace("%2B", "+")
    api_url = "https://fellessonsbygghandel.woody.se/api/externalprice/priceinfos"
    res = requests.post(api_url, data=data, headers=headers)
    return float(res.json()["partnerskus"][0]["Price"].replace(",", ".").replace("\xa0", ""))


def get_byggmax_product(url: str) -> Dict[str, str]:
    content = get_url_content(url)
    soup = BeautifulSoup(content, "html.parser")

    for script_tag in soup.find_all("script", type="application/ld+json"):
        tag_data = json.loads(script_tag.string)
        if type(tag_data) != list:
            continue
        product_types = list(filter(lambda item: item.get("@type", None) == "Product", tag_data))

        def fix_url(the_url):
            quoted_chars = {
                'ä': quote('ä')
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
    return 0.0

def get_bauhaus_product(url: str) -> float:
    content = get_url_content(url)
    soup = BeautifulSoup(content, "html.parser")
    base_tag = soup.find("div", class_="price-box price-final_price")

    return float(base_tag.find(lambda tag: tag.name=="meta" and tag.attrs.get("itemprop", "") == "price").attrs.get("content"))


def notify_result(failed_urls: List[str]) -> None:
    is_monday = datetime.today().isoweekday() == 1
    if is_monday or failed_urls:
        smtp_config = {}
        with open(Path(script_path, "collector_cnf.json"), "r") as f:
            smtp_config = json.load(f)
        context = ssl.create_default_context()
        msg = create_email(is_monday, failed_urls)
        with smtplib.SMTP_SSL(smtp_config["SMTP_HOST"], smtp_config["SMTP_PORT"], context=context) as server:
            server.login(smtp_config["SMTP_SENDER_EMAIL"], smtp_config["SMTP_SENDER_PASSWORD"])
            server.sendmail(smtp_config["SMTP_SENDER_EMAIL"], smtp_config["SMTP_RECIPIENTS"], msg)
            server.quit()
            logger.debug(f"Sent email: {msg}")


def create_email(monday: bool, failed_urls: List[str]) -> str:
    if monday and not failed_urls:
        return """Subject: Monday - It still works test

        It is Monday and I just want to make sure that I can send you status emails.

        This message was generated {}
        Yours sincerely,
        pylumber
        """.format(datetime.now())

    return """Subject: One or more urls failed

        I am sorry to inform you that one or more urls have failed to return data. Here is the list {}.

        This message was generated {}
        Yours sincerely,
        pylumber
        """.format(", ".join(failed_urls), datetime.now())


def get_products():
    products = []
    resp = requests.get(url="http://localhost:5000/api/products")
    for group in resp.json():
        for product in group["products"]:
            products.append((product["id"], product["store"], product["url"]))
    return products


def collect(access_token, products):
    processed_products = 0
    failed_urls = []
    for id, store, url in products:
        try:
            price = 0.0
            if store == "optimera":
                price = get_optimera_product(url)
            if store == "woody":
                price = get_woody_product(url)
            if store == "byggmax":
                price = get_byggmax_product(url)
            if store == "bauhaus":
                price = get_bauhaus_product(url)

            price_snapshot = PriceCreateModel(price=price, date=datetime.utcnow().date().isoformat())
            logger.debug(f"product id: {id}, store: {store}, price data: {price_snapshot.dict()}")
            requests.post(url=f"http://localhost:5000/api/products/{id}/prices", json=price_snapshot.dict(), headers={"access_token": access_token})
        except Exception as e:
            logger.exception(f"Got exception {e} for url {url}")
            print(url)
            traceback.print_exc()
            failed_urls.append(url)
        processed_products += 1
        print(f"Processed {processed_products}/{len(products)}")

    notify_result(failed_urls)


if __name__ == '__main__':
    script_path = Path(__file__).parent.absolute()
    Path(script_path, "dumps").mkdir(exist_ok=True)
    Path(script_path, "logs").mkdir(exist_ok=True)

    logger = logging.getLogger("collector")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    fh = logging.FileHandler(Path(script_path, "logs", "collector.log"), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    access_token = None
    # Let us use the first token in the allow list.
    with open(Path(script_path, "access_tokens.txt"), 'r+') as f:
        access_token = f.readline().strip()

    collect(access_token, get_products())
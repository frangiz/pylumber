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
            "price": float(product["price"])
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


def get_byggmax_product(url: str) -> Dict[str, str]:
    content = get_url_content(url)
    soup = BeautifulSoup(content, "html.parser")
    title = soup.find(lambda tag: tag.name=="span" and tag.attrs.get("data-ui-id", "") == "page-title-wrapper").get_text()
    base_tag = soup.find("div", class_="price-box price-final_price")

    price_kr = int(base_tag.find("span", class_="integer").get_text())
    decimal_text = base_tag.find("span", class_="decimal").get_text()
    price_decimals = float(decimal_text if decimal_text.strip() != "" else "0")
    display_unit = base_tag.find("span", class_="package-display-unit").get_text()

    price = price_kr + price_decimals / 100.0

    return {
        "source": "byggmax",
        "description": title,
        "price": price
    }


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


total_sources = sum(len(group["sources"]) for group in lumber_sources)
processed_sources = 0
failed_urls = []
for group in lumber_sources:
    for source in group["sources"]:
        product = {}
        try:
            url = source["url"]
            alt_unit_factor = source.get("alt_unit_factor", 1.0)
            if "optimera" in url:
                product = get_optimera_product(url)
            if "woody" in url:
                product = get_woody_product(url)
            if "byggmax" in url:
                product = get_byggmax_product(url)
            product["price"] = product["price"] / alt_unit_factor
            product["date"] = datetime.utcnow().date().isoformat()
            product["group_name"] = group["name"]
            product["url"] = url
            logger.debug(product)
            #resp = requests.post(url="http://localhost:5000/api/pricedproduct", json=product)
        except Exception as e:
            logger.exception(f"Got exception {e} for url {url}")
            print(url)
            traceback.print_exc()
            failed_urls.append(url)
        processed_sources += 1
        print(f"Processed {processed_sources}/{total_sources}")

notify_result(failed_urls)
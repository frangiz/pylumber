# collects all prices and stores in db. Should be run nightly. 

from datetime import datetime
import json
from pathlib import Path
from typing import List

import requests
import logging
import traceback
import ssl
import smtplib
from app.resources import PriceCreateModel
import argparse
from datetime import timezone
from common.price_fetcher import PriceFetcher

def notify_result(failed_urls: List[str]) -> None:
    is_monday = datetime.now().isoweekday() == 1
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
    resp = requests.get(url="http://localhost:5000/api/products?prices=true")
    for group in resp.json():
        for product in group["products"]:
            last_price_snapshot = product["prices"][-1 ]["date"] if product["prices"] else None
            if last_price_snapshot != datetime.now(timezone.utc).date().isoformat():
                products.append((product["id"], product["store"], product["url"]))
    return products


def collect(access_token, products):
    failed_urls = []
    price_fetcher = PriceFetcher()
    for processed_products, (id, store, url) in enumerate(products, start=1):
        try:
            price = price_fetcher.get_price(store, url)
            price_snapshot = PriceCreateModel(price=price, date=datetime.now(timezone.utc).date().isoformat())
            logger.debug(f"product id: {id}, store: {store}, price data: {price_snapshot.dict()}")
            requests.post(url=f"http://localhost:5000/api/products/{id}/prices", json=price_snapshot.dict(), headers={"access_token": access_token})
        except Exception as e:
            logger.exception(f"Got exception {e} for url {url}")
            print(url)
            traceback.print_exc()
            failed_urls.append(url)
        print(f"Processed {processed_products}/{len(products)}")

    notify_result(failed_urls)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Collecting some price snapshots.')
    parser.add_argument(
        "-s",
        "--stores",
        nargs="*",
        choices=["optimera", "woody", "byggmax", "bauhaus"],
        help="Collect only snapshots for this store.",
    )
    args = parser.parse_args()

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

    products = get_products()
    if args.stores:
        products = list(filter(lambda p: p[1] in (args.stores), products))
    collect(access_token, products)
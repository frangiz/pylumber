# collects all prices and stores in db. Should be run nightly.

import argparse
import logging
import smtplib
import ssl
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import requests  # type: ignore
import sentry_sdk
from pydantic import BaseModel, BaseSettings

from app.resources import PriceCreateModel
from common.price_fetcher import PriceFetcher


class SMTPSettings(BaseSettings):
    host: str = ""
    port: int = 0
    sender_email: str = ""
    sender_password: str = ""
    recipients: List[str] = []

    class Config:
        env_prefix = "smtp_"


class Settings(BaseSettings):
    flask_env: str = "development"
    sentry_sdk_dsn: str = ""
    smtp: SMTPSettings = SMTPSettings()


class Product(BaseModel):
    id: int
    store: str
    url: str


def now_isoformat() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def notify_result(failed_urls: List[str], settings: SMTPSettings) -> None:
    is_monday = datetime.now().isoweekday() == 1
    if is_monday or failed_urls:
        context = ssl.create_default_context()
        msg = create_email(is_monday, failed_urls)
        with smtplib.SMTP_SSL(settings.host, settings.port, context=context) as server:
            server.login(settings.sender_email, settings.sender_password)
            server.sendmail(settings.sender_email, settings.recipients, msg)
            server.quit()
            logger.debug(f"Sent email: {msg}")


def create_email(monday: bool, failed_urls: List[str]) -> str:
    if monday and not failed_urls:
        return """Subject: Monday - It still works test

        It is Monday and I just want to make sure that I can send you status emails.

        This message was generated {}
        Yours sincerely,
        pylumber
        """.format(
            datetime.now()
        )

    return """Subject: One or more urls failed

        I am sorry to inform you that one or more urls have failed to return data. Here is the list {}.

        This message was generated {}
        Yours sincerely,
        pylumber
        """.format(  # noqa: E501
        ", ".join(failed_urls), datetime.now()
    )


def get_products() -> List[Product]:
    products = []
    resp = requests.get(url="http://localhost:5000/api/products")
    for group in resp.json():
        for prod in group["products"]:
            if prod["price_updated_date"] != now_isoformat():
                products.append(Product(**prod))
    return products


def upload_price(access_token: str, product: Product, price: float):
    price_snapshot = PriceCreateModel(price=price, date=now_isoformat())
    logger.debug(
        f"product id: {product.id}, store: {product.store}, price data: {price_snapshot.dict()}"  # noqa: E501
    )
    requests.post(
        url=f"http://localhost:5000/api/products/{product.id}/prices",
        json=price_snapshot.dict(),
        headers={"access_token": access_token},
    )


def collect(access_token, products, smtp_settings):
    failed_urls = []
    price_fetcher = PriceFetcher()
    for processed_products, product in enumerate(products, start=1):
        try:
            price = price_fetcher.get_price(product.store, product.url)
            upload_price(access_token, product, price)
        except Exception as e:
            logger.exception(f"Got exception {e} for url {product.url}")
            print(product.url)
            traceback.print_exc()
            failed_urls.append(product.url)
        print(f"Processed {processed_products}/{len(products)}")

    notify_result(failed_urls, smtp_settings)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collecting some price snapshots.")
    parser.add_argument(
        "-s",
        "--stores",
        nargs="*",
        choices=["optimera", "woody", "byggmax", "bauhaus"],
        help="Collect only snapshots for this store.",
    )
    args = parser.parse_args()

    settings = Settings()

    sentry_sdk.init(dsn=settings.sentry_sdk_dsn, environment=settings.flask_env)

    script_path = Path(__file__).parent.absolute()
    Path(script_path, "dumps").mkdir(exist_ok=True)
    Path(script_path, "logs").mkdir(exist_ok=True)

    logger = logging.getLogger("collector")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    fh = logging.FileHandler(
        Path(script_path, "logs", "collector.log"), encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    access_token = None
    # Let us use the first token in the allow list.
    with open(Path(script_path, "access_tokens.txt"), "r+") as f:
        access_token = f.readline().strip()

    products = get_products()
    if args.stores:
        products = list(filter(lambda p: p.store in (args.stores), products))
    collect(access_token, products, settings.smtp)

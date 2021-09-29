from app.services import get_priced_products
from flask import Blueprint, render_template

bp = Blueprint("website", __name__)


def get_last_price_change(prices):
    last_price = prices[-1]["price"]
    price_change = {
        "date": prices[0]["date"],
        "price": prices[0]["price"],
        "change": "---" # TODO: figure this one out
    }
    for price_snapshot in reversed(prices):
        if last_price != price_snapshot["price"]:
            return price_change
        price_change["date"] = price_snapshot["date"]
        price_change["price"] = price_snapshot["price"]
    return price_change


@bp.route("/", methods=["GET"])
def index():
    with open("version.txt", "r") as f:
        version = f.readline().strip()
    all_prices = get_priced_products()
    price_tables_data = {}
    for group in all_prices:
        price_tables_data[group["group_name"]] = []
        for source in group["sources"]:
            last_price_change = get_last_price_change(source["prices"])
            data = {
                'store': source["source"],
                'date': last_price_change["date"],
                'price': last_price_change["price"],
                'price changed': last_price_change["change"]
            }
            price_tables_data[group["group_name"]].append(data)
    return render_template("main.jinja2", groups=all_prices, price_tables_data=price_tables_data, version=version)
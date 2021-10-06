from app.services import get_priced_products
from flask import Blueprint, render_template

bp = Blueprint("website", __name__)


def float_to_kr_str(value: float) -> str:
    sign = "+" if value > 0.0 else ""
    return f"{sign}{value:.2f} kr"


def get_last_price_change(prices):
    price_change = {
        "date": prices[0]["date"],
        "price": prices[0]["price"],
        "change": "---"
    }
    if len(prices) == 1:
        return price_change
    for i in range(len(prices) - 1, 0, -1):
        current_snapshot = prices[i]
        prev_snapshot = prices[i - 1]
        if current_snapshot["price"] != prev_snapshot["price"]:
            price_change["date"] = current_snapshot["date"]
            price_change["price"] = current_snapshot["price"]
            price_change["change"] = float_to_kr_str(current_snapshot["price"] - prev_snapshot["price"])
            return price_change
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
                'price': float_to_kr_str(last_price_change["price"])[1:],
                'price_changed': last_price_change["change"]
            }
            price_tables_data[group["group_name"]].append(data)
    return render_template("main.jinja2", groups=all_prices, price_tables_data=price_tables_data, version=version)
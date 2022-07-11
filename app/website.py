from datetime import date, datetime, time

from flask import Blueprint, render_template

from app.services import get_products

bp = Blueprint("website", __name__)


def float_to_kr_str(value: float) -> str:
    sign = "+" if value > 0.0 else ""
    return f"{sign}{value:.2f} kr"


def get_last_price_change(prices):
    if len(prices) == 0:
        return {
            "date": None,
            "price": 0.0,
            "change": None,
            "change_str": "---",
            "change_percent": 0.0,
        }
    price_change = {
        "date": prices[0].date,
        "price": prices[0].price,
        "change": None,
        "change_str": "---",
        "change_percent": 0.0,
    }
    if len(prices) == 1:
        return price_change
    for i in range(len(prices) - 1, 0, -1):
        current_snapshot = prices[i]
        prev_snapshot = prices[i - 1]
        if current_snapshot.price != prev_snapshot.price:
            price_change["date"] = current_snapshot.date
            price_change["price"] = current_snapshot.price
            price_change["change"] = current_snapshot.price - prev_snapshot.price
            price_change["change_str"] = float_to_kr_str(
                current_snapshot.price - prev_snapshot.price
            )
            change_percent = current_snapshot.price / prev_snapshot.price
            price_change["change_percent"] = (
                change_percent if change_percent < 0 else change_percent - 1
            ) * 100
            return price_change
    return price_change


def get_price_change_color(date: date, price_change: float) -> str:
    if date is None or price_change is None:
        return "black"
    if (datetime.utcnow() - datetime.combine(date, time())).days <= 5:
        return "red" if price_change > 0.0 else "green"
    return "black"


@bp.route("/", methods=["GET"])
def index():
    with open("version.txt", "r") as f:
        version = f.readline().strip()
    all_products = get_products()
    price_table_data = {}
    price_change_data = []
    for group in all_products:
        products = []
        for product in group.products:
            last_price_change = get_last_price_change(product.price_trends)
            data = {
                "store": product.store,
                "url": product.url,
                "date": last_price_change["date"],
                "price": float_to_kr_str(last_price_change["price"])[1:],
                "price_changed": last_price_change["change_str"],
                "price_changed_percent": last_price_change["change_percent"],
                "text_color": get_price_change_color(
                    last_price_change["date"], last_price_change["change"]
                ),
            }
            products.append(data)
            if data["text_color"] != "black":
                price_change_data.append({**{"group_name": group.group_name}, **data})
        products.sort(key=lambda p: float(p["price"].replace(" kr", "")), reverse=True)
        price_table_data[group.group_name] = products

    price_change_data.sort(key=lambda p: (p["date"], p["group_name"]), reverse=True)
    return render_template(
        "main.jinja2",
        price_change_data=price_change_data,
        price_table_data=price_table_data,
        version=version,
    )

from app.models import Product, PriceSnapshot
from itertools import groupby
from operator import attrgetter


def get_products():
    entries = Product.query.all()
    entries.sort(key=lambda e: e.group_name)

    return [{"group_name": k, "products": [e.to_dict_except(["group_name"]) for e in g]} for k, g in groupby(entries, attrgetter("group_name"))]


def get_products_with_prices():
    res = get_products()
    for group in res:
        for source in group["products"]:
            price_snapshots = PriceSnapshot.query.filter_by(product_id=source["id"]).all()
            source["prices"] = [ps.to_dict_except(["id", "product_id"]) for ps in price_snapshots]
            del source["id"]

    return res
from app.models import Product, PriceTrend
from itertools import groupby
from operator import attrgetter
from natsort import natsorted


def get_products():
    entries = Product.query.all()
    entries.sort(key=lambda e: e.group_name)

    res = [{"group_name": k, "products": [e.to_dict_except(["group_name"]) for e in g]} for k, g in groupby(entries, attrgetter("group_name"))]
    return natsorted(res, key=lambda g: g["group_name"])


def get_products_with_price_trends():
    res = get_products()
    for group in res:
        for source in group["products"]:
            price_trends = PriceTrend.query.filter_by(product_id=source["id"]).all()
            source["price_trends"] = [pt.to_dict_except(["id", "product_id"]) for pt in price_trends]
    return res
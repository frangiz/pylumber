from itertools import groupby
from operator import attrgetter

from natsort import natsorted

from app.models import Product


def get_products():
    entries = Product.query.order_by(Product.group_name, Product.current_price).all()

    res = [
        {"group_name": k, "products": [e.to_dict_except(["group_name"]) for e in g]}
        for k, g in groupby(entries, attrgetter("group_name"))
    ]
    return natsorted(res, key=lambda g: g["group_name"])

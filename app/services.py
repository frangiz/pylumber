from app.models import Product, PriceSnapshot
from itertools import groupby
from operator import attrgetter
from typing import List


def get_products():
    entries = Product.query.all()
    entries.sort(key=lambda e: e.group_name)

    return [{"group_name": k, "products": [e.to_dict_except(["group_name"]) for e in g]} for k, g in groupby(entries, attrgetter("group_name"))]


def filter_repeating_values(values: PriceSnapshot) -> List[PriceSnapshot]:
    '''Removes duplicated values (checking the price), but keeping the first and last in the group.'''
    res = []
    for _, g in groupby(values, attrgetter("price")):
        group = list(g)
        res.append(group[0])
        if group[0].date != group[-1].date:
            res.append(group[-1])
    return res


def get_products_with_prices():
    res = get_products()
    for group in res:
        for source in group["products"]:
            price_snapshots = PriceSnapshot.query.filter_by(product_id=source["id"]).all()
            price_snapshots = filter_repeating_values(price_snapshots)
            source["prices"] = [ps.to_dict_except(["id", "product_id"]) for ps in price_snapshots]

    return res
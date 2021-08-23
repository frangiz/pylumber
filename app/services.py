from app.models import PricedProduct, PriceSnapshot
from itertools import groupby
from operator import attrgetter


def get_priced_products():
    entries = PricedProduct.query.all()
    entries.sort(key=lambda e: e.group_name)

    res = [{"group_name": k, "sources": [e.to_dict_except(["group_name"]) for e in g]} for k, g in groupby(entries, attrgetter("group_name"))]

    for group in res:
        for source in group["sources"]:
            price_snapshots = PriceSnapshot.query.filter_by(priced_product_id=source["id"]).all()
            source["prices"] = [ps.to_dict_except(["id", "priced_product_id"]) for ps in price_snapshots]
            del source["id"]

    return res
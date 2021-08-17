from flask import Blueprint, render_template
from app.models import PricedProduct, PriceSnapshot
from itertools import groupby
from operator import attrgetter

bp = Blueprint("website", __name__)

@bp.route("/", methods=["GET"])
def index():
    entries = PricedProduct.query.all()

    res = [{"group_name": k, "sources": [e.to_dict_except(["group_name"]) for e in g]} for k, g in groupby(entries, attrgetter("group_name"))]

    for group in res:
        for source in group["sources"]:
            price_snapshots = PriceSnapshot.query.filter_by(priced_product_id=source["id"]).all()
            source["prices"] = [ps.to_dict_except(["id", "priced_product_id"]) for ps in price_snapshots]
            del source["id"]

    return render_template("main.html", groups=res)
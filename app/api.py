from operator import attrgetter
from flask import Blueprint, request, current_app, abort
from flask.json import jsonify
from app import db
from app.models import PricedProduct
from itertools import groupby

bp = Blueprint("api", __name__)

@bp.route("/pricedproduct", methods=["POST"])
def create_priced_product():
    if request.remote_addr not in ["127.0.0.1"]:
        current_app.logger.warning(f"Got a call from remote addr {request.remote_addr}")
        abort(404)
    body = request.get_json()
    pp = PricedProduct()
    pp.date = body["date"]
    pp.group_name = body["group_name"]
    pp.source = body["source"]
    pp.description = body["description"]
    pp.url = body["url"]
    pp.price = body["price"]

    db.session.add(pp)
    db.session.commit()

    return jsonify(pp.to_dict()), 200


@bp.route("/pricedproduct", methods=["GET"])
def list_priced_products():
    entries = PricedProduct.query.all()

    # crude sorting, should probably be improved
    res = [{"name": k, "sources": list(g)} for k, g in groupby(entries, attrgetter('group_name'))]
    for group in res:
        group["sources"] = [{"source": k[0], "descr": k[1], "url": k[2], "prices": list(g)} for k, g in groupby(group["sources"], lambda e: (e.source, e.description, e.url))]
    for group in res:
        for source in group["sources"]:
            source["prices"] = [{"date": e.date, "price": e.price} for e in source["prices"]]

    return jsonify(res), 200
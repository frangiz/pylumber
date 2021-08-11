from operator import attrgetter
from flask import Blueprint, request, current_app, abort
from flask.json import jsonify
from app import db
from app.models import PricedProduct, PriceSnapshot
from itertools import groupby

bp = Blueprint("api", __name__)

@bp.route("/pricedproduct", methods=["POST"])
def create_priced_product():
    if request.remote_addr not in ["127.0.0.1"]:
        current_app.logger.warning(f"Got a call from remote addr {request.remote_addr}")
        abort(404)
    body = request.get_json()

    priced_product = PricedProduct.query.filter_by(group_name=body["group_name"], source=body["source"]).first()
    if not priced_product:
        pp = PricedProduct()
        pp.group_name = body["group_name"]
        pp.source = body["source"]
        pp.description = body["description"]
        pp.url = body["url"]

        db.session.add(pp)
        db.session.commit()

        priced_product = pp
    
    if PriceSnapshot.query.filter_by(priced_product_id=priced_product.id, date=body["date"]).first():
        current_app.logger.warning(f"Already got price snapshot {body}")
        abort(400)
    
    ps = PriceSnapshot()
    ps.priced_product_id = priced_product.id
    ps.date = body["date"]
    ps.price = body["price"]

    db.session.add(ps)
    db.session.commit()

    return jsonify({**priced_product.to_dict(), **ps.to_dict()}), 200


@bp.route("/pricedproduct", methods=["GET"])
def list_priced_products():
    entries = PricedProduct.query.all()

    res = [{"group_name": k, "sources": [e.to_dict_except(["group_name"]) for e in g]} for k, g in groupby(entries, attrgetter("group_name"))]

    for group in res:
        for source in group["sources"]:
            price_snapshots = PriceSnapshot.query.filter_by(priced_product_id=source["id"]).all()
            source["prices"] = [ps.to_dict_except(["id", "priced_product_id"]) for ps in price_snapshots]
            del source["id"]

    return jsonify(res), 200


@bp.route("/shutdown", methods=["GET"])
def shutdown():
    if request.remote_addr not in ["127.0.0.1"]:
        current_app.logger.warning(f"Got a call from remote addr {request.remote_addr}")
        abort(404)

    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return "Shutting down..."
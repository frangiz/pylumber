from flask import Blueprint, request, current_app, abort
from flask.json import jsonify
from app import db
from app.models import PricedProduct, PriceSnapshot
from app.services import get_priced_products

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
    return jsonify(get_priced_products()), 200
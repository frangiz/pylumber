from datetime import datetime
from flask import Blueprint, request, current_app, abort
from flask.json import jsonify
from app import db
from app.models import Product, PriceSnapshot
import app.services as services
from pydantic import BaseModel, validator
from flask_pydantic import validate
from app.auth import token_required

bp = Blueprint("api", __name__)

class PriceCreateModel(BaseModel):
    price: float
    date: str

    @validator("date")
    def date_must_be_isoformat(cls, value):
        datetime.strptime(value, "%Y-%m-%d")
        return value


class Source(BaseModel):
    group_name: str
    source: str
    url: str
    alt_unit_factor: float


@bp.route("/products/<int:id>/prices", methods=["POST"])
@token_required
@validate()
def create_priced_product(id, body: PriceCreateModel):
    product = Product.query.filter_by(id=id).first()
    if not product:
        current_app.logger.warning(f"Could not find product with id {id} and add the body {body}")
        abort(400)
    if PriceSnapshot.query.filter_by(product_id=product.id, date=body.date).first():
        current_app.logger.warning(f"Already got price snapshot {body}")
        abort(400)
    
    # TODO handle price_modifier here
    ps = PriceSnapshot()
    ps.product_id = product.id
    ps.date = body.date
    ps.price = body.price

    db.session.add(ps)
    db.session.commit()

    return jsonify({**product.to_dict(), **ps.to_dict()}), 200


@bp.route("/products", methods=["GET"])
def get_products():
    if request.args.get("prices", False):
        return jsonify(services.get_products_with_prices()), 200
    return jsonify(services.get_products()), 200

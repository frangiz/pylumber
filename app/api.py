from datetime import datetime
from flask import Blueprint, request, current_app, abort
from flask.json import jsonify
from app import db
from app.models import Product, PriceSnapshot
import app.services as services
from pydantic import BaseModel, validator
from flask_pydantic import validate
from app.auth import token_required
from app.modifiers import price_modifiers

bp = Blueprint("api", __name__)

class PriceCreateModel(BaseModel):
    price: float
    date: str

    @validator("date")
    def date_must_be_isoformat(cls, value):
        datetime.strptime(value, "%Y-%m-%d")
        return value


class ProductCreateModel(BaseModel):
    group_name: str
    store: str
    description: str = ""
    url: str
    price_modifier: str

    @validator("price_modifier")
    def price_modifier_must_be_known(cls, value):
        if value in price_modifiers:
            return value
        raise ValueError("Modifier not known")


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

    ps = PriceSnapshot()
    ps.product_id = product.id
    ps.date = body.date
    ps.price = round(price_modifiers[product.price_modifier](body.price), 2)

    db.session.add(ps)
    db.session.commit()

    return jsonify({**product.to_dict(), **ps.to_dict()}), 200


@bp.route("/products", methods=["GET"])
def get_products():
    if request.args.get("prices", False):
        return jsonify(services.get_products_with_prices()), 200
    return jsonify(services.get_products()), 200


@bp.route("/products", methods=["POST"])
@token_required
@validate()
def create_product(body: ProductCreateModel):
    product = Product.query.filter_by(group_name=body.group_name, store=body.store).first()
    if product:
        current_app.logger.warning(f"Product already exits {body}")
        abort(400)
    p = Product()
    p.group_name = body.group_name
    p.store = body.store
    p.description = body.description
    p.url = body.url
    p.price_modifier = body.price_modifier

    db.session.add(p)
    db.session.commit()

    return jsonify({"msg": "ok"}), 200

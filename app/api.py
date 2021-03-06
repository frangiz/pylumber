from flask import Blueprint, abort, current_app
from flask.json import jsonify
from flask_pydantic import validate

import app.services as services
from app import db, price_fetcher
from app.auth import token_required
from app.models import PriceSnapshot, PriceTrend, Product
from app.resources import (
    PriceCreateModel,
    ProductCreateModel,
    ProductResponseModel,
    price_modifiers,
)

bp = Blueprint("api", __name__)


@bp.route("/products/<int:id>/prices", methods=["POST"])
@token_required
@validate()
def create_price(id, body: PriceCreateModel):
    product = Product.query.filter_by(id=id).first()
    if not product:
        current_app.logger.warning(
            f"Could not find product with id {id} and add the body {body}"
        )
        abort(400)
    if PriceSnapshot.query.filter_by(product_id=product.id, date=body.date).first():
        current_app.logger.warning(f"Already got price snapshot {body}")
        abort(400)

    price = round(price_modifiers[product.price_modifier](body.price), 2)

    product.price_updated_date = body.date
    product.current_price = price

    ps = PriceSnapshot()
    ps.product_id = product.id
    ps.date = body.date
    ps.price = price

    price_trends = PriceTrend.query.filter_by(product_id=product.id).all()
    if len(price_trends) < 2:
        db.session.add(PriceTrend(product_id=product.id, date=body.date, price=price))
    elif price_trends[-2].price == price and price_trends[-1].price == price:
        price_trends[-1].date = body.date
        db.session.add(price_trends[-1])
    else:
        db.session.add(PriceTrend(product_id=product.id, date=body.date, price=price))

    db.session.add(ps)
    db.session.add(product)
    db.session.commit()

    return ProductResponseModel.from_orm(product).json(), 201


@bp.route("/products", methods=["GET"])
def get_products():
    return jsonify([p.dict() for p in services.get_products()]), 200


@bp.route("/products", methods=["POST"])
@token_required
@validate()
def create_product(body: ProductCreateModel):
    if Product.query.filter_by(group_name=body.group_name, store=body.store).first():
        current_app.logger.warning(f"Product already exits {body}")
        abort(400)
    try:
        price_fetcher.get_price(body.store, body.url)
    except Exception:
        current_app.logger.warning(f"Unable to find price for url {body.url}")
        abort(400)
    p = Product()
    p.group_name = body.group_name
    p.store = body.store
    p.url = body.url
    p.price_modifier = body.price_modifier

    db.session.add(p)
    db.session.commit()

    return ProductResponseModel.from_orm(p).json(), 201

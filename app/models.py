from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from app import db


class Product(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(64), nullable=False)
    store = db.Column(db.String(64), nullable=False)
    url = db.Column(db.String(256), nullable=False)
    price_modifier = db.Column(db.String(64), nullable=False)
    price_updated_date = db.Column(db.String(16), nullable=True)
    current_price = db.Column(db.Float, nullable=True)
    price_trends = relationship("PriceTrend", lazy="joined")


class PriceSnapshot(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(16), nullable=False)
    price = db.Column(db.Float, nullable=False)


class PriceTrend(db.Model):  # type: ignore
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, ForeignKey("product.id"), nullable=False)
    date = db.Column(db.String(16), nullable=False)
    price = db.Column(db.Float, nullable=False)

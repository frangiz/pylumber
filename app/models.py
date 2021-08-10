from app import db
from datetime import datetime


def to_dict(self):
    return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

class PricedProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(16), nullable=False)
    source = db.Column(db.String(64), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False)

PricedProduct.to_dict = to_dict
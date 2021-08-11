from app import db


def to_dict(self):
    return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

class PricedProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(16), nullable=False)
    group_name = db.Column(db.String(64), nullable=False)
    source = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(128), nullable=False)
    url = db.Column(db.String(256), nullable=False)
    price = db.Column(db.Float, nullable=False)

PricedProduct.to_dict = to_dict
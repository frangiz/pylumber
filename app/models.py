from app import db


def to_dict(self):
    return {c.name: getattr(self, c.name, None) for c in self.__table__.columns}

def to_dict_except(self, exclusions):
    all_attrs = {c.name: getattr(self, c.name, None) for c in self.__table__.columns}
    return {k: v for k, v in all_attrs.items() if k not in exclusions}


class PricedProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(64), nullable=False)
    store = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(128), nullable=False)
    url = db.Column(db.String(256), nullable=False)
    alt_unit_factor = db.Column(db.Float, nullable=True)

PricedProduct.to_dict = to_dict
PricedProduct.to_dict_except = to_dict_except


class PriceSnapshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    priced_product_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(16), nullable=False)
    price = db.Column(db.Float, nullable=False)

PriceSnapshot.to_dict = to_dict
PriceSnapshot.to_dict_except = to_dict_except
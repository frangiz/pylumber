from flask import Blueprint
from flask.json import jsonify
from app import db
from app.models import PricedProduct
from datetime import datetime

bp = Blueprint("api", __name__)

@bp.route("/", methods=["GET"])
def index():
    from random import randint
    pp = PricedProduct()
    pp.price = randint(100, 1000) / 10.0
    pp.name = "some name"
    pp.source = "the source"
    pp.date = datetime.utcnow().date().isoformat()

    db.session.add(pp)
    db.session.commit()

    entries = PricedProduct.query.all()
    res = [e.to_dict() for e in entries]

    return jsonify(res), 200
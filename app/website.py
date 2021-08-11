from flask import Blueprint
from app.models import PricedProduct
from flask.json import jsonify

bp = Blueprint("website", __name__)

@bp.route("/", methods=["GET"])
def index():
    entries = PricedProduct.query.all()
    res = [e.to_dict() for e in entries]

    return jsonify(res), 200
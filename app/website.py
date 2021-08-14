from flask import Blueprint
from app.api import list_priced_products

bp = Blueprint("website", __name__)

@bp.route("/", methods=["GET"])
def index():
    return list_priced_products()
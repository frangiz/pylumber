from app.services import get_priced_products
from flask import Blueprint, render_template

bp = Blueprint("website", __name__)

@bp.route("/", methods=["GET"])
def index():
    with open("version.txt", "r") as f:
        version = f.readline().strip()
    return render_template("main.html", groups=get_priced_products(), version=version)
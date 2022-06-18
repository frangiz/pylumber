from itertools import groupby
from operator import attrgetter

from natsort import natsorted

from app.models import Product

from app.resources import ProductGroupResponseModel, ProductResponseModel
from typing import List


def get_products() -> List[ProductGroupResponseModel]:
    entries: List[Product] = Product.query.order_by(Product.group_name, Product.current_price).all()

    res = [
        ProductGroupResponseModel(group_name=k, products=[ProductResponseModel.from_db_product(e) for e in g])
        for k, g in groupby(entries, attrgetter("group_name"))
    ]
    return natsorted(res, key=lambda g: g.group_name)

from datetime import datetime, date

from pydantic import BaseModel, validator

from typing import List

from app.models import PriceTrend, Product


class PydanticDictIsoFormat(BaseModel):
    def dict(self, **kwargs):
        output = super().dict(**kwargs)
        for k,v in output.items():
            if isinstance(v, date):
                output[k] = v.isoformat()
        return output


class PriceCreateModel(BaseModel):
    price: float
    date: str

    @validator("date")
    def date_must_be_isoformat(cls, value):
        datetime.strptime(value, "%Y-%m-%d")
        return value


price_modifiers = {
    "divide_by_3dot6": lambda p: p / 3.6,
    "divide_by_4": lambda p: p / 4.0,
    "none": lambda p: p,
}


class ProductCreateModel(BaseModel):
    group_name: str
    store: str
    url: str
    price_modifier: str

    @validator("price_modifier")
    def price_modifier_must_be_known(cls, value):
        if value in price_modifiers:
            return value
        raise ValueError("Modifier not known")


class PriceTrendResponseModel(PydanticDictIsoFormat):
    date: date
    price: float

    @staticmethod
    def from_db_price_trend(trend: PriceTrend) -> "PriceTrendResponseModel":
        return PriceTrendResponseModel(date = trend.date, price=trend.price)


class ProductResponseModel(PydanticDictIsoFormat):
    current_price: float
    id: int
    price_modifier: str
    price_trends: List[PriceTrendResponseModel]
    price_updated_date: date
    store: str
    url: str

    @staticmethod
    def from_db_product(product: Product) -> "ProductResponseModel":
        return ProductResponseModel(
            current_price=product.current_price,
            id=product.id,
            price_modifier=product.price_modifier,
            price_trends=[PriceTrendResponseModel.from_db_price_trend(pt) for pt in product.price_trends],
            price_updated_date=product.price_updated_date,
            store = product.store,
            url = product.url
        )


class ProductGroupResponseModel(BaseModel):
    group_name: str
    products: List[ProductResponseModel]
from pydantic import BaseModel, validator
from datetime import datetime


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

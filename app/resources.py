from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, validator


class PydanticDictIsoFormat(BaseModel):
    def dict(self, **kwargs):
        output = super().dict(**kwargs)
        for k, v in output.items():
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

    class Config:
        orm_mode = True


class ProductResponseModel(PydanticDictIsoFormat):
    current_price: Optional[float]
    id: int
    price_modifier: str
    price_trends: List[PriceTrendResponseModel]
    price_updated_date: Optional[date]
    store: str
    url: str

    class Config:
        orm_mode = True


class ProductGroupResponseModel(BaseModel):
    group_name: str
    products: List[ProductResponseModel]

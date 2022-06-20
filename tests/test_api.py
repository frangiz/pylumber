from pathlib import Path

import pytest
from flask import url_for

from app import create_app, db
from app.resources import PriceCreateModel, ProductCreateModel, ProductResponseModel
from config import Config, basedir


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(Path(basedir, "test_pylumber.db"))
    SENTRY_SDK_DSN = None
    ACCESS_TOKENS_FILENAME = "test_access_tokens.txt"


AUTH_TEST_TOKEN = "MY-TEST-TOKEN"


@pytest.fixture(scope="module")
def app():
    return create_app(TestConfig)


def setup_module(module):
    Path(TestConfig.ACCESS_TOKENS_FILENAME).write_text(AUTH_TEST_TOKEN)


def teardown_module(module):
    Path(TestConfig.ACCESS_TOKENS_FILENAME).unlink()
    Path(basedir, "test_pylumber.db").unlink()


def setup_function(function):
    db.create_all()


def teardown_function(function):
    db.session.remove()
    db.drop_all()


def add_basic_product(client, mocker) -> ProductResponseModel:
    mocker.patch("app.price_fetcher.get_price", return_value=42.0)

    product = ProductCreateModel(
        group_name="my_group", store="the_store", url="some_url", price_modifier="none"
    )

    resp = client.post(
        url_for("api.create_product"),
        json=product.dict(),
        headers={"access-token": AUTH_TEST_TOKEN},
    )
    assert resp.status_code == 201
    return ProductResponseModel.parse_raw(resp.text)


def test_get_products_with_no_products_returns_empty_result(client):
    res = client.get(url_for("api.get_products"))
    assert res.json == []
    assert res.status_code == 200


def test_can_crate_basic_product(client, mocker):
    add_basic_product(client, mocker)

    res = client.get(url_for("api.get_products"))
    assert res.json == [
        {
            "group_name": "my_group",
            "products": [
                {
                    "current_price": None,
                    "id": 1,
                    "price_modifier": "none",
                    "price_trends": [],
                    "price_updated_date": None,
                    "store": "the_store",
                    "url": "some_url",
                }
            ],
        }
    ]
    assert res.status_code == 200


def test_can_add_first_price_snapshot_basic_product(client, mocker):
    product = add_basic_product(client, mocker)

    new_price = PriceCreateModel(price=42.0, date="2022-06-20")
    resp = ProductResponseModel.parse_raw(
        client.post(
            url_for("api.create_price", id=product.id),
            json=new_price.dict(),
            headers={"access-token": AUTH_TEST_TOKEN},
        ).text
    )

    assert resp.current_price == 42.0
    assert resp.price_updated_date.isoformat() == "2022-06-20"
    assert resp.price_trends[0].price == 42.0
    assert resp.price_trends[0].date.isoformat() == "2022-06-20"

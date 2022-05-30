import pytest
from flask import url_for

from app import create_app, db
from app.resources import ProductCreateModel
from config import Config
from pathlib import Path


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_pylumber.db"
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


def setup_function(function):
    db.create_all()


def teardown_function(function):
    db.session.remove()
    db.drop_all()


def test_get_products_with_no_products_returns_empty_result(client):
    res = client.get(url_for("api.get_products"))
    assert res.json == []
    assert res.status_code == 200


def test_can_crate_basic_product(client, mocker):
    mocker.patch("app.price_fetcher.get_price", return_value=42.0)

    product = ProductCreateModel(
        group_name="my_group", store="the_store", url="some_url", price_modifier="none"
    )
    res = client.post(
        url_for("api.create_product"),
        json=product.dict(),
        headers={"access-token": AUTH_TEST_TOKEN},
    )
    assert res.status_code == 201

    res = client.get(url_for("api.get_products"))
    assert res.json == [
        {
            "group_name": "my_group",
            "products": [
                {
                    "current_price": None,
                    "id": 1,
                    "price_modifier": "none",
                    "price_updated_date": None,
                    "store": "the_store",
                    "url": "some_url",
                }
            ],
        }
    ]
    assert res.status_code == 200

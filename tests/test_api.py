import pytest
from flask import url_for

from app import create_app, db
from app.resources import ProductCreateModel
from config import Config

import json


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_pylumber.db"
    SENTRY_SDK_DSN = None


@pytest.fixture(scope="module")
def app():
    return create_app(TestConfig)


def setup_function(function):
    db.create_all()


def teardown_function(function):
    db.session.remove()
    db.drop_all()


def test_get_products__with_no_products_returns_empty_result(client):
    res = client.get(url_for("api.get_products"))
    assert res.json == []
    assert res.status_code == 200


# TODO: Handle price fetcher logic.
def test_can_crate_basic_product(client):
    product = ProductCreateModel(group_name="my_group", store="the_store", url="some_url", price_modifier="none")
    res = client.post(url_for("api.create_product"), json=product.dict(), headers={"access-token": "foo"})
    assert res.status_code == 201

    res = client.get(url_for("api.get_products"))
    assert len(res.json) == 1
    assert res.status_code == 200
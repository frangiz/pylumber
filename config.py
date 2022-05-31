import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".flaskenv"))


class Config(object):
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "pylumber.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FLASK_ENV = os.environ.get("FLASK_ENV")

    SENTRY_SDK_DSN = os.environ.get("SENTRY_SDK_DSN")

    ACCESS_TOKENS_FILENAME = "access_tokens.txt"

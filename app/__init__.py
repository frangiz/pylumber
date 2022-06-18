import logging
from pathlib import Path

import sentry_sdk
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sentry_sdk.integrations.flask import FlaskIntegration

from common.price_fetcher import PriceFetcher
from config import Config

db = SQLAlchemy()
migrate = Migrate()
price_fetcher = PriceFetcher()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    sentry_sdk.init(
        dsn=app.config["SENTRY_SDK_DSN"],
        integrations=[FlaskIntegration()],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,
        environment=app.config["FLASK_ENV"],
    )

    # setup logging
    app_path = Path(__file__).parent.parent.absolute()
    Path(app_path, "logs").mkdir(exist_ok=True)

    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    handler = logging.FileHandler(
        Path(app_path, "logs", "pylumber.log"), encoding="utf-8"
    )
    handler.formatter = formatter

    # The werkzeug logger is available in dev mode, so grab that one
    # and add the handler to it.
    logger = logging.getLogger("werkzeug")
    if logger.hasHandlers():
        logger.addHandler(handler)
    else:
        app.logger.addHandler(handler)

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

    from app.website import bp as website_bp

    app.register_blueprint(website_bp)

    from app.api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")

    return app


from app import models  # noqa: E402,F401

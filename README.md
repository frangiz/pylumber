# pylumber

## Getting started
* Make sure to have at least Python 3.9 installed.
* Install dependencies with `pip install -r requirements.txt`
* Setup the database for the first time with `flask db upgrade`
* Create a file named `access_tokens.txt`. This file contains the access tokens in order to use some of the API endpoints. The tokens are line separated.
* Seed the database by posting a few products to /api/products
* Run the server in debug mode with `export FLASK_ENV=development` and then start it with `flask run`
* In order to add price snapshots to the products, the collector.py need to be run. If the collector should be able to send emails, then the config file `collector_cnf.json` need to exist and be configured.
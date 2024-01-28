from services.recent_changes import *
import importlib
from os import environ

module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

@app.route("/recent_changes")
def get_all_products_with_price_change():
    changes = get_all_products_with_price_change_service()
    if changes:
        return changes


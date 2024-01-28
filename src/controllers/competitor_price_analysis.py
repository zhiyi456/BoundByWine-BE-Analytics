from flask import jsonify
import importlib
from os import environ

from services.competitor_price_analysis import *

module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

# does not work when deployed (ERROR: 500 Internal Server Error)
@app.route('/get_products_with_price_deviations')
def get_products_with_price_deviations():
    result = get_top_products_with_price_deviations()
    if bool(result) != False: # result is not an empty list
        return jsonify(
            {
                "code": 200,
                "data": result,
                "message": "There are products with price deviations."
            }
        )
    return jsonify(
            {
                "code": 404,
                "data": result,
                "message": "Unable to find products with price deviations."
            }
        )
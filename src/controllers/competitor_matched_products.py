from flask import jsonify
from services.competitor_matched_products import *
import importlib
from os import environ

module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

@app.route("/matched_products/search/<string:search_query>", methods=['GET'])
def get_matched_products_by_name(search_query):
    product_list = get_matched_products_by_name_service(search_query)
    if len(product_list) != 0:
        return jsonify(
            {
                "code": 200,
                "data": {
                    "matched_competitor_products": product_list
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no matched products for the string " + search_query
        }
    )
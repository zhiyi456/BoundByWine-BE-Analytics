from flask import jsonify
from services.bbw_product import *
import importlib
from os import environ

module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

@app.route("/shopify_products_to_db")
def get_all_bbw_product_shopify():
    result = get_products_from_shopify()
    if bool(result) == False: # no errors - result is an empty list
        return jsonify(
            {
                "code": 200,
                "message": "All products from shopify have been successfully created."
            }
        )
    return jsonify(
            {
                "code": 404,
                "errors": result,
                "message": "List of bbw_product that can't be inserted into the db"
            }
        )
    
@app.route('/products', methods=['GET'])
def get_products():
    bbw_product_list = get_all_bbw_product_service()
    if bool(bbw_product_list):
        return jsonify(
            {
                "code": 200,
                "data": {
                    "product_listing": bbw_product_list
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no BBW products."
        }
    )

@app.route("/products/search/<string:search_query>", methods=['GET'])
def get_products_by_name(search_query):
    product_list = get_products_by_name_service(search_query) # search bar function - %LIKE%
    if len(product_list) != 0:
        return jsonify(
            {
                "code": 200,
                "data": {
                    "products_BBW": product_list
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no BBW products for the string " + search_query
        }
    )
from flask import jsonify
from models.matched_product_listing import *
from os import environ

module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

def get_all_products_with_price_change_service():
    try:
        changes = get_product_with_price_change()
        if changes:
            return jsonify(
                {
                    "code": 200,
                    "data": {
                        "recent_changes_price": changes
                    }
                }
            )
        return jsonify(
            {
                "code": 404,
                "message": "There are no changes."
            }
        ), 404
    except:
        return jsonify(
            {
                "code": 500,
                "message": 'Internal server error' 
            }
        ), 500


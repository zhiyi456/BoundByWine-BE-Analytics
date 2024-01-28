import json
from os import environ
import importlib
from services.new_webscrape import *
from models.webscrape_param import *
from services.bbw_match_orders import *
from services.bbw_orders_with_metafields import *

module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

@app.route("/")
def homepage():
    return "Hello World"

# does not work when deployed (ERROR: 500 Internal Server Error)
@app.route('/test_metafields')
def test_metafields():
    
    result, errors = get_metafields_for_all_orders()

    """ if result:
        return jsonify(
            {
                "code": 404,
                "message": "We found nothing."
            }
        ) """
    return jsonify(
        {
            "message": "Test.",
            "data": result,
            "errors": errors
        }
    )

# does not work when deployed (ERROR: 500 Internal Server Error)
@app.route('/test_get_metafields_json_for_slides')
def test_get_metafields_json_for_slides():
    lst_ids = [
        8596545274175, 8596232798527, 8596550517055, 8596101726527
    ]
    metafields_from_shopify, errors = get_metafields(lst_ids)
    
    metafields = []
    for pdt in metafields_from_shopify:
        temp = {}
        for field in pdt:
            temp[field['key']] = field['value']
        metafields.append(temp)

    with open("full_metafields.json", "w") as file: 
            json.dump(metafields, file)

    return jsonify(
        {
            "metafields": metafields,
            "errors": errors,
        }
    )

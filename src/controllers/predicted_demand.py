from flask import jsonify
import importlib
from os import environ

from services.predicted_demand import *
from models.bbw_match_orders import *

module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

@app.route('/get_demand_predictions/<string:product_name>', methods=['GET'])
def get_demand_predictions(product_name):
    historical_demand, predicted_demand, errors = run_main_demand_prediction_pipeline(product_name)
    if predicted_demand or historical_demand:
    
        return jsonify(
            {
                'code': 200,
                'data': {
                    "historical_demand": historical_demand,
                    "predicted_demand": predicted_demand
                },
                'errors': errors
            }
        )
    return jsonify(
        {
            'code': 404,
            'data': {
                "historical_demand": historical_demand,
                "predicted_demand": predicted_demand
            },
            'errors': errors
        }
    )


""" # some products to test
missing metafields: # to test ARIMA-SARIMAX
    8596224737599 - get_demand_predictions/Lagertal%20Holunder%20Goldtraminer%202020
    8596373963071 - get_demand_predictions/Stolpman%20Love%20You%20Bunches%202021
    8596571783487 - get_demand_predictions/Zenato%20Lugana%20DOC%20San%20Benedetto%202021

has all metafields: # to test MLR
    8596329922879 - get_demand_predictions/Couvent%20Rouge%20Rosé%202020 """ # has historical_demand
    # - get_demand_predictions/Rara%20Neagră%20de%20Purcari%202020 (to test for CSV orders, but no historical demand in shopify store)

# def main_demand_prediction_pipeline(product_name):
#     historical_demand = []
#     predicted_demand = []
    
#     # get product ID
#     bbw_product = get_shopify_product_by_product_name(product_name)
#     if bbw_product['code'] == 404:
#         return [], [], "There is no such product. Try refreshing database to get all Shopify products or double check the product name entered."
#     else:
#         bbw_product = bbw_product['data']
#         # get metafields
#         product_metafields, errors = get_metafields([bbw_product['shopify_product_id']])
#         product_metafields = product_metafields[0]

#         for key, value in product_metafields.items():
#             bbw_product[key] = value

#         # check if all metafields have values
#         check = check_if_relevant_metafields_exist_for_demand_pred(product_metafields)

#     """ if check == True:
#         return bbw_product, [], errors
#         pass # do MLR """

#     #if check == False: 
#     try:
#         historical_demand, predicted_demand = load_arima_sarimax_and_get_demand_prediction(product_name)
#     except Exception as e:
#         print(e)
#         errors.append(str(e))
#         historical_demand = get_orders_by_product_name(product_name)
#         predicted_demand = []

#     return historical_demand, predicted_demand, errors


""" @app.route("/run_predicted_demand_model/<string:product_name>", methods=['GET'])
def run_predicted_demand_model(product_name):
    # historical_demand, predicted_demand = run_main_demand_prediction_pipeline(product_name) # use this once pipeline is ready
    historical_demand, predicted_demand = load_arima_sarimax_and_get_demand_prediction(product_name) # old function

    if predicted_demand:
        post_prediction_to_db(predicted_demand)
        return jsonify(
            {
                "code": 200,
                "data": {
                    "historical_demand": historical_demand,
                    "predicted_demand": predicted_demand
                },
                "message": "Predicted demand for this product has also been successfully stored into the database."
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": 'No predicted demand history for product named ' + str(product_name) 
        }
    ), 404
 """

""" 
@app.route('/kevan_testing')
def kevan_testing():
    
    result = train_mlr_demand_prediction()
    # result, result2 = load_mlr_and_get_demand_prediction()

    return jsonify(
        {
            "code": 200,
            "message": result
        }
    ) """
from flask import jsonify
import importlib
from os import environ
import pandas as pd
from models.bbw_match_orders import *

module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

# does not work when deployed (ERROR: 500 Internal Server Error)
@app.route('/get_total_orders_from_shopify')
def get_total_orders_from_shopify():
    orders = get_all_bbw_orders()
    if len(orders) == 0:
        return jsonify(
            {
                "code": 404,
                "data": orders,
                "message": "No historical orders were found."
            }
        ), 404

    df = pd.DataFrame(orders)
    df['order_date'] = df['order_datetime'].dt.date
    df['order_date'] = df['order_date'].astype(str)
    data = df.groupby('order_date')['item_quantity'].sum()
    data = data.to_dict()

    return jsonify(
        {
            "code": 200,
            "data": data,
        }
    ), 200


@app.route('/get_total_orders_from_csv')
def get_total_orders_from_csv():
    df = pd.read_csv('datasets/cleaned_orders.csv')
    data = df.groupby('order_date')['item_quantity'].sum()
    data = data.to_dict()
    
    if len(data) > 0:
        return jsonify(
            {
                "code": 200,
                "data": data
            }
        ), 200
    else:
        return jsonify(
            {
                "code": 404,
                "data": data,
                "message": "No historical orders were found."
            }
        ), 400
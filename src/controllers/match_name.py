from flask import jsonify

from services.new_name_match import *
from models.bbw_product import *

import importlib
import pandas as pd

from os import environ

module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

# does not work when deployed (ERROR: 500 Internal Server Error)
@app.route('/test_name_matching')
def test_name_matching():
    df = pd.read_csv('datasets/sample_supplier_products.csv')
    
    supplier_pdts = df.values.tolist()

    bbw_products = get_all_bbw_product_model()
    bbw_products = pd.DataFrame.from_records(bbw_products)
    bbw_products_dict = bbw_products.to_dict()['bbw_product_name']

    final = []
    for product in supplier_pdts:
        product_name = product[1]
        matches = [product_name]
        temp = fuzzy_wuzzy_name_matcher(product_name, bbw_products_dict)
        if temp == '':
            matches.append('')
            continue
        else:
            matches.append(temp)
        final.append(matches)

    print(len(final))
        
    return jsonify(
        {
            "code": 200,
            "data": final,

        }
    )
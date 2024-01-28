import shopify
import pandas as pd
import time
from os import environ

from models.bbw_product_metafields import *
from models.bbw_match_orders import *
from services.bbw_product import *
from models.bbw_product import *
from services.bbw_match_orders import *

module = importlib.import_module(environ.get("STAGE_ENV"))

client = module.client

def get_metafields_for_all_orders():
    # get orders from SQL database -> to dataframe
    get_orders_from_shopify()
    orders = pd.DataFrame(get_all_bbw_orders())

    # unique IDs that appear >= num times -> minimise duplicate calls to get metafield
    ids = orders['shopify_product_id'].value_counts().loc[lambda x: x >= 1].index

    metadata, errors = get_metafields(ids)
    metadata_df = pd.DataFrame(metadata)

    matched_metafields = orders.merge(metadata_df, on='shopify_product_id', how='left')
    result = matched_metafields.to_dict(orient='records')

    return result, errors # return result: dictionary


def get_metafields(list_of_shopify_pdt_ids):
    start_shopify_session()
    errors = []
    metadata = []

    for i in range(len(list_of_shopify_pdt_ids)):
        shopify_product_id = str(int(list_of_shopify_pdt_ids[i]))
        temp = get_metafield_by_id(shopify_product_id)

        if temp == {}: # db does not contain this product's metafields
            if i%5 == 4:
                time.sleep(2)
            metafields = client.get('products/' + shopify_product_id + '/metafields.json?fields=key,value').json()['metafields']
            temp = post_metafields_to_db(metafields, shopify_product_id)
            if temp['code'] == 500: # errors posting to db
                errors.append(temp)

        metadata.append(temp['data'])
    
    shopify.ShopifyResource.clear_session() # clear shopify session
    return metadata, errors # returns a list of dictionaries
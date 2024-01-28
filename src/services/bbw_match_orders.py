import shopify
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
#import time
from os import environ
from datetime import datetime

from models.bbw_match_orders import *
from services.bbw_product import *
from services.new_name_match import *

module = importlib.import_module(environ.get("STAGE_ENV"))

client = module.client

def get_orders_from_shopify(): # to get orders and then upload to DB

    latest_order_in_db = get_latest_order()
    
    start_shopify_session()
    errors = []

    orders_df = pd.DataFrame.from_records(handle_shopify_orders(latest_order_in_db))
    if len(orders_df) == 0:
        return pd.DataFrame(), errors

    # get bbw products & clean dataframe
    products_df = pd.DataFrame(get_all_bbw_product_service())
    products_df = products_df[['shopify_product_id','bbw_product_name','product_type','shopify_sku']]
    products_df = products_df.drop_duplicates(subset=['bbw_product_name'])

    matched_orders = match_orders_to_products(orders_df, products_df)
    matched_orders_dict = matched_orders.to_dict('records')

    for order in matched_orders_dict:
        res = post_order_to_db(order)
        if res['code'] != 201: # posting was unsuccessful
            errors.append(res)

    return matched_orders_dict, errors

def handle_shopify_orders(latest_datetime):
    orders = []
    resource_type = shopify.Order
    resource_count = resource_type.count()

    if resource_count > 0:
        page = resource_type.find()
        for odr in page:
            temp = extract_order_info(odr.to_dict(), latest_datetime)
            if temp != False:
                orders.extend(temp)
        while page.has_next_page():
            page = page.next_page()
            for odr in page:
                temp = extract_order_info(odr.to_dict(), latest_datetime)
                if temp != False:
                    orders.extend(temp)
    return orders

def extract_order_info(order, latest_datetime):
    result = []
    order_datetime = order["created_at"]
    
    if len(latest_datetime) > 0:
        latest_datetime = latest_datetime['data']['order_datetime']
        
        # handle datetime from shopify -> currently a string
        temp_order_datetime = order_datetime.split('+')[0]
        temp_order_datetime = datetime.strptime(temp_order_datetime, "%Y-%m-%dT%H:%M:%S")
        
        check = bool(temp_order_datetime > latest_datetime)
    else:
        check = True # no orders in DB yet

    if check == True:
        if bool(order.get('line_items'))==False: # no products bought
            return False

        lineitems = order["line_items"]
        
        if bool(order.get('checkout_token')): 
            checkout_token = order["checkout_token"]
        else:
            checkout_token = np.nan
        
        for item in lineitems:
            if bool(item.get('title'))==False:
                continue
            if check_products_to_exclude(item['title'], '') == False:
                continue
            if item['sku'] == '':
                sku = np.nan
            else:
                sku = item['sku']
            if bool(item['product_id'])==False: # no product id specified
                pid = np.nan
            else:
                pid = str(int(item['product_id']))

            result.append({
                "checkout_token": checkout_token,
                "order_datetime": order_datetime,
                "shopify_sku": sku,
                "pdt_id": pid,
                "item_name": item["title"],
                "item_qty": item["quantity"],
                "price": item["price"],
            })
        return result
    return False


def match_orders_to_products(orders_df, bbw_products):
    # merge product & order data -> find sku matches -> get shopify product ID
    merged = pd.merge(orders_df.dropna(subset=['shopify_sku']),bbw_products,how='left',on='shopify_sku')
    merged['pdt_id'].fillna(merged['shopify_product_id'],inplace=True)

    # append the rest of the orders without sku matches
    temp = orders_df[(pd.isna(orders_df['shopify_sku'])) | (orders_df['shopify_sku']=='')]
    merged = pd.concat([merged,temp])

    # merge product & order data -> find exact product name matches -> get shopify product ID
    bbw_products = bbw_products[['shopify_product_id','bbw_product_name','product_type']]
    merged = orders_df.merge(bbw_products, left_on='item_name', right_on='bbw_product_name', how='left')

    # separating matches & non-matches
    dropped = merged[(pd.isna(merged['pdt_id'])) | (merged['pdt_id']=='')]
    merged = merged.dropna(subset=['pdt_id'])

    temp = dropped.copy()
    for index, row in dropped.iterrows():
        new_pdt_name = regex_remove_patterns(row['item_name'])
        pdt, pid, ptype = get_match_fuzzywuzzy(new_pdt_name, bbw_products)
        if pdt != False:
            temp.at[index, 'bbw_product_name'] = pdt
            temp.at[index, 'shopify_product_id'] = pid
            temp.at[index, 'product_type'] = ptype
    
    if len(temp) != temp['shopify_product_id'].isna().sum(): # there are shopify pdt IDs
        temp['pdt_id'].fillna(temp['shopify_product_id'], inplace=True)
    temp = temp.dropna(subset=['pdt_id'])

    final = pd.concat([merged,temp])
    return final.drop(columns=['shopify_product_id','bbw_product_name','shopify_sku'])


def get_match_fuzzywuzzy(pdt, bbw_pdts):
    bbw_products_dict = bbw_pdts.set_index('bbw_product_name').to_dict('index')

    edited_name = regex_remove_patterns(pdt)
    substrings = edited_name.split(' ')

    possible_matches = []
    for substring in substrings:
        if substring != '':
            possible_matches += [key for key in bbw_products_dict.keys() if substring in key]
    unique_possible_matches = set(possible_matches)

    best_match = ''
    highest_score = 0
    threshold = 75

    for bbw_wine_name in list(unique_possible_matches):
        score = fuzz.ratio(pdt.lower(), bbw_wine_name.lower())
        if score >= threshold:
            best_match = bbw_wine_name
            highest_score = score
        if score > 95:
            best_match = bbw_wine_name
            highest_score = score
            break
    if highest_score == 0:
        return False, False, False
    
    shopify_product_id = bbw_products_dict[best_match]['shopify_product_id']
    product_type = bbw_products_dict[best_match]['product_type']
    return best_match, shopify_product_id, product_type

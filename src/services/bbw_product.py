import shopify
from os import environ
from sqlalchemy import and_
from models.bbw_product import *

def get_all_bbw_product_service():
    bbw_product_list = get_all_bbw_product_model()
    if bbw_product_list:
        return bbw_product_list
    else: # if no products, get products from shopify.
        get_products_from_shopify()
        bbw_product_list = get_all_bbw_product_model()
        if bbw_product_list:
            return bbw_product_list
    return []

def get_products_by_name_service(search_query): # search bar function
    search_terms = search_query.split()
    conditions = [BBWProduct.bbw_product_name.like('%'+term+'%') for term in search_terms]
    product_list = BBWProduct.query.filter(and_(*conditions)).all()
    
    if product_list:
        return [product.json() for product in product_list]
    return []

def start_shopify_session():
    key = environ.get("SHOPIFY_API_KEY")
    store = environ.get("STORE")
    url = str(store) + ".myshopify.com"

    session = shopify.Session(url, '2022-07', key) # 2022-07 is the shopify api version
    shopify.ShopifyResource.activate_session(session)

def get_products_from_shopify():
    start_shopify_session()
    truncate_table()
    resource_type = shopify.Product
    resource_count = resource_type.count()
    errors = []

    if resource_count > 0:
        page = resource_type.find()
        for pdt in page:
            temp, html, image, sku, price = get_products_details_for_each_shopify_product(pdt)
            if temp != False:
                result = post_product_to_db(temp, html, image, sku, price)
                if result != True:
                    errors.append(result)

        while page.has_next_page():
            page = page.next_page()
            for pdt in page:
                temp, html, image, sku, price = get_products_details_for_each_shopify_product(pdt)
                if temp != False:
                    result = post_product_to_db(temp, html, image, sku, price)
                    if result != True:
                        errors.append(result)

    shopify.ShopifyResource.clear_session() # clear shopify session
    return errors


def check_products_to_exclude(product_name, product_type):
    item_names_to_exclude = [
        'tasting', 'workshop', 'event', 'bundle', 'subscription', 'venue booking', 'engagement', 'jancis', 'zalto', 
        'outstanding balance', 'cheese', 'wine addict', 'wine virgin', 'wine nut', 'shopee', 'crackers', 'chip', 
        'pretzel', 'chili', 'nuts', 'harvest box', 'coconut water', 'tonic water', 'lavender water', 'sparkling water', 
        'dash water', 'fiji water', 'all shook up', 'mezete', 'dinner', 'catering', 'service', 'barbecue', 'barbeque',
        'charcuterie', 'platter', 'decanter', 'case of', 'networking', 'shiok', 'cappuccino', 'latte', 
        'soda', 'sparkling juice', 'hamper', 'zieher', 'gift card', 'gift set','hunny bunny', 'sampl', 'misc', 
        'combo', 'pax', 'pizza', 'bbq', 'glassware', 'snowboard', 'chocolate', 'gift wrap', 'bottled water', 
        "riedel 'vinum'", "riedel 'extreme'", 'riedel winewings', 'wine ambassador series', 'wine stoppers', 'pasta', 
        'tomato sauce', 'gift message', 'olive oil', 'magazine'
    ]
    for x in item_names_to_exclude:
        if x in product_name.lower():
            return False # false = don't keep product 
    product_types_to_exclude = [
        'Chips', 'Coffee', 'Dips & Spreads', 'Event Tickets', 'Gift & Hamper', 'Gift Message', 'Snack Foods',
        'Stemware', 'Wine Aerators', 'Water', 'Vitamins & Supplements', 'Candy & Chocolate', 'Bottle Stoppers & Savers'
    ]
    if product_type == '':
        return True # true = keep product
    
    if product_type in product_types_to_exclude:
        return False # false = don't keep product
    
    return True # true = keep product


def get_products_details_for_each_shopify_product(pdt):
    temp = pdt.to_dict()
    if check_products_to_exclude(temp['title'], temp['product_type']) == False:
        return False,False,False,False,False
    if bool(temp.get('body_html')):
        start = temp['body_html'].find('<p>')
        end = temp['body_html'].find('</p>')
        html = temp['body_html'][start+3:end]
    else: 
        html = ""
    if bool(temp.get('variants')):
        sku = temp['variants'][0]['sku']
        price = float(temp['variants'][0]['price'])
    else: 
        sku = ""
        price = 0
    if bool(temp.get('image')):
        image = temp['image']['src']
    else: 
        image = ""

    return temp, html, image, sku, price
from sqlalchemy import and_
from models.matched_product_listing import *
from os import environ

module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

def get_matched_products_by_name_service(search_query): # search bar function
    print(1234, search_query)
    search_terms = search_query.split()
    conditions = [MatchedProductListing.bbw_product_name.like('%'+term+'%') for term in search_terms]
    product_list = MatchedProductListing.query.filter(and_(*conditions)).all()
    
    if product_list:
        return [product.json() for product in product_list]
    return []

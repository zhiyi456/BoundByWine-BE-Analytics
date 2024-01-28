from datetime import datetime
from flask import jsonify

from services.new_name_match import *
from models.webscrape_param import *
from models.matched_product_listing import *
from models.unmatched_product_listing import *
from services.bbw_product import *
from services.new_webscrape import *
from models.scrape_logs import *
import importlib
from os import environ

module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

# get json from user input, post method
# new etl pipeline workflow
@app.route("/webscrapetest")
def test_route():
    return "test route"

@app.route("/webscrape/<string:supplier_name>")
def webscraping(supplier_name):
    # should return a json file containing the params from the website table
    # e.g {
    #    "supplier_name": "vivino",
    #    "website_product_url": "https://www.vivino.com/explore?e=eJzLLbI1VMvNzLM1Nl
    #    "params": "...",
    #}
    webscrape_params = get_supplier_webscrape_params(supplier_name) # call the function from service/webscrape.py file
    
    print("===========================================get webscrape params service function==============================================")
    print(webscrape_params)
    if webscrape_params == {}:
        return "Something went wrong when retrieving webscrape params from " + supplier_name + "or supplier name does not exist in webscrape_params table"
    webscrape_datetime = datetime.now()

    if supplier_name == "wine.delivery":
        data_df = scrape_wine_delivery(webscrape_params) # return a dictionary or dataframe and called from the service/webscrape.py file

    if supplier_name == "vivino":
        data_df = scrape_vivino(webscrape_params) # return a dictionary or dataframe and called from the service/webscrape.py file

    if supplier_name == "pivene":
        data_df = scrape_pivene(webscrape_params) # return a dictionary or dataframe and called from the service/webscrape.py file

    if supplier_name == "twdc":
        data_df = scrape_twdc(webscrape_params) # return a dictionary or dataframe and called from the service/webscrape.py file

    if supplier_name == "winedelivery":
        data_df = scrape_winedelivery(webscrape_params) # return a dictionary or dataframe and called from the service/webscrape.py file

    if supplier_name == "winelistasia":
        data_df = scrape_winelistasia(webscrape_params) # return a dictionary or dataframe and called from the service/webscrape.py file

    if supplier_name == "winesonline":
        data_df = scrape_winesonline(webscrape_params) # return a dictionary or dataframe and called from the service/webscrape.py file
    
    if supplier_name == "wineswholesales":
        data_df = scrape_wineswholesale(webscrape_params) # return a dictionary or dataframe and called from the service/webscrape.py file

    
    data_dict = data_df.to_dict("records")

    if not data_dict:
        return "Something went wrong when webscraping" + webscrape_params["supplier_name"] + "website"
    
    print("===========================================get all bbw product service function==============================================")
    bbw_products = pd.DataFrame.from_records(get_all_bbw_product_service()) #call the function from service/bbw_product.py, return a dataframe
    bbw_products_dict = bbw_products.to_dict()["bbw_product_name"] #return a list of bbw_product_name
    
    # Check the entire scraped data to see if product alr exist in matched_product_listing or unmatched_product_listing,
    # Else, check if product name can be matched with bbw_product_name, then create new product in matched_product_listing or unmatched_product_listing
    
    
    for data_row in data_dict:
        # sample data_row output {'Product_Name': 'Black Shiraz', 'Supplier_Name': 'Vivino', 'Product_In_Stock': True, 'Scraped_Data_Old_Price': 0.0, 'Scraped_Data_New_Price': 169.0}
        print("\n===========================================check if product name and supplier name exist in matched or unmatched product listing==============================================\n")
        # print(data_row)
        #check if supplier original name is inside matched_product_listing or unmatched_product_listing
        supplier_original_product_name = data_row["Product_Name"]
        #if yes, then update the matched_product_listing or unmatched_product_listing
        if check_if_product_name_and_supplier_name_exist_matched(supplier_original_product_name, supplier_name): #return boolean value
            #update the matched_product_listing (directly call the function from models/matched_product_listing.py)
            update_matched_product_listing(supplier_original_product_name, supplier_name, data_row["Scraped_Data_New_Price"])


        elif check_if_product_name_and_supplier_name_exist_unmatched(supplier_original_product_name, supplier_name):
            #update the matched_product_listing (directly call the function from models/matched_product_listing.py)
            update_unmatched_product_listing(supplier_original_product_name, supplier_name, data_row["Scraped_Data_New_Price"])

        else:
            matched_product_name = fuzzy_wuzzy_name_matcher(data_row["Product_Name"], bbw_products_dict) #call the function from service/match_name.py, return bbw_product_name or ""
            if matched_product_name == "":
                create_new_poduct_in_unmatched_product_listing(data_row["Product_Name"], supplier_name, data_row["Product_In_Stock"], data_row["Scraped_Data_New_Price"])
            else:
                create_new_poduct_in_matched_product_listing(matched_product_name, data_row["Product_Name"], supplier_name, data_row["Product_In_Stock"], data_row["Scraped_Data_New_Price"])


    # update scrape_logs table
    log = create_new_scrape_log(supplier_name, webscrape_datetime)
    if log:
        return jsonify(
        {
            "code": 400,
            "message": "Webscraping successful but an error occured when updating scrape_logs table",
        }
    )

    return jsonify(
        {
            "code": 200,
            "message": "Webscraping successful and scrape_logs table updated",
        }
    )
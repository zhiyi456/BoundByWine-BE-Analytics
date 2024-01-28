from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from os import environ
from dotenv import load_dotenv
from shopifyapi import ShopifyAPI


app = Flask(__name__)

load_dotenv()

# Remember to add/remove the app config with your php password
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get(
    'dbURL') or 'mysql+mysqlconnector://root:@localhost:3306/grapevantage_rds'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# cara
""" app.config['SQLALCHEMY_DATABASE_URI'] = environ.get(
    'dbURL') or 'mysql+mysqlconnector://root:root@localhost:8889/grapevantage_rds'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  """

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)

CORS(app)

client = ShopifyAPI(token=environ.get("SHOPIFY_API_KEY"), store=environ.get("STORE"))

import models.bbw_product
import models.bbw_product_metafields
import models.supplier
# import models.historical_demand
import models.predicted_demand
import models.scrape_logs
import models.webscrape_param
import models.schedule_params
import models.bbw_match_orders

import services.bbw_product
import services.bbw_match_orders
import services.bbw_orders_with_metafields
import services.predicted_demand
import services.scrape_logs
import services.webscrape_param
import services.schedule_params
import services.new_webscrape
import services.scheduler
import services.competitor_price_analysis
import services.competitor_matched_products

import controllers.bbw_product
import controllers.predicted_demand
import controllers.test
import controllers.scrape_logs
import controllers.match_name
import controllers.historical_demand
import controllers.webscrape_param
import controllers.schedule_params
import controllers.new_webscrape
import controllers.competitor_price_analysis
import controllers.competitor_matched_products


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(port=5000, debug=False)
    
    #app.run(port=5000, debug=True)
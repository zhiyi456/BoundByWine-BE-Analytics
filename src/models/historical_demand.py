""" from flask import jsonify
from os import environ
import importlib

app = importlib.import_module(environ.get("STAGE_ENV"))

db = app.db

class HistoricalDemand(db.Model):
    __tablename__ = 'Historical_Demand'

    Product_Name = db.Column(db.String(200), primary_key=True)
    Supplier_Name = db.Column(db.String(100), primary_key=True)
    Historical_Demand_Date = db.Column(db.Date, primary_key=True)
    Historical_Demand_Sales = db.Column(db.Integer, nullable=False)

    def __init__(self, Product_Name, Supplier_Name, Historical_Demand_Date, Historical_Demand_Sales):
        self.Product_Name = Product_Name
        self.Supplier_Name = Supplier_Name
        self.Historical_Demand_Date = Historical_Demand_Date
        self.Historical_Demand_Sales = Historical_Demand_Sales

    def json(self):
        dto = {
            'Product_Name': self.Product_Name,
            'Supplier_Name': self.Supplier_Name,
            'Historical_Demand_Date': self.Historical_Demand_Date,
            'Historical_Demand_Sales': self.Historical_Demand_Sales
        }
        return dto

@app.app.route("/historical_demand/get_all", methods=['GET'])
def get_all_historical_demand():
    historical_demand_list = HistoricalDemand.query.all()
    
    if historical_demand_list:
        return jsonify(
            {
                "code": 200,
                "data": {
                    "historical_demand": [historical_demand.json() for historical_demand in historical_demand_list]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no Historical Demand."
        }
    ), 404


def get_all_selected_product_price(product_name):
    historical_demand_list = HistoricalDemand.query.filter_by(Product_Name = product_name).all()
    if historical_demand_list:
        return jsonify(
            {
                "code": 200,
                "data": {
                    "historical_demand": [historical_demand.json() for historical_demand in historical_demand_list]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": 'No historical demand history for product named ' + str(product_name) 
        }
    ), 404 """

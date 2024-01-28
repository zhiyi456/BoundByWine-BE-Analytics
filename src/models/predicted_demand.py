""" from flask import jsonify
from os import environ
import importlib

app = importlib.import_module(environ.get("STAGE_ENV"))

db = app.db

class PredictedDemand(db.Model):
    __tablename__ = 'Predicted_Demand'

    Product_Name = db.Column(db.String(200), primary_key=True)
    Predicted_Demand_Target_Date = db.Column(db.Date, primary_key=True)
    Predicted_Demand_Prediction = db.Column(db.Integer, nullable=False)

    def __init__(self, Product_Name, Predicted_Demand_Target_Date, Predicted_Demand_Prediction):
        self.Product_Name = Product_Name
        self.Predicted_Demand_Target_Date = Predicted_Demand_Target_Date
        self.Predicted_Demand_Prediction = Predicted_Demand_Prediction

    def json(self):
        dto = {
            'Product_Name': self.Product_Name,
            'Predicted_Demand_Target_Date': self.Predicted_Demand_Target_Date,
            'Predicted_Demand_Prediction': self.Predicted_Demand_Prediction
        }
        return dto 

def get_all_predicted_demand():
    predicted_demand_list = PredictedDemand.query.all()
    
    if predicted_demand_list:
        return jsonify(
            {
                "code": 200,
                "data": {
                    "predicted_demand": [predicted_demand.json() for predicted_demand in predicted_demand_list]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no Predicted Demand."
        }
    ), 404


def get_product_predicted_demand(product_name):
    predicted_demand_list =PredictedDemand.query.filter_by(Product_Name = product_name).all()
    if predicted_demand_list:
        return jsonify(
            {
                "code": 200,
                "data": {
                    "predicted_demand": [predicted_demand.json() for predicted_demand in predicted_demand_list]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": 'No predicted demand history for product named ' + str(product_name) 
        }
    ), 404
 """
from flask import jsonify
from os import environ
import importlib

app = importlib.import_module(environ.get("STAGE_ENV"))

db = app.db

class WebscrapeParams(db.Model):
    __tablename__ = 'webscrape_params'

    supplier_name = db.Column(db.String(200), primary_key=True)
    website_url = db.Column(db.String(200))
    category = db.Column(db.String(200), nullable = True)
    country = db.Column(db.String(), nullable = True)
    region = db.Column(db.String(200), nullable = True) #don't add this also (more consistent)
    rating = db.Column(db.String(200), nullable = True) #don't add this also


    def __init__(self, supplier_name, website_url, category, country, region, rating):
        self.supplier_name = supplier_name
        self.website_url = website_url
        self.category = category
        self.country = country
        self.region = region
        self.rating = rating

    def json(self):
        dto = {
            'supplier_name': self.supplier_name,
            'website_url': self.website_url,
            'category': self.category,
            'country': self.country,
            'region': self.region,
            'rating': self.rating,
        }
        return dto 

def get_supplier_webscrape_params(supplier_name):
    webscrape_params = WebscrapeParams.query.filter_by(supplier_name = supplier_name).first()
    if webscrape_params:
        return webscrape_params.json()
    return {}

def delete_all_parameters():
    try:
        num_rows_deleted = db.session.query(WebscrapeParams).delete()
        db.session.commit()
    except:
        db.session.rollback()

#add parameters to db and delete all current parameters
def add_parameters(data):

    parameters = WebscrapeParams(supplier_name = data["supplier_name"],
                                website_url = data["website_url"], 
                                category = data["category"],
                                country = data["country"],
                                region = data["region"],
                                rating = data["rating"])
    try:
        db.session.add(parameters)
        db.session.commit()
    except:
        return jsonify(
                {
                    "code": 500,
                    "data": parameters,
                    "message": "An error occured while adding parameters."
                }
            ), 500
    return jsonify(
        {
            "code": 201,
            "message": "Parameters has been successfully added."
        }
    ), 201

def update_parameters(supplier_name, website_url, category, country, region, rating):
    try:
        parameters = db.session.execute(db.select(WebscrapeParams).filter_by(supplier_name=supplier_name)).scalar_one()
        print(parameters.website_url)
        parameters.website_url = website_url
        parameters.category = category
        parameters.country = country
        parameters.region = region
        parameters.rating = rating
        db.session.commit()
    except:
        return jsonify(
            {
                "code": 500,
                "data": parameters,
                "message": "An error occured while updating parameters."
            }
        ), 500
    return jsonify(
        {
            "code": 201,
            "message": "Parameters has been successfully updated."
        }
    ), 201

def get_all_parameters():
    parameter_list = WebscrapeParams.query.all()
    
    if parameter_list:
        return jsonify(
            {
                "code": 200,
                "data": {
                    "parameter_listing": [parameter.json() for parameter in parameter_list]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": "There are no parameters added to the db."
        }
    ), 404

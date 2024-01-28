from models.webscrape_param import *
import importlib
from os import environ

module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

def webscrape_param_services(parameters):
    
    '''
        {
            "supplier_name": "vivino",
            "website_url": "https://www.vivino.com/explore",
            "category": "Rosé, Sparkling",
            "country": "Chile, Argentina, Australia",
            "region": "",
            "rating":""
        },
        {
            "supplier_name": "wine.delivery",
            "website_url": "https://wine.delivery/Buy-Wine-Online",
            "category": "White Wine",
            "country": "Italy",
            "region":"",
            "rating":""
        }
            
    '''
    result = update_parameters(parameters['supplier_name'], parameters['website_url'], parameters['category'],
                                parameters['country'],parameters['region'],parameters['rating'])
    return result
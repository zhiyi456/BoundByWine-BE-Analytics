from flask import request

from services.webscrape_param import *
from models.webscrape_param import *
import importlib
from os import environ


module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

#update webscrape_param
@app.route('/webscrape_param', methods=['POST'])
def webscrape_param_controller():
    data = request.get_json()
    return webscrape_param_services(data)


@app.route('/webscrape_param/add', methods=['POST'])
def webscrape_param_add_controller():
    data = request.get_json()
    return add_parameters(data)
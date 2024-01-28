from flask import request

from services.schedule_params import *
import importlib
from os import environ


module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

#throw this to bottom
@app.route('/schedule_params', methods=['POST'])
def date_controller():
    data = request.get_json()
    return schedule_params_services(data)
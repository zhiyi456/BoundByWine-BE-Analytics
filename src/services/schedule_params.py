from models.schedule_params import *
import importlib
from os import environ


module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

def schedule_params_services(data):
    
    delete_all_date()

    '''
        {
            "day": "30"
        }
    '''
    result = add_date(data['day'])
    return result
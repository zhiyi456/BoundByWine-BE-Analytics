from flask import jsonify
from models.scrape_logs import *

# some weird error for get_all_scrape_logs_model()
def get_all_scrape_logs_service():
    try:
        scrape_logs_list = get_all_scrape_logs_model()
        if scrape_logs_list:
            return jsonify(
                {
                    "code": 200,
                    "data": {
                        "scrape_logs": [scrape_log.json() for scrape_log in scrape_logs_list]
                    }
                }
            )
        return jsonify(
            {
                "code": 404,
                "message": "There are no scrape log."
            }
        ), 404
    except:
        return jsonify(
            {
                "code": 500,
                "message": 'Internal server error' 
            }
        ), 500


def get_scrape_logs_by_supplier_service(supplier_name):
    try:
        scrape_logs_list = get_scrape_logs_by_supplier_model(supplier_name)
        if scrape_logs_list:
            return jsonify(
                {
                    "code": 200,
                    "data": {
                        "scrape_log": [scrape_log.json() for scrape_log in scrape_logs_list]
                    }
                }
            )
        return jsonify(
            {
                "code": 404,
                "message": 'No scrape logs for ' + str(supplier_name) 
            }
        ), 404
    except:
        return jsonify(
            {
                "code": 500,
                "message": 'Internal server error' 
            }
        ), 500

def get_scrape_logs_by_date_service():
    try:
        scrape_logs_list = get_scrape_logs_by_date_model()
        if scrape_logs_list:
            return jsonify(
                {
                    "code": 200,
                    "data": {
                        "scrape_logs": [scrape_log.json() for scrape_log in scrape_logs_list]
                    }
                }
            )
        return jsonify(
            {
                "code": 404,
                "message": "There are no scrape log."
            }
        ), 404
    except:
        return jsonify(
            {
                "code": 500,
                "message": 'Internal server error' 
            }
        ), 500
from services.scrape_logs import *
import importlib
from os import environ

module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

@app.route("/scrape_logs")
def get_all_scrape_logs_controller():
    logs = get_all_scrape_logs_service()
    if logs:
        return logs


@app.route("/scrape_logs/<string:supplier_name>", methods=['GET'])
def get_scrape_logs_by_supplier_controller(supplier_name):
    logs = get_scrape_logs_by_supplier_service(supplier_name)
    if logs:
        return logs

@app.route("/scrape_logs_by_date", methods=['GET'])
def get_scrape_logs_by_date_controller():
    logs = get_scrape_logs_by_date_service()
    return logs

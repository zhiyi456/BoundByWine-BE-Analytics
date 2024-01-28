from datetime import datetime

from services.new_name_match import *
from models.webscrape_param import *
from models.schedule_params import *
from models.matched_product_listing import *
from models.unmatched_product_listing import *
from services.bbw_product import *
from services.new_webscrape import *
from services.predicted_demand import *
from models.scrape_logs import *
from controllers.new_webscrape import *

from os import environ
import importlib
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from flask_apscheduler import APScheduler

module = importlib.import_module(environ.get("STAGE_ENV"))

app = module.app

scheduler = APScheduler()


@scheduler.task('interval', id='do_job_1', seconds=3600, misfire_grace_time=900)
def run_all():
    with scheduler.app.app_context():
        result = get_date()
        date = result.get_json()['data']['parameter_listing'][0]
        year = datetime.now().year
        month = datetime.now().month
        day = int(date['day'])
        current_day = datetime.now().day
        hour = 2
        current_hour = datetime.now().hour
        # minute = 7 
        # second = 0
        #this runs at 2am for any stated date
        if day == current_day and hour == current_hour:
            schedule_scrape()



# @scheduler.task('date', id='do_job', run_date = datetime(year, month, day, hour, minute, second))
def schedule_scrape():
    with scheduler.app.app_context():
        #get filter parameters
        scheduler.pause_job('do_job_1')

        i = 0
        
        while (i < 9):
            i+= 1
            
            if i == 1:
                webscraping("wine.delivery")
            elif i == 2:
                webscraping("vivino")
            elif i == 3:
                webscraping("pivene")
            elif i == 4:
                webscraping("twdc")
            elif i == 5:
                webscraping("winedelivery")
            elif i == 6:
                webscraping("winelistasia")
            elif i == 7:
                webscraping("winesonline")
            elif i == 8:
                webscraping("wineswholesales")
            elif i == 9:
                train_mlr_demand_prediction()

    scheduler.resume_job('do_job_1')
    return print("All Web Scraping have ran successfully! Congratz mate.")


@app.before_request 
def before_request_callback(): 
    scheduler.pause_job('do_job_1')

@app.after_request 
def after_request_callback( response ): 
    # your code here 
    scheduler.resume_job('do_job_1')
    return response 

scheduler.init_app(app)
scheduler.start()
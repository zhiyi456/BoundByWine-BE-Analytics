from flask import jsonify
from os import environ
import importlib

app = importlib.import_module(environ.get("STAGE_ENV"))

db = app.db

class ScheduleParams(db.Model):
    __tablename__ = 'schedule_params'

    scheduler_id = db.Column(db.Integer(), primary_key=True)
    day = db.Column(db.String(200), nullable = True)


    def __init__(self, day):
        self.day = day

    def json(self):
        dto = {
            'day': self.day
        }
        return dto 

def delete_all_date():
    try:
        num_rows_deleted = db.session.query(ScheduleParams).delete()
        db.session.commit()
    except:
        db.session.rollback()

#add parameters to db and delete all current parameters
def add_date(day):
    parameters = ScheduleParams(day = day)
    try:
        db.session.add(parameters)
        db.session.commit()
    except:
        return jsonify(
                {
                    "code": 500,
                    "data": parameters,
                    "message": "An error occured while adding the date."
                }
            )
    return jsonify(
        {
            "code": 201,
            "message": "Date has been successfully updated."
        }
    )

def get_date():
    parameter_list = ScheduleParams.query.all()
    
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
            "message": "There are no Date added to the db."
        }
    )
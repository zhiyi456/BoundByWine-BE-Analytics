from os import environ
import importlib

app = importlib.import_module(environ.get("STAGE_ENV"))

db = app.db

class ScrapeLogs(db.Model):
    __tablename__ = 'Scrape_Logs'

    Supplier_Name = db.Column(db.String(100) , primary_key=True)
    Scraped_Data_Datetime = db.Column(db.DateTime, primary_key=True)

    def __init__(self, Supplier_Name, Scraped_Data_Datetime):
        self.Supplier_Name = Supplier_Name
        self.Scraped_Data_Datetime = Scraped_Data_Datetime

    def json(self):
        dto = {
            'Supplier_Name': self.Supplier_Name,
            'Scraped_Data_Datetime': self.Scraped_Data_Datetime
        }
        return dto 
    
def create_new_scrape_log(supplier_name, datetime):
    log = ScrapeLogs(Supplier_Name = supplier_name, 
                Scraped_Data_Datetime = datetime)
    try:
        db.session.add(log)
        db.session.commit()
    except:
           return log.json()
    return None

def get_all_scrape_logs_model():
    scrape_logs_list = ScrapeLogs.query.all()
    return scrape_logs_list

def get_scrape_logs_by_supplier_model(supplier_name):
    scrape_logs_list = ScrapeLogs.query.filter_by(Supplier_Name = supplier_name).all()
    return scrape_logs_list

def get_scrape_logs_by_date_model():
    scrape_logs_list = ScrapeLogs.query.order_by(ScrapeLogs.Scraped_Data_Datetime.desc()).all()
    return scrape_logs_list



from os import environ
import importlib

app = importlib.import_module(environ.get("STAGE_ENV"))

db = app.db

class Supplier(db.Model):
    __tablename__ = 'Supplier'

    Supplier_Name = db.Column(db.String(200), primary_key=True)

    def __init__(self, Supplier_Name):
        self.Supplier_Name = Supplier_Name

    def json(self):
        dto = {
            'Supplier_Name': self.Supplier_Name,
        }
        return dto 


def get_all_supplier_listing():
    supplier_list = Supplier.query.all()
    
    if supplier_list:
        return [supplier.json() for supplier in supplier_list]
    return []


def get_all_supplier_name():
    supplier_name_list = Supplier.query.all()
    if supplier_name_list:
        return [supplier.json()['Supplier_Name'] for supplier in supplier_name_list]
    return []
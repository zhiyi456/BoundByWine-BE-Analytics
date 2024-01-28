from os import environ
import importlib
from sqlalchemy import text

app = importlib.import_module(environ.get("STAGE_ENV"))

db = app.db

class UnmatchedProductListing(db.Model):
    __tablename__ = 'unmatched_product_listing'

    supplier_original_product_name = db.Column(db.String(200), primary_key=True)
    supplier_name = db.Column(db.String(100), primary_key=True)
    in_stock_status = db.Column(db.Boolean, nullable=False)
    product_listing_old_price = db.Column(db.Float, nullable=False)
    product_listing_current_price = db.Column(db.Float, nullable=False)

    def __init__(self, supplier_original_product_name, supplier_name, in_stock_status, product_listing_old_price, product_listing_current_price):
        self.supplier_original_product_name = supplier_original_product_name
        self.supplier_name = supplier_name
        self.in_stock_status = in_stock_status
        self.product_listing_old_price = product_listing_old_price
        self.product_listing_current_price = product_listing_current_price

    def json(self):
        dto = {
            'supplier_original_product_name': self.supplier_original_product_name,
            'supplier_name': self.supplier_name,
            'in_stock_status': self.in_stock_status,
            'product_listing_old_price': self.product_listing_old_price,
            'product_listing_current_price': self.product_listing_current_price
        }
        return dto 


def product_listing_get_all():
    product_listing_list = UnmatchedProductListing.query.all()
    if product_listing_list:
        return product_listing_list
    return []

def update_unmatched_product_listing(supplier_original_product_name, supplier_name, product_listing_current_price):
    data_row = UnmatchedProductListing.query.filter_by(supplier_original_product_name = supplier_original_product_name, supplier_name = supplier_name).first()
    old_price = data_row.json()['product_listing_current_price']
    sql = text("UPDATE unmatched_product_listing SET product_listing_old_price = :old_price, product_listing_current_price = :product_listing_current_price WHERE supplier_original_product_name = :supplier_original_product_name and supplier_name = :supplier_name")
    val = {
            "old_price": old_price, 
            "product_listing_current_price": product_listing_current_price, 
            "supplier_original_product_name": supplier_original_product_name,
            "supplier_name": supplier_name
        }
    db.session.execute(sql, val)
    db.session.commit()

def check_if_product_name_and_supplier_name_exist_unmatched(supplier_original_product_name, supplier_name):
    product_listing = UnmatchedProductListing.query.filter_by(supplier_original_product_name = supplier_original_product_name, supplier_name = supplier_name).first()
    if product_listing:
        return True
    return False

def create_new_poduct_in_unmatched_product_listing(supplier_original_product_name, supplier_name, product_listing_status, product_listing_current_price):
    product_listing = UnmatchedProductListing(supplier_original_product_name, supplier_name, product_listing_status, 0, product_listing_current_price)
    try:
        db.session.add(product_listing)
        db.session.commit()
    except:
        return False
    return True
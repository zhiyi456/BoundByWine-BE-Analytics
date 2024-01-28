from os import environ
import importlib
from sqlalchemy import text

app = importlib.import_module(environ.get("STAGE_ENV"))

db = app.db

# Does not contain bbw as a supplier, only from other competitors website product

class MatchedProductListing(db.Model):
    __tablename__ = 'matched_product_listing'

    bbw_product_name = db.Column(db.String(200), primary_key=True)
    supplier_name = db.Column(db.String(100), primary_key=True)
    supplier_original_product_name = db.Column(db.String(200), primary_key=True)
    in_stock_status = db.Column(db.Boolean, nullable=False)
    product_listing_old_price = db.Column(db.Float, nullable=False)
    product_listing_current_price = db.Column(db.Float, nullable=False)

    def __init__(self, bbw_product_name, supplier_name, supplier_original_product_name, in_stock_status, product_listing_old_price, product_listing_current_price):
        self.bbw_product_name = bbw_product_name
        self.supplier_name = supplier_name
        self.supplier_original_product_name = supplier_original_product_name
        self.in_stock_status = in_stock_status
        self.product_listing_old_price = product_listing_old_price
        self.product_listing_current_price = product_listing_current_price

    def json(self):
        dto = {
            'bbw_product_name': self.bbw_product_name,
            'supplier_name': self.supplier_name,
            'supplier_original_product_name': self.supplier_original_product_name,
            'product_listing_status': self.in_stock_status,
            'product_listing_old_price': self.product_listing_old_price,
            'product_listing_current_price': self.product_listing_current_price
        }
        return dto 


def product_listing_get_all():
    product_listing_list = MatchedProductListing.query.all()
    if product_listing_list:
        return [product.json() for product in product_listing_list]
    return []

def update_matched_product_listing(supplier_original_product_name, supplier_name, product_listing_current_price):
    data_row = MatchedProductListing.query.filter_by(supplier_original_product_name = supplier_original_product_name, supplier_name = supplier_name).first()
    old_price = data_row.json()['product_listing_current_price']
    sql = text("UPDATE matched_product_listing SET product_listing_old_price = :old_price, product_listing_current_price = :product_listing_current_price WHERE supplier_original_product_name = :supplier_original_product_name and supplier_name = :supplier_name")
    val = {
        "old_price": old_price, 
        "product_listing_current_price": product_listing_current_price, 
        "supplier_original_product_name": supplier_original_product_name,
        "supplier_name": supplier_name
    }
    db.session.execute(sql, val)
    db.session.commit()


def check_if_product_name_and_supplier_name_exist_matched(supplier_original_product_name, supplier_name):
    product_listing = MatchedProductListing.query.filter_by(supplier_original_product_name = supplier_original_product_name, supplier_name = supplier_name).first()
    if product_listing:
        return True
    return False

def create_new_poduct_in_matched_product_listing(bbw_product_name, supplier_original_product_name, supplier_name, product_listing_status, product_listing_current_price):
    product_listing = MatchedProductListing(bbw_product_name, supplier_name, supplier_original_product_name, product_listing_status, 0, product_listing_current_price)
    try:
        db.session.add(product_listing)
        db.session.commit()
    except:
        return False
    return True

def get_product_with_price_change():
    product_listing_list = MatchedProductListing.query.filter(MatchedProductListing.product_listing_old_price!=MatchedProductListing.product_listing_current_price).all()
    if product_listing_list:
        return [product.json() for product in product_listing_list]
    return []
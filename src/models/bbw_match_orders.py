from os import environ
import importlib
from sqlalchemy import desc
from datetime import datetime

app = importlib.import_module(environ.get("STAGE_ENV"))

db = app.db

class BBWMatchedOrders(db.Model):
    __tablename__ = 'bbw_matched_orders'

    checkout_token = db.Column(db.String(200), primary_key=True)
    order_datetime = db.Column(db.TIMESTAMP, primary_key=True)
    product_name = db.Column(db.String(200), primary_key=True)
    item_quantity = db.Column(db.Integer)
    item_price = db.Column(db.Float(6,2))
    shopify_product_id = db.Column(db.String(200))
    product_type = db.Column(db.String(200))

    def __init__(self, checkout_token, order_datetime, product_name, item_quantity, item_price, shopify_product_id, product_type):
        self.checkout_token = checkout_token
        self.order_datetime = order_datetime
        self.product_name = product_name
        self.item_quantity = item_quantity
        self.item_price = item_price
        self.shopify_product_id = shopify_product_id
        self.product_type = product_type

    def json(self):
        dto = {
            'checkout_token': self.checkout_token,
            'order_datetime': self.order_datetime,
            'product_name': self.product_name,
            'item_quantity': self.item_quantity,
            'item_price': self.item_price,
            'shopify_product_id': self.shopify_product_id,
            'product_type': self.product_type,
        }
        return dto
    
def post_order_to_db(order):

    order_datetime = order['order_datetime'].split('+')[0]
    order_datetime = datetime.strptime(order_datetime, "%Y-%m-%dT%H:%M:%S")

    to_db = {
        'checkout_token': order['checkout_token'],
        'order_datetime': order_datetime,
        'product_name': order['item_name'],
        'item_quantity': order['item_qty'],
        'item_price': order['price'],
        'shopify_product_id': order['pdt_id'],
        'product_type': order['product_type'],
    }
    add_pdt = BBWMatchedOrders(**to_db)
    try:
        db.session.add(add_pdt)
        db.session.commit() # POST method
        return {
                "code": 201,
                "data": to_db,
                "message": "Order successfully created."
                }
    except Exception as e:
        print("post_orders_to_db error: " + str(e))
        return {
                "code": 500,
                "data": to_db,
                "message": str(e),
                }

def get_all_bbw_orders():
    order_list = BBWMatchedOrders.query.all()
    if order_list:
        return [order.json() for order in order_list]
    
    return []

def get_latest_order():
    latest_order = BBWMatchedOrders.query.order_by(desc('order_datetime')).first()
    if latest_order:
        return {
            'code': 200,
            'data': latest_order.json()
        }
    return {}

def get_orders_by_product_id(shopify_product_id):
    orders_for_particular_product = BBWMatchedOrders.query.filter_by(shopify_product_id = shopify_product_id)
    if orders_for_particular_product:
        return [order.json() for order in orders_for_particular_product]
    return []
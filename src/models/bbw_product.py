from os import environ
import importlib

app = importlib.import_module(environ.get("STAGE_ENV"))

db = app.db

class BBWProduct(db.Model):
    __tablename__ = 'bbw_product'

    shopify_product_id = db.Column(db.String(200), primary_key=True)
    bbw_product_name = db.Column(db.String(200))
    product_type = db.Column(db.String(200))
    product_description = db.Column(db.String())
    image = db.Column(db.String(200))
    shopify_sku = db.Column(db.String(200))
    price = db.Column(db.Float(5,2))

    def __init__(self, shopify_product_id, bbw_product_name,  product_type, product_description, image, shopify_sku, price):
        self.shopify_product_id = shopify_product_id
        self.bbw_product_name = bbw_product_name
        self.product_type = product_type
        self.product_description = product_description
        self.image = image
        self.shopify_sku = shopify_sku
        self.price = price

    def json(self):
        dto = {
            'shopify_product_id': self.shopify_product_id,
            'bbw_product_name': self.bbw_product_name,
            'product_type': self.product_type,
            'product_description': self.product_description,
            'image': self.image,
            'shopify_sku': self.shopify_sku,
            'price': self.price,
        }
        return dto 


def get_all_bbw_product_model():
    product_list = BBWProduct.query.all()
    
    if product_list:
        return [product.json() for product in product_list]
    
    return []

def post_product_to_db(temp_dict, html, image, sku, price):
    to_db = {
        'shopify_product_id': str(temp_dict['id']), 
        'bbw_product_name': temp_dict['title'], 
        'product_type': temp_dict['product_type'],
        'product_description': html,
        'image': image,
        'shopify_sku': sku,
        'price': price
    }
    add_pdt = BBWProduct(**to_db)
    try:
        db.session.add(add_pdt)
        db.session.commit() # POST method
        return True
    except Exception as e:
        print("post_product_to_db error: " + str(e))
        return to_db
    
def truncate_table():
    if BBWProduct.query.all():
        try:
            BBWProduct.query.delete()
            db.session.commit()
            print("BBW products table truncated.")
        except Exception as e:
            print("truncate_table error: " + str(e))

def get_shopify_product_by_product_name(product_name):
    shopify_product = BBWProduct.query.filter_by(bbw_product_name = product_name).first()
    if shopify_product:
        return {
            "code": 200,
            "data": shopify_product.json()
            }
    return {
            "code": 404,
            "message": 'No Shopify data for product named ' + str(product_name)
            }
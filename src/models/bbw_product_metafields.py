from os import environ
import importlib
import ast

app = importlib.import_module(environ.get("STAGE_ENV"))

db = app.db

class BBWProductMetafields(db.Model):
    __tablename__ = 'bbw_product_metafields'

    shopify_product_id = db.Column(db.String(200), primary_key=True)
    acidity = db.Column(db.String(200))
    country = db.Column(db.String(200))
    dryness = db.Column(db.String(200))
    fermentation = db.Column(db.String(200))
    glass = db.Column(db.String(200))
    grape = db.Column(db.String(200))
    region = db.Column(db.String(200))
    tannin = db.Column(db.String(200))
    body = db.Column(db.String(200))
    varietals = db.Column(db.String())

    def __init__(self, shopify_product_id, acidity, country, dryness, fermentation, glass, grape, region, tannin, body, varietals):
        self.shopify_product_id = shopify_product_id
        self.acidity = acidity
        self.country = country
        self.dryness = dryness
        self.fermentation = fermentation
        self.glass = glass
        self.grape = grape
        self.region = region
        self.tannin = tannin
        self.body = body
        self.varietals = varietals

    def json(self):
        dto = {
            'shopify_product_id': self.shopify_product_id,
            'acidity': self.acidity,
            'country': self.country,
            'dryness': self.dryness,
            'fermentation': self.fermentation,
            'glass': self.glass,
            'grape': self.grape,
            'region': self.region,
            'tannin': self.tannin,
            'body': self.body,
            'varietals': self.varietals,
        }
        return dto
    
def post_metafields_to_db(metafields, shopify_product_id):
    to_db = {
        'shopify_product_id': shopify_product_id,
        'acidity': None,
        'country': None,
        'dryness': None,
        'fermentation': None,
        'glass': None,
        'grape': None,
        'region': None,
        'tannin': None,
        'body': None,
        'varietals': None,
    }
    varietals = []
    for field in metafields:
        key = field['key']
        if key == 'regional_varietals' or key == 'varietals':
            if field['value'] != None and field['value'] != '': # convert to list and append to varietals
                varietals.extend(ast.literal_eval(field['value']))
        else:
            if key in to_db.keys():
                to_db[key] = field['value']
    
    if varietals != []:
        to_db['varietals'] = repr(varietals)
        # print(repr(varietals))

    add_pdt = BBWProductMetafields(**to_db)
    try:
        db.session.add(add_pdt)
        db.session.commit() # POST method
        return {
                "code": 201,
                "data": to_db,
                "message": "Metafield successfully created."
                }
    except Exception as e:
        print("post_metafields_to_db error: " + str(e))
        return {
                "code": 500,
                "data": to_db,
                "message": "Unable to create metafield in database.",
                }
    

def get_metafield_by_id(shopify_product_id):
    fields = BBWProductMetafields.query.filter_by(shopify_product_id=shopify_product_id).first()
    if fields:
        return {
                "code": 200,
                "data": fields.json()
                }
    return {}
    
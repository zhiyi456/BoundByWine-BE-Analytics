import pandas as pd
from os import environ

from models.bbw_product import *
from models.matched_product_listing import *

module = importlib.import_module(environ.get("STAGE_ENV"))

def get_top_products_with_price_deviations():
    result = []

    merged_df = merge_bbw_data_to_matched_competitor_listings()

    merged_stats = get_mean_and_median(merged_df.copy()) 

    # get unique bbw_products and find top 5 (each) mean & median differences
    merged_stats.drop_duplicates(subset=['bbw_product_name'], inplace=True)
    top_deviations = pd.concat([merged_stats.sort_values(by=['mean_deviation'],ascending=False)[0:4], merged_stats.sort_values(by=['median_deviation'],ascending=False)[0:4]])
    top_deviations.drop_duplicates(subset=['bbw_product_name'], inplace=True)

    for index, row in top_deviations.iterrows():
        suppliers = find_competitors_with_same_item(row['bbw_product_name'], merged_df)
        top_deviations.at[index, 'supplier_name'] = suppliers
    
    return top_deviations.to_dict('records')


def find_competitors_with_same_item(bbw_product_name, merged_df):
    competitors = merged_df[merged_df['bbw_product_name']==bbw_product_name]['supplier_name']
    return ', '.join(competitors.tolist())


def merge_bbw_data_to_matched_competitor_listings():
    # get all matched products from competitors and suppliers
    matched_listings_df = pd.DataFrame(product_listing_get_all())
    matched_listings_df = matched_listings_df[['bbw_product_name','supplier_name','product_listing_current_price']]
    matched_listings_df['product_listing_current_price'] = matched_listings_df['product_listing_current_price'].astype(float)

    # get all BBW products
    bbw_products_df = pd.DataFrame(get_all_bbw_product_model())
    bbw_products_df = bbw_products_df[['bbw_product_name','image','price']]
    bbw_products_df.drop_duplicates(subset=['bbw_product_name'], inplace=True)
    bbw_products_df['price'] = bbw_products_df['price'].astype(float)
    
    # merge supplier & bbw listing info
    merged_df = pd.merge(matched_listings_df, bbw_products_df, how='left', on='bbw_product_name')

    return merged_df


def get_mean_and_median(merged_df):
    no_null_competitor_prices = merged_df[(merged_df['product_listing_current_price']!=0) & merged_df['product_listing_current_price'].notnull()]
    no_null_competitor_prices['median_price'] = no_null_competitor_prices['product_listing_current_price']
    no_null_competitor_prices['mean_price'] = no_null_competitor_prices['product_listing_current_price']

    # get mean and median (group by bbw_product name)
    mean_and_median = no_null_competitor_prices[['bbw_product_name','mean_price','median_price']].groupby('bbw_product_name').agg({'mean_price': 'mean', 'median_price': 'median'})
    no_null_competitor_prices.drop(columns=['mean_price','median_price'], inplace=True)
    merged_stats = pd.merge(merged_df, mean_and_median, on='bbw_product_name', how='left')

    # find difference in bbw_price and competitor median/mean
    merged_stats['mean_deviation'] = abs(merged_stats['mean_price'] - merged_stats['price'])
    merged_stats['median_deviation'] = abs(merged_stats['median_price'] - merged_stats['price'])

    return merged_stats
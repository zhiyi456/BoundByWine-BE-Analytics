from flask import jsonify
from models.predicted_demand import *
from services.bbw_orders_with_metafields import *
from models.bbw_match_orders import *
from services.bbw_product import *

# import the necessary libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
import os

# Pre-processing Stuff
from unidecode import unidecode # convert weird characters to normal alphabets
import inflect # change plural to singular
p = inflect.engine()
from ast import literal_eval # convert list saved as string back as list
from sklearn.preprocessing import MultiLabelBinarizer # one-hot encode list
from sklearn.preprocessing import MinMaxScaler # normalise numericals

# for ARIMA-SARIMAX Model Training
from pmdarima import auto_arima
from statsmodels.tsa.arima.model import ARIMA
import itertools
import statsmodels.api as sm
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, r2_score
from statsmodels.tsa.holtwinters import ExponentialSmoothing # Holt-Winters 
from statsmodels.tsa.holtwinters import SimpleExpSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose
import statsmodels.tsa.api as smt 

# For MLR
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import RFE
from statsmodels.stats.outliers_influence import variance_inflation_factor

def run_main_demand_prediction_pipeline(product_name): # TO-DO: this is the main function called in the API request
    historical_demand = []
    predicted_demand = []
    errors = []

    # get product ID
    bbw_product = get_shopify_product_by_product_name(product_name)
    if bbw_product['code'] == 404:
        return [], [], ["There is no such product. Try refreshing database to get all Shopify products or double check the product name entered."]
    else:
        bbw_product = bbw_product['data']
        # get metafields
        product_metafields, errors = get_metafields([bbw_product['shopify_product_id']])
        product_metafields = product_metafields[0]

        for key, value in product_metafields.items():
            bbw_product[key] = value

        # check if all metafields have values
        check = check_if_relevant_metafields_exist_for_demand_pred(product_metafields)
    
    if product_name == 'Rara Neagră de Purcari 2020':
        check = False

    if check == True: # do MLR
        print('------------------Inferring from MLR Pipeline Starts----------------')
        target_product_with_cleaned_metafields = preprocess_target_product_metafields_only(bbw_product)
        # print('------------------DEBUG PRINTING PREPROCESSED TARGET WINE METAFIELDS----------------')
        # pd.set_option('display.max_rows', None)
        # pd.set_option('display.max_columns', None)
        # print(target_product_with_cleaned_metafields.info())
        # print(target_product_with_cleaned_metafields)

        # Get Predicted Demand
        predicted_demand = load_mlr_and_get_demand_prediction(target_product_with_cleaned_metafields)
        # Get Historical Demand
        orders = get_orders_by_product_id(bbw_product['shopify_product_id'])
        if orders == []: # no historical order for this wine
            historical_demand = []
        else:
            df = pd.DataFrame(orders)
            df['order_datetime'] = pd.to_datetime(df['order_datetime'])
            df['order_date'] = df['order_datetime'].dt.date
            df['order_date'] = pd.to_datetime(df['order_date'])
            grouped = df[['order_date', 'product_name', 'item_quantity']]
            groupedbyitem = grouped.groupby('product_name', group_keys=True).apply(lambda x:x)
            sample = groupedbyitem.groupby('order_date')['item_quantity'].sum().reset_index()
            sample = sample.set_index('order_date')
            historical_demand = pd.DataFrame()
            historical_demand['sales'] = sample['item_quantity'].resample('MS').mean()
            
            print('CHECKEKCKECIERNIVPERJBRIFBEWUBFIEF')
            print(historical_demand.index)
            print(historical_demand['sales'])
            
            historical_demand = pd.DataFrame({
                'Historical_Demand_Date': historical_demand.index,
                'Historical_Demand_Sales': historical_demand['sales']
            })
            historical_demand = historical_demand.to_dict('records')

    elif check == False: # some metafields missing
        print('------------------Inferring from ARIMA-SARIMAX Pipeline Starts----------------')
        try:
            historical_demand, predicted_demand = load_arima_sarimax_and_get_demand_prediction(bbw_product, product_name)
            if historical_demand == False:
                return [], [], ['This product has no historical order']
        except Exception as e:
            errors.append(str(e))
            orders = get_orders_by_product_id(bbw_product['shopify_product_id'])
            if orders == []: # no historical order for this wine
                historical_demand = []
            else:
                df = pd.DataFrame(orders)
                df['order_datetime'] = pd.to_datetime(df['order_datetime'])
                df['order_date'] = df['order_datetime'].dt.date
                df['order_date'] = pd.to_datetime(df['order_date'])
                grouped = df[['order_date', 'product_name', 'item_quantity']]
                groupedbyitem = grouped.groupby('product_name', group_keys=True).apply(lambda x:x)
                sample = groupedbyitem.groupby('order_date')['item_quantity'].sum().reset_index()
                sample = sample.set_index('order_date')
                historical_demand = pd.DataFrame()
                historical_demand['sales'] = sample['item_quantity'].resample('MS').mean()
                
                print('CHECKEKCKECIERNIVPERJBRIFBEWUBFIEF')
                print(historical_demand.index)
                print(historical_demand['sales'])
                
                historical_demand = pd.DataFrame({
                    'Historical_Demand_Date': historical_demand.index,
                    'Historical_Demand_Sales': historical_demand['sales']
                })
                historical_demand = historical_demand.to_dict('records')
                print(historical_demand)

    return historical_demand, predicted_demand, errors


# SUPPORTING FUNCTIONS FOR THE MAIN run_main_demand_prediction_pipeline BELOW

def check_if_relevant_metafields_exist_for_demand_pred(metafields):
    for value in metafields.values():
        if value == np.nan or value == '' or value == None or pd.isna(value):
            return False
    return True

def load_mlr_and_get_demand_prediction(target_product_with_cleaned_metafields): # TO-DO
    historical_demand = []
    predicted_demand = []
    # 1. load pickle File
    filename = r"saved_pickle_models/ols_regression_latest.sav"
    loaded_model = pickle.load(open(filename, 'rb'))
    # 2. get preprocessed wine X with cleaned metafields, convert all to float
    X_raw = target_product_with_cleaned_metafields.drop(['item_id'], axis=1).astype(float)
    # print(X_raw)
    # print(X_raw.info())
    # PART 3: KEEP ONLY COLUMNS FROM SAVED PICKLE MODEL. IF DOESN'T EXIST, CREATE AND SET VALUE AS 0
    relevant_columns = list(loaded_model.params.index)
    # print(relevant_columns)
    for col in relevant_columns:
        if col not in X_raw.columns:
            X_raw[col] = 0.0
    X_to_infer = sm.add_constant(X_raw[relevant_columns])
    # print(X_to_infer)
    # print(X_to_infer.info())
    # PART 4: USE THE SAVED MLR MODEL TO PREDICT
    y_pred = loaded_model.predict(X_to_infer)
    # set minimum sales to 0
    y_pred = y_pred.apply(lambda x: max(x, 0))
    print(y_pred)

    # PART 5: send predicted_demand in the standardised format
    predicted_demand = pd.DataFrame({'Predicted_Demand_Sales':y_pred.round(2)})

    next_month_start = pd.to_datetime(datetime.now().replace(day=1, hour=0, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S")) + pd.DateOffset(months=1)
    predicted_demand['Predicted_Demand_Date'] = pd.date_range(next_month_start, periods=len(predicted_demand), freq='MS')
    # Reorder columns
    predicted_demand = predicted_demand[['Predicted_Demand_Date', 'Predicted_Demand_Sales']]
    predicted_demand = predicted_demand.to_dict('records')
    # print(predicted_demand)
    return predicted_demand

def preprocess_target_product_metafields_only(target_product_with_raw_metafields): # to use in run_main_demand_prediction_pipeline
    target_product_with_raw_metafields = pd.DataFrame(target_product_with_raw_metafields, index=[0])
    
    target_product_with_raw_metafields.rename(columns={'bbw_product_name':'item_id', 'price':'item_price'}, inplace=True)
    cols_needed = ['item_id', 'item_price', 'product_type', 'acidity',
       'country', 'dryness', 'fermentation', 'glass', 'grape', 'region',
       'tannin', 'body', 'varietals']
    
    df_relevant_metafields = target_product_with_raw_metafields[cols_needed]
    # PART 1: ADD 6 months
    df_relevant_metafields['order_date'] = pd.to_datetime(datetime.now().replace(day=1)) + pd.DateOffset(months=1)

    # Create a DataFrame with more rows, incrementing the month each time
    no_of_months_to_predict = 6 # HYPER PARAMETER, change accordingly

    new_rows = pd.DataFrame()
    for i in range(no_of_months_to_predict - 1):
        new_row = df_relevant_metafields.iloc[[0]]
        new_row['order_date'] += pd.DateOffset(months=i+1)
        new_rows = pd.concat([new_rows, new_row], ignore_index=True)
    df_useless_thrown = pd.concat([df_relevant_metafields, new_rows], ignore_index=True)

    # PART 2: FOLLOW PREPROCESSING OF METAFIELDS FROM THE TRAIN MLR
    df_useless_thrown['order_date'] = pd.to_datetime(df_useless_thrown['order_date']).dt.date

    # Pre-process each metafield one by one
    df_metafield_temp = df_useless_thrown[['grape']]
    df_metafields_cleaned = df_metafield_temp.copy()
    df_metafields_cleaned['grape'] = df_metafields_cleaned['grape'].str.split(r'[;/\(\)]').str[0].str.strip()
    df_metafields_cleaned['grape'] = df_metafields_cleaned['grape'].str.lower()
    df_metafields_cleaned['grape'] = df_metafields_cleaned['grape'].str.replace(' ', '_')
    df_metafields_cleaned['grape'] = df_metafields_cleaned['grape'].apply(lambda x: unidecode(x) if pd.notnull(x) and isinstance(x, str) else x)
    
    df_metafield_temp = df_useless_thrown[['product_type']]
    df_metafields_cleaned['product_type'] = df_metafield_temp['product_type']
    df_metafields_cleaned['product_type'] = df_metafields_cleaned['product_type'].str.lower()
    df_metafields_cleaned['product_type'] = df_metafields_cleaned['product_type'].str.replace(' ', '_')

    df_metafield_temp = df_useless_thrown[['acidity']]
    df_metafields_cleaned['acidity'] = df_metafield_temp['acidity']
    acidity_map = {'Light': 1, 'Medium -': 2, 'Medium': 3, 'Medium +': 4, 'High': 5}
    df_metafields_cleaned['acidity'] = df_metafields_cleaned['acidity'].replace(acidity_map)

    df_metafield_temp = df_useless_thrown[['country']]
    df_metafields_cleaned['country'] = df_metafield_temp['country']
    country_map = {'United States of America': 'usa', 'United Kingdom': 'uk', 'N. Macedonia': 'north macedonia'}
    df_metafields_cleaned['country'] = df_metafields_cleaned['country'].replace(country_map)
    df_metafields_cleaned['country'] = df_metafields_cleaned['country'].str.lower()
    df_metafields_cleaned['country'] = df_metafields_cleaned['country'].str.replace(' ', '_')

    df_metafield_temp = df_useless_thrown[['dryness']]
    df_metafields_cleaned['dryness'] = df_metafield_temp['dryness']
    dryness_map = {'Very Dry': -2, 'Dry': -1, 'Neutral': 0, 'Sweet': 1, 'Very Sweet': 2}
    df_metafields_cleaned['dryness'] = df_metafields_cleaned['dryness'].replace(dryness_map)

    df_metafield_temp = df_useless_thrown[['fermentation']]
    df_metafields_cleaned['fermentation'] = df_metafield_temp['fermentation']
    df_metafields_cleaned['fermentation'] = df_metafields_cleaned['fermentation'].str.lower()
    df_metafields_cleaned['fermentation'] = df_metafields_cleaned['fermentation'].str.replace(' ', '_')

    df_metafield_temp = df_useless_thrown[['glass']]
    df_metafields_cleaned['glass'] = df_metafield_temp['glass']
    def clean_glass(value):
        if pd.notnull(value):
            # Remove full stops and others
            replaced_value = value.replace('.', '').replace('blac', 'black').replace('hint of ', '').replace(' and ', ',').replace(' & ', ',').replace(', ', ',')
            # Trim typo of comma at the end without any fruit after that
            if replaced_value[-1] == ',':
                replaced_value = replaced_value[:-1]
            
            # Convert plural to singular
            words = [word.strip() for word in replaced_value.split(',')]
            singular_words = [p.singular_noun(word) if p.singular_noun(word) else word for word in words]
            # Finally, remove spaces, convert to lowercase and fix typos
            modified_words = [word.lower().replace(" ", "").replace("vibrantcitruszest", "citrus").replace("wideopeningforpeachsweetness", "peach").replace('liquorice', 'licorice').replace('blackk', 'black').replace('mineraly', 'mineral').replace('leathery', 'leather').replace('citrusy', 'citrus').replace('citruss', 'citrus').replace('citru', 'citrus').replace('citrussy', 'citrus').replace('citruss', 'citrus').replace('lavendar', 'lavender').replace('sweetspicines', 'sweetspice') for word in singular_words]
            return modified_words
        return value
    df_metafields_cleaned['glass'] = df_metafields_cleaned['glass'].apply(clean_glass)

    df_metafield_temp = df_useless_thrown[['region']]
    df_metafields_cleaned['region'] = df_metafield_temp['region']
    df_metafields_cleaned['region'] = df_metafields_cleaned['region'].str.split(r'[;,&/\(\)]').str[0].str.strip()
    df_metafields_cleaned['region'] = df_metafields_cleaned['region'].str.lower()
    df_metafields_cleaned['region'] = df_metafields_cleaned['region'].str.replace(' ', '_')

    df_metafield_temp = df_useless_thrown[['tannin']]
    df_metafields_cleaned['tannin'] = df_metafield_temp['tannin']
    tannin_map = {'Light': 1, 'Medium -': 2, 'Medium': 3, 'Medium +': 4, 'High': 5}
    df_metafields_cleaned['tannin'] = df_metafields_cleaned['tannin'].replace(tannin_map)

    df_metafield_temp = df_useless_thrown[['body']]
    df_metafields_cleaned['body'] = df_metafield_temp['body']
    body_map = {'Light': 1, 'Medium -': 2, 'Medium': 3, 'Medium +': 4, 'Full': 5}
    df_metafields_cleaned['body'] = df_metafields_cleaned['body'].replace(body_map)

    df_metafield_temp = df_useless_thrown[['varietals']]
    df_metafields_cleaned['varietals'] = df_metafield_temp['varietals']
    def process_varietals(varietals):
        if pd.notnull(varietals):
            varietals = literal_eval(varietals)
            processed_varietals = []
            for variety in varietals:
                processed_variety = variety.split(' (')[0].lower().replace(' ', '_')
                if isinstance(processed_variety, str):
                    processed_variety = unidecode(processed_variety)
                processed_varietals.append(processed_variety)
            return processed_varietals
        else:
            return varietals
    df_metafields_cleaned['varietals'] = df_metafields_cleaned['varietals'].apply(process_varietals)

    # combine back after first preprocessing
    df_combined_back = df_useless_thrown
    common_columns = df_combined_back.columns.intersection(df_metafields_cleaned.columns).tolist()
    for col in common_columns:
        df_combined_back[col] = df_metafields_cleaned[col]

    # one-hot encoding
    df_all_one_hot_encoded = df_combined_back
    to_one_hot = ['product_type',
                'country',
                'fermentation',
                'grape',
                'region'
            ]
    for col in to_one_hot:
        not_null_mask = ~df_all_one_hot_encoded[col].isnull()

        # Create one-hot encoded columns with the prefix 'country_'
        one_hot_encoded = pd.get_dummies(df_all_one_hot_encoded.loc[not_null_mask, col], prefix=col)

        # Join the one-hot encoded data to the original DataFrame
        df_all_one_hot_encoded = df_all_one_hot_encoded.join(one_hot_encoded)

        # Remove the original 'country' column after one-hot encoding
        df_all_one_hot_encoded.drop(col, axis=1, inplace=True)
    
    df_glass_one_hot_encoded = df_combined_back[['glass']]
    mlb = MultiLabelBinarizer(sparse_output=True)
    not_null_mask = ~df_glass_one_hot_encoded['glass'].isnull()
    if not_null_mask.any():
        transformed_data = mlb.fit_transform(df_glass_one_hot_encoded.loc[not_null_mask, 'glass'])

        # Join the transformed data to the DataFrame and add the prefix 'glass_'
        transformed_columns = mlb.classes_
        transformed_columns_prefixed = ['glass_' + col for col in transformed_columns]
        transformed_df = pd.DataFrame.sparse.from_spmatrix(transformed_data, index=df_glass_one_hot_encoded.index[not_null_mask], columns=transformed_columns_prefixed)
        df_glass_one_hot_encoded = df_glass_one_hot_encoded.join(transformed_df)

        # Remove the 'glass' column after transformation
        df_glass_one_hot_encoded.drop('glass', axis=1, inplace=True)

    df_regional_varietals_one_hot_encoded = df_combined_back[['varietals']]
    mlb = MultiLabelBinarizer(sparse_output=True)
    not_null_mask = ~df_regional_varietals_one_hot_encoded['varietals'].isnull()
    if not_null_mask.any():
        transformed_data = mlb.fit_transform(df_regional_varietals_one_hot_encoded.loc[not_null_mask, 'varietals'])
        transformed_columns = mlb.classes_
        transformed_columns_prefixed = ['varietals_' + col for col in transformed_columns]
        transformed_df = pd.DataFrame.sparse.from_spmatrix(transformed_data, index=df_regional_varietals_one_hot_encoded.index[not_null_mask], columns=transformed_columns_prefixed)
        df_regional_varietals_one_hot_encoded = df_regional_varietals_one_hot_encoded.join(transformed_df)

        # Remove the 'glass' column after transformation
        df_regional_varietals_one_hot_encoded.drop('varietals', axis=1, inplace=True)

    df_all_one_hot_encoded = df_all_one_hot_encoded.join(df_glass_one_hot_encoded)
    df_all_one_hot_encoded = df_all_one_hot_encoded.join(df_regional_varietals_one_hot_encoded)
    df_all_one_hot_encoded.drop(['glass', 'varietals'], axis=1, inplace=True)
    # df_all_one_hot_encoded.drop(['glass'], axis=1, inplace=True)

    # Normalise integer columns
    dryness_scaler = MinMaxScaler(feature_range=(-1, 1))
    dryness_values = df_all_one_hot_encoded['dryness'].dropna().values.reshape(-1, 1)  # Extract non-null 'dryness' values
    normalized_dryness = dryness_scaler.fit_transform(dryness_values)  # Normalize the values
    # Replace 'dryness' values with normalized values
    df_all_one_hot_encoded.loc[df_all_one_hot_encoded['dryness'].notnull(), 'dryness'] = normalized_dryness

    to_normalise = ['acidity',
                    'tannin',
                    'body'
                ]
    scaler = MinMaxScaler(feature_range=(0, 1))
    for col in to_normalise:
        curr_values = df_all_one_hot_encoded[col].dropna().values.reshape(-1, 1)  # Extract non-null 'acid' values
        normalized_values = scaler.fit_transform(curr_values)  # Normalize the values
        # Replace original values with normalized values
        df_all_one_hot_encoded.loc[df_all_one_hot_encoded[col].notnull(), col] = normalized_values

    df_one_wine_one_day_with_product_metafields = df_all_one_hot_encoded.copy()

    # breaking down order_date into its sin and cos
    df_one_wine_one_day_with_product_metafields["year"]=pd.to_datetime(df_one_wine_one_day_with_product_metafields["order_date"]).dt.year
    df_one_wine_one_day_with_product_metafields["month"]=pd.to_datetime(df_one_wine_one_day_with_product_metafields["order_date"]).dt.month
    df_one_wine_one_day_with_product_metafields["day"]=pd.to_datetime(df_one_wine_one_day_with_product_metafields["order_date"]).dt.day
    df_one_wine_one_day_with_product_metafields["day_name"]=pd.to_datetime(df_one_wine_one_day_with_product_metafields["order_date"]).dt.weekday

    def encode(df, col_name, max_val):
        df[col_name + '_sin'] = np.sin(2 * np.pi * df[col_name]/max_val)
        df[col_name + '_cos'] = np.cos(2 * np.pi * df[col_name]/max_val)
        return df

    df_one_wine_one_day_with_product_metafields = encode(df_one_wine_one_day_with_product_metafields, 'month', 12)
    df_one_wine_one_day_with_product_metafields = encode(df_one_wine_one_day_with_product_metafields, 'day', 31)
    df_one_wine_one_day_with_product_metafields = encode(df_one_wine_one_day_with_product_metafields, 'day_name', 6)

    target_product_with_cleaned_metafields = df_one_wine_one_day_with_product_metafields.drop(['order_date',
                                                                            'month',
                                                                            'day',
                                                                            'day_name'
                                                                        ], axis=1)
    return target_product_with_cleaned_metafields

# TRAINING MLR FUNCTIONS BELOW

def train_mlr_demand_prediction():
    # 1. get orders + raw metafields from services.get_metafields_for_orders --> use cara's directly instead of the csv like on jupyter
    # 1a. if empty, call bbw_product.get_products_from_shopify
    # 2. run preprocess_orders_and_metafields
    # 3. train mlr and get the pickle file
    print('---------START OF train_mlr_demand_prediction----------')
    # PART 1: get orders + raw metafields from services.get_metafields_for_orders
    orders_with_metafields_from_db, errors1 = get_metafields_for_all_orders()
    # for x in orders_with_metafields_from_db:
    #     print(x)

    pd.set_option('display.max_rows', None)
    orders_with_metafields_original = pd.DataFrame(orders_with_metafields_from_db)
    # print(orders_with_metafields_original.info())
    # print(orders_with_metafields_original.head(5))

    # PART 2: run preprocess_orders_and_metafields
    df_to_use_for_mlr = preprocess_orders_and_metafields(orders_with_metafields_original)
    print('---------AFTER preprocessing----------')
    pd.set_option('display.max_columns', None)
    print(df_to_use_for_mlr.info())
    print(df_to_use_for_mlr.head(5))
    # print(df_to_use_for_mlr.columns)

    print('---------TRAINING MLR----------')
    # Train-Test Split
    y = df_to_use_for_mlr['total_daily_sale']
    X = df_to_use_for_mlr.drop(['item_id', 'total_daily_sale'], axis=1).astype(float)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=69)
    print("X_train shape:", X_train.shape)
    print("X_test shape:", X_test.shape)
    print("y_train shape:", y_train.shape)
    print("y_test shape:", y_test.shape)
    
    # Selecting n Features using RFE 
    n = 10 # hyperparamter of how many features to keep. Can adjust accordingly
    lr_estimator = LinearRegression()
    rfe = RFE(lr_estimator, n_features_to_select=n, step=1)
    selector = rfe.fit(X_train,y_train)
    # RFE Feature Ranking
    rfe_ranking = pd.DataFrame({'rank' : selector.ranking_, 'support': selector.support_, 'features' : X_train.columns}).sort_values(by='rank',ascending=True)
    # Selected Features
    selected_features = rfe_ranking.loc[rfe_ranking['rank'] == 1,'features'].values

    def ols_fit(y,X) : 
        X_train_sm = sm.add_constant(X)
        model = sm.OLS(y,X_train_sm).fit()
        # print(model.summary()) # uncomment for OLS regression info
        return model
    def vif(X) : 
        df = sm.add_constant(X)
        vif = [variance_inflation_factor(df.values,i) for i in range(df.shape[1])]
        vif_frame = pd.DataFrame({'vif' : vif[0:]},index = df.columns).reset_index()
        # print(vif_frame.sort_values(by='vif',ascending=False)) # uncomment for VIF info

    # Training RFE + OLS Regression
    features_1 = selected_features
    final_model = ols_fit(y_train,X_train[features_1])
    vif(X_train[selected_features])

    # Inference
    X_train_sm = sm.add_constant(X_train[selected_features])
    y_train_pred = final_model.predict(X_train_sm)
    X_train_new=X_train[selected_features]
    X_test_new = X_test[X_train_new.columns]
    X_test_new = sm.add_constant(X_test_new)
    print('--------------------------------TO SEE FORMAT OF X INFERENCE--------------------------------')
    print(X_test_new.info())
    print(X_test_new)
    print('--------------------------------END OF FORMAT OF X INFERENCE--------------------------------')
    y_test_pred = final_model.predict(X_test_new)

    # Evaluation
    comparison = pd.DataFrame({'Actual': y_test, 'Predicted': y_test_pred})
    print('-------------------10 samples of ground truth vs prediction-------------------')
    print(comparison.head(10))
    print()
    mse = mean_squared_error(y_test, y_test_pred)
    rmse = mean_squared_error(y_test, y_test_pred, squared=False)
    rsquared_test = r2_score(y_test, y_test_pred)
    rsquared_train = r2_score(y_train, y_train_pred)
    n = X_test.shape[0]
    p = X_test.shape[1]
    adjusted_r2 = round(1-(1-rsquared_test)*(n-1)/(n-p-1),2)
    print('Mean Squared Error = ',round(mse,3))
    print("Root Mean Squared Error (RMSE):", round(rmse,3))
    print('R-squared for train data:',round(rsquared_train,2))
    print('R-squared for test data:',round(rsquared_test,2))
    print('Adjusted R-Squared for test data = ',round(adjusted_r2,3))

    # Saving the Model as a pickle file
    directory = 'saved_pickle_models'
    filename = 'ols_regression_latest.sav'
    if not os.path.exists(directory):
        os.makedirs(directory)
    filepath = os.path.join(directory, filename)
    filename = 'saved_pickle_models/ols_regression_latest.sav'
    pickle.dump(final_model, open(filename, 'wb'))
    
    result = f"The model has been successfully saved to {filepath}."
    print(result)
    return result

def preprocess_orders_and_metafields(orders_with_metafields_original): # to use in train_mlr_demand_prediction
    df_useless_thrown = orders_with_metafields_original.copy(deep=True)
    df_useless_thrown['order_date'] = pd.to_datetime(df_useless_thrown['order_datetime']).dt.date
    useless_columns = ['checkout_token',
                   'shopify_product_id',
                   'order_datetime'
                  ]
    
    df_useless_thrown = df_useless_thrown.drop(useless_columns, axis=1)
    df_useless_thrown.rename(columns={'product_name':'item_id'}, inplace=True)

    # throw products which do not have all the relevant metafields
    df_useless_thrown = df_useless_thrown.dropna()
    print('DEBUG HERE')
    print(df_useless_thrown.columns)

    # Pre-process each metafield one by one
    df_metafield_temp = df_useless_thrown[['grape']]
    df_metafields_cleaned = df_metafield_temp.copy()
    df_metafields_cleaned['grape'] = df_metafields_cleaned['grape'].str.split(r'[;/\(\)]').str[0].str.strip()
    df_metafields_cleaned['grape'] = df_metafields_cleaned['grape'].str.lower()
    df_metafields_cleaned['grape'] = df_metafields_cleaned['grape'].str.replace(' ', '_')
    df_metafields_cleaned['grape'] = df_metafields_cleaned['grape'].apply(lambda x: unidecode(x) if pd.notnull(x) and isinstance(x, str) else x)
    
    df_metafield_temp = df_useless_thrown[['product_type']]
    df_metafields_cleaned['product_type'] = df_metafield_temp['product_type']
    df_metafields_cleaned['product_type'] = df_metafields_cleaned['product_type'].str.lower()
    df_metafields_cleaned['product_type'] = df_metafields_cleaned['product_type'].str.replace(' ', '_')

    df_metafield_temp = df_useless_thrown[['acidity']]
    df_metafields_cleaned['acidity'] = df_metafield_temp['acidity']
    acidity_map = {'Light': 1, 'Medium -': 2, 'Medium': 3, 'Medium +': 4, 'High': 5}
    df_metafields_cleaned['acidity'] = df_metafields_cleaned['acidity'].replace(acidity_map)

    df_metafield_temp = df_useless_thrown[['country']]
    df_metafields_cleaned['country'] = df_metafield_temp['country']
    country_map = {'United States of America': 'usa', 'United Kingdom': 'uk', 'N. Macedonia': 'north macedonia'}
    df_metafields_cleaned['country'] = df_metafields_cleaned['country'].replace(country_map)
    df_metafields_cleaned['country'] = df_metafields_cleaned['country'].str.lower()
    df_metafields_cleaned['country'] = df_metafields_cleaned['country'].str.replace(' ', '_')

    df_metafield_temp = df_useless_thrown[['dryness']]
    df_metafields_cleaned['dryness'] = df_metafield_temp['dryness']
    dryness_map = {'Very Dry': -2, 'Dry': -1, 'Neutral': 0, 'Sweet': 1, 'Very Sweet': 2}
    df_metafields_cleaned['dryness'] = df_metafields_cleaned['dryness'].replace(dryness_map)

    df_metafield_temp = df_useless_thrown[['fermentation']]
    df_metafields_cleaned['fermentation'] = df_metafield_temp['fermentation']
    df_metafields_cleaned['fermentation'] = df_metafields_cleaned['fermentation'].str.lower()
    df_metafields_cleaned['fermentation'] = df_metafields_cleaned['fermentation'].str.replace(' ', '_')

    df_metafield_temp = df_useless_thrown[['glass']]
    df_metafields_cleaned['glass'] = df_metafield_temp['glass']
    def clean_glass(value):
        if pd.notnull(value):
            # Remove full stops and others
            replaced_value = value.replace('.', '').replace('blac', 'black').replace('hint of ', '').replace(' and ', ',').replace(' & ', ',').replace(', ', ',')
            # Trim typo of comma at the end without any fruit after that
            if replaced_value[-1] == ',':
                replaced_value = replaced_value[:-1]
            
            # Convert plural to singular
            words = [word.strip() for word in replaced_value.split(',')]
            singular_words = [p.singular_noun(word) if p.singular_noun(word) else word for word in words]
            # Finally, remove spaces, convert to lowercase and fix typos
            modified_words = [word.lower().replace(" ", "").replace("vibrantcitruszest", "citrus").replace("wideopeningforpeachsweetness", "peach").replace('liquorice', 'licorice').replace('blackk', 'black').replace('mineraly', 'mineral').replace('leathery', 'leather').replace('citrusy', 'citrus').replace('citruss', 'citrus').replace('citru', 'citrus').replace('citrussy', 'citrus').replace('citruss', 'citrus').replace('lavendar', 'lavender').replace('sweetspicines', 'sweetspice') for word in singular_words]
            return modified_words
        return value
    df_metafields_cleaned['glass'] = df_metafields_cleaned['glass'].apply(clean_glass)

    df_metafield_temp = df_useless_thrown[['region']]
    df_metafields_cleaned['region'] = df_metafield_temp['region']
    df_metafields_cleaned['region'] = df_metafields_cleaned['region'].str.split(r'[;,&/\(\)]').str[0].str.strip()
    df_metafields_cleaned['region'] = df_metafields_cleaned['region'].str.lower()
    df_metafields_cleaned['region'] = df_metafields_cleaned['region'].str.replace(' ', '_')

    df_metafield_temp = df_useless_thrown[['tannin']]
    df_metafields_cleaned['tannin'] = df_metafield_temp['tannin']
    tannin_map = {'Light': 1, 'Medium -': 2, 'Medium': 3, 'Medium +': 4, 'High': 5}
    df_metafields_cleaned['tannin'] = df_metafields_cleaned['tannin'].replace(tannin_map)

    df_metafield_temp = df_useless_thrown[['body']]
    df_metafields_cleaned['body'] = df_metafield_temp['body']
    body_map = {'Light': 1, 'Medium -': 2, 'Medium': 3, 'Medium +': 4, 'Full': 5}
    df_metafields_cleaned['body'] = df_metafields_cleaned['body'].replace(body_map)

    df_metafield_temp = df_useless_thrown[['varietals']]
    df_metafields_cleaned['varietals'] = df_metafield_temp['varietals']
    def process_varietals(varietals):
        if pd.notnull(varietals):
            varietals = literal_eval(varietals)
            processed_varietals = []
            for variety in varietals:
                processed_variety = variety.split(' (')[0].lower().replace(' ', '_')
                if isinstance(processed_variety, str):
                    processed_variety = unidecode(processed_variety)
                processed_varietals.append(processed_variety)
            return processed_varietals
        else:
            return varietals
    df_metafields_cleaned['varietals'] = df_metafields_cleaned['varietals'].apply(process_varietals)

    # combine back after first preprocessing
    df_combined_back = df_useless_thrown
    common_columns = df_combined_back.columns.intersection(df_metafields_cleaned.columns).tolist()
    for col in common_columns:
        df_combined_back[col] = df_metafields_cleaned[col]

    # one-hot encoding
    df_all_one_hot_encoded = df_combined_back
    to_one_hot = ['product_type',
                'country',
                'fermentation',
                'grape',
                'region'
            ]
    for col in to_one_hot:
        not_null_mask = ~df_all_one_hot_encoded[col].isnull()

        # Create one-hot encoded columns with the prefix 'country_'
        one_hot_encoded = pd.get_dummies(df_all_one_hot_encoded.loc[not_null_mask, col], prefix=col)

        # Join the one-hot encoded data to the original DataFrame
        df_all_one_hot_encoded = df_all_one_hot_encoded.join(one_hot_encoded)

        # Remove the original 'country' column after one-hot encoding
        df_all_one_hot_encoded.drop(col, axis=1, inplace=True)
    
    df_glass_one_hot_encoded = df_combined_back[['glass']]
    mlb = MultiLabelBinarizer(sparse_output=True)
    not_null_mask = ~df_glass_one_hot_encoded['glass'].isnull()
    if not_null_mask.any():
        transformed_data = mlb.fit_transform(df_glass_one_hot_encoded.loc[not_null_mask, 'glass'])

        # Join the transformed data to the DataFrame and add the prefix 'glass_'
        transformed_columns = mlb.classes_
        transformed_columns_prefixed = ['glass_' + col for col in transformed_columns]
        transformed_df = pd.DataFrame.sparse.from_spmatrix(transformed_data, index=df_glass_one_hot_encoded.index[not_null_mask], columns=transformed_columns_prefixed)
        df_glass_one_hot_encoded = df_glass_one_hot_encoded.join(transformed_df)

        # Remove the 'glass' column after transformation
        df_glass_one_hot_encoded.drop('glass', axis=1, inplace=True)

    df_regional_varietals_one_hot_encoded = df_combined_back[['varietals']]
    mlb = MultiLabelBinarizer(sparse_output=True)
    not_null_mask = ~df_regional_varietals_one_hot_encoded['varietals'].isnull()
    if not_null_mask.any():
        transformed_data = mlb.fit_transform(df_regional_varietals_one_hot_encoded.loc[not_null_mask, 'varietals'])
        transformed_columns = mlb.classes_
        transformed_columns_prefixed = ['varietals_' + col for col in transformed_columns]
        transformed_df = pd.DataFrame.sparse.from_spmatrix(transformed_data, index=df_regional_varietals_one_hot_encoded.index[not_null_mask], columns=transformed_columns_prefixed)
        df_regional_varietals_one_hot_encoded = df_regional_varietals_one_hot_encoded.join(transformed_df)

        # Remove the 'glass' column after transformation
        df_regional_varietals_one_hot_encoded.drop('varietals', axis=1, inplace=True)

    df_all_one_hot_encoded = df_all_one_hot_encoded.join(df_glass_one_hot_encoded)
    df_all_one_hot_encoded = df_all_one_hot_encoded.join(df_regional_varietals_one_hot_encoded)
    df_all_one_hot_encoded.drop(['glass', 'varietals'], axis=1, inplace=True)
    # df_all_one_hot_encoded.drop(['glass'], axis=1, inplace=True)

    # Normalise integer columns
    dryness_scaler = MinMaxScaler(feature_range=(-1, 1))
    dryness_values = df_all_one_hot_encoded['dryness'].dropna().values.reshape(-1, 1)  # Extract non-null 'dryness' values
    normalized_dryness = dryness_scaler.fit_transform(dryness_values)  # Normalize the values
    # Replace 'dryness' values with normalized values
    df_all_one_hot_encoded.loc[df_all_one_hot_encoded['dryness'].notnull(), 'dryness'] = normalized_dryness

    to_normalise = ['acidity',
                    'tannin',
                    'body'
                ]
    scaler = MinMaxScaler(feature_range=(0, 1))
    for col in to_normalise:
        curr_values = df_all_one_hot_encoded[col].dropna().values.reshape(-1, 1)  # Extract non-null 'acid' values
        normalized_values = scaler.fit_transform(curr_values)  # Normalize the values
        # Replace original values with normalized values
        df_all_one_hot_encoded.loc[df_all_one_hot_encoded[col].notnull(), col] = normalized_values

    df_to_handle_date = df_all_one_hot_encoded.copy(deep=True)
    df_sales_info = df_to_handle_date[['order_date',
                    'item_id',
                    'item_quantity',
                    'item_price'
                ]]
    df_product_info = df_to_handle_date.drop(['order_date',
                    'item_quantity',
                    'item_price'
                ], axis=1)
    df_product_info = df_product_info.drop_duplicates(subset=['item_id'])

    grouped = df_to_handle_date.groupby(['order_date', 'item_id']).agg({
        'item_quantity': 'sum',
        'item_price': 'first'
    }).reset_index()
    # Rename item_quantity to total_daily_sale
    grouped = grouped.rename(columns={'item_quantity': 'total_daily_sale'})
    grouped['total_daily_sale'] = grouped['total_daily_sale'].astype(float)
    # Save the results into df_one_wine_one_day
    df_one_wine_one_day = grouped

    # Merge the two DataFrames on 'item_id'
    df_one_wine_one_day_with_product_metafields = df_one_wine_one_day.merge(df_product_info, on='item_id', how='left')

    # breaking down order_date into its sin and cos
    df_one_wine_one_day_with_product_metafields["year"]=pd.to_datetime(df_one_wine_one_day_with_product_metafields["order_date"]).dt.year
    df_one_wine_one_day_with_product_metafields["month"]=pd.to_datetime(df_one_wine_one_day_with_product_metafields["order_date"]).dt.month
    df_one_wine_one_day_with_product_metafields["day"]=pd.to_datetime(df_one_wine_one_day_with_product_metafields["order_date"]).dt.day
    df_one_wine_one_day_with_product_metafields["day_name"]=pd.to_datetime(df_one_wine_one_day_with_product_metafields["order_date"]).dt.weekday

    def encode(df, col_name, max_val):
        df[col_name + '_sin'] = np.sin(2 * np.pi * df[col_name]/max_val)
        df[col_name + '_cos'] = np.cos(2 * np.pi * df[col_name]/max_val)
        return df

    df_one_wine_one_day_with_product_metafields = encode(df_one_wine_one_day_with_product_metafields, 'month', 12)
    df_one_wine_one_day_with_product_metafields = encode(df_one_wine_one_day_with_product_metafields, 'day', 31)
    df_one_wine_one_day_with_product_metafields = encode(df_one_wine_one_day_with_product_metafields, 'day_name', 6)

    df_to_use_for_mlr = df_one_wine_one_day_with_product_metafields.drop(['order_date',
                                                                            'month',
                                                                            'day',
                                                                            'day_name'
                                                                        ], axis=1)

    return df_to_use_for_mlr

def load_arima_sarimax_and_get_demand_prediction(bbw_product, product_name):
    # get orders from CSV
    df = pd.read_csv('datasets/cleaned_orders.csv')
    df['order_date'] = pd.to_datetime(df['order_date'])
    grouped = df[['order_date', 'item_id', 'item_quantity']]
    groupedbyitem = grouped.groupby('item_id', group_keys=True).apply(lambda x:x)
    sample = groupedbyitem[groupedbyitem['item_id']==product_name]
    if len(sample) == 0:
        return False, False
    sample = sample.groupby('order_date')['item_quantity'].sum().reset_index()
    sample = sample.set_index('order_date')

    # get orders from shopify
    """ orders = get_orders_by_product_id(bbw_product['shopify_product_id'])
    if len(orders) == 0:
        return [], [], 'No orders found for this product.'
    df = pd.DataFrame(orders)
    df['order_datetime'] = pd.to_datetime(df['order_datetime'])
    df['order_date'] = df['order_datetime'].dt.date
    df['order_date'] = pd.to_datetime(df['order_date'])
    grouped = df[['order_date', 'product_name', 'item_quantity']]
    groupedbyitem = grouped.groupby('product_name', group_keys=True).apply(lambda x:x)
    sample = groupedbyitem.groupby('order_date')['item_quantity'].sum().reset_index()
    sample = sample.set_index('order_date') """

    # resample - monthly
    monthly_sales = pd.DataFrame()
    monthly_sales['sales'] = sample['item_quantity'].resample('MS').mean()

    # Training time
    x = monthly_sales.index # month
    y = monthly_sales.sales # monthly sales
    y = y.fillna(0)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=69, shuffle=False)

    # ARIMA
    auto_arima(y_train, test='adf',seasonal=True, trace=True, error_action='ignore', suppress_warnings=True)
    auto_arima(y,test='adf',
               seasonal=True,
               trace=True,
               error_action='ignore',
               suppress_warnings=True,
               stepwise=True)
    model_arima = ARIMA(y_train, order=(1,1,1)).fit()
    pred_arima = model_arima.predict(start=len(y_train), end=(len(y)-1),dynamic=True)

    # SARIMAX
    # model_sarimax = sm.tsa.statespace.SARIMAX(y_train,order=(1, 1, 1),seasonal_order=(1,1,1,12)) # original
    model_sarimax = sm.tsa.statespace.SARIMAX(y_train,order=(1, 0, 0),seasonal_order=(1,0,0,12))
    results_sarimax = model_sarimax.fit()
    pred_sarimax = results_sarimax.predict(start= len(y_train), end=(len(y)-1),dynamic=True)

    # Ensemble Learning
    rmse_results = []
    mape_results = []

    for weight in np.arange(0.1, 1.0, 0.1):
        # Calculate the weighted average of the two predictions
        weighted_average = (weight * np.array(pred_arima)) + ((1-weight) * np.array(pred_sarimax))
        
        # Calculate MSE and MAPE
        rmse = mean_squared_error(y_test, weighted_average, squared=False)
        mape = mean_absolute_percentage_error(y_test, weighted_average)
        
        # Append results to the lists
        rmse_results.append((weight, rmse))
        mape_results.append((weight, mape))
    
    # Find the weight with the lowest RMSE
    # Can change to MAPE also
    min_rmse_weight = None
    min_rmse = float('inf')
    for weight, rmse in rmse_results:
        if rmse < min_rmse:
            min_rmse = rmse
            min_rmse_weight = weight
    
    # Showtime
    future_sales_arima = model_arima.predict(start=len(y), end=(len(y)+6))
    future_sales_sarimax = results_sarimax.predict(start=len(y), end=(len(y)+6))
    weight_arima = min_rmse_weight
    future_sales_weighted = (weight_arima * future_sales_arima) + ((1-weight_arima) * future_sales_sarimax)

    y_df = pd.DataFrame({
        'Historical_Demand_Date': y.index,
        'Historical_Demand_Sales': y.values
        })
    historical_demand = y_df.to_dict('records')

    future_sales_weighted_df = pd.DataFrame({
        'Predicted_Demand_Date': future_sales_weighted.index, 
        'Predicted_Demand_Sales': future_sales_weighted.values
        })
    predicted_demand = future_sales_weighted_df.to_dict('records')

    return historical_demand, predicted_demand


""" def post_prediction_to_db(predicted_demand):
    product_name = predicted_demand[0]['Product_Name']
    
    # Get existing records with the same product_name
    existing_records = PredictedDemand.query.filter_by(Product_Name=product_name).all()

    if existing_records:
        # Delete existing records
        for record in existing_records:
            db.session.delete(record)
    
    # Insert new records
    try:
        for pdt in predicted_demand:
            to_db = PredictedDemand(**pdt)
            db.session.add(to_db)
        
        db.session.commit()
        return jsonify(
            {
                "code": 201,
                "data": predicted_demand,
                "message": "Predicted demand for this product has been successfully stored into the database."
            }
        ), 201
    except Exception as e:
        db.session.rollback()  # Rollback changes if an error occurs
        return jsonify(
            {
                "code": 500,
                "data": pdt,
                "message": "An error occurred creating a particular predicted demand record.",
                "error": str(e)
            }
        ), 500 """

# def get_all_predicted_demand():
#     predicted_demand_list = PredictedDemand.query.all()
    
#     if predicted_demand_list:
#         return jsonify(
#             {
#                 "code": 200,
#                 "data": {
#                     "predicted_demand": [predicted_demand.json() for predicted_demand in predicted_demand_list]
#                 }
#             }
#         )
#     return jsonify(
#         {
#             "code": 404,
#             "message": "There are no Predicted Demand."
#         }
#     ), 404

""" def get_product_predicted_demand(product_name):
    predicted_demand_list = PredictedDemand.query.filter_by(Product_Name = product_name).all()
    if predicted_demand_list:
        return jsonify(
            {
                "code": 200,
                "data": {
                    "predicted_demand": [predicted_demand.json() for predicted_demand in predicted_demand_list]
                }
            }
        )
    return jsonify(
        {
            "code": 404,
            "message": 'No predicted demand history for product named ' + str(product_name) 
        }
    ), 404 """
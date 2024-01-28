import pandas as pd
import time

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
# from bs4 import BeautifulSoup
#https://googlechromelabs.github.io/chrome-for-testing/#stable
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains

from models.matched_product_listing import *
from models.unmatched_product_listing import *
from models.scrape_logs import *


#helper function

# chromium initialization
def webdriver_initialize(url):
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    driver.maximize_window()
    driver.get(url)
    time.sleep(3)
    return driver

def scrape_wine_delivery(webscrape_params): # takes in 2 strings: category, country
    #url = "https://wine.delivery/Buy-Wine-Online"
    # OR
    
    url = webscrape_params["website_url"]
    category = webscrape_params['category']
    country = webscrape_params['country']
    print(category)
    print(country)
    driver = webdriver_initialize(url)

    try:
        button = driver.find_element(By.XPATH, f"//button[text()='Accept']")
        button.click() # accept cookies
    except NoSuchElementException:
        pass

    # clear all filters - all wines to be selected, whole range of prices
    button = driver.find_element(By.XPATH, "//button[text()='Clear All']")
    button.click()

    # now, filter by the given parameters
    if category != '':
        try:
            button = driver.find_element(By.XPATH, f"//label[text()='{category}']")
            button.click()
        except NoSuchElementException:
            pass
    if country != '':
        try:
            button = driver.find_element(By.XPATH, f"//label[text()='{country}']")
            button.click()
        except NoSuchElementException:
            pass
    
    time.sleep(3)

    last_height = driver.execute_script("return document.body.scrollHeight")
    count = 50 # pre-set number of scrolls to minimise run time

    for i in range(count): # keep scrolling down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    time.sleep(3)
    try:
        items = driver.find_elements(By.XPATH, "//div[@class='sc-kAyceB eryWgk']")
        # format of each card:
        # # vintage, type (e.g. red wine), region/country, price, discounted price, stock info
        # discounted price & stock info are optional fields
        df = pd.DataFrame(columns=['Product_Name', 'Scraped_Data_New_Price', 'Scraped_Data_Old_Price'])

        for item in items:
            info = item.text
            info = info.split('\n')
            final = [info[0]] # get vintage name
            old_price = 0.0
            if ("S$" in info[-1]) == True: # check if there is NO stock info
                new_price = float(info[-1].replace('S$',''))
                final.append(new_price) # no stock info, means last value is a price
            else:
                new_price = float(info[-2].replace('S$',''))
                final.append(new_price) # 2nd last value must be a price
            final.append(old_price)
            df.loc[len(df)] = final # append to the end of the dataframe

        
        df['Supplier_Name'] = 'wine.delivery'
        df['Product_In_Stock'] = True
        df = df[['Product_Name', 'Supplier_Name', 'Product_In_Stock', 'Scraped_Data_Old_Price', 'Scraped_Data_New_Price']]
        print(df)
        return df

    except NoSuchElementException:
        pass
    return {
        "code": 500,
        "message": "Product elements not found on the webpage or have not loaded. Check XPATH of products or extend wait time."
    }


# Webscrape script gets datetime to store into the webscrape function with 
def scrape_vivino(webscrape_params):   
    #url = "https://www.vivino.com/explore"
    # OR
    regions = []
    countries = []
    winetypes = []
    url = webscrape_params["website_url"]
    if webscrape_params['category'] != "":
        winetypes = webscrape_params['category'].split(", ")
    if webscrape_params['region'] != "":
        regions = webscrape_params['region'].split(", ")
    if webscrape_params['country'] != "":
        countries = webscrape_params['country'].split(", ")
    rating = webscrape_params['rating']

    driver = webdriver_initialize(url)
    

    slider = driver.find_element(By.XPATH, "//*[@id='explore-page-app']/div/div/div[2]/div[1]/div/div[2]/div[2]/div[2]/div/div[4]")
    move = ActionChains(driver)
    move.click_and_hold(slider).move_by_offset(-100, 0).release().perform()
    # # right handle
    slider = driver.find_element(By.XPATH, "//*[@id='explore-page-app']/div/div/div[2]/div[1]/div/div[2]/div[2]/div[2]/div/div[5]")
    move = ActionChains(driver)
    move.click_and_hold(slider).move_by_offset(200, 0).release().perform()

    try:
        #button = driver.find_element(By.XPATH, f"//span[text()='Only show wines with a discount']")
        #button.click() # remove: default on the url is to only show discounted
        button = driver.find_element(By.XPATH, "//span[text()='Red']")
        button.click() # remove default red wine selection
    except NoSuchElementException:
        pass

    if rating != '':
        try: # get only items that are rated a certain way
            button = driver.find_element(By.XPATH, f"//div[text()='{rating}']")
            button.click()
        except NoSuchElementException:
            pass
        time.sleep(2)

    if len(winetypes) > 0:
        for cat in winetypes:
            print(cat)
            try: 
                button = driver.find_element(By.XPATH, f"//span[text()='{cat}']")
                button.click()
            except NoSuchElementException:
                pass
            time.sleep(2)
    
    if len(regions) > 0:
        for region in regions:
            try: 
                button = driver.find_element(By.XPATH, f"//span[text()='{region}']")
                button.click()
            except NoSuchElementException:
                pass
            time.sleep(2)

    if len(countries) > 0:
        for country in countries:
            print(country)
            try: 
                button = driver.find_element(By.XPATH, f"//span[text()='{country}']")
                button.click()
            except NoSuchElementException:
                pass
            time.sleep(2)
    
    # for infinite scrolling
    last_height = driver.execute_script("return document.body.scrollHeight")
    count = 50 # pre-set number of scrolls to minimise run time
    for i in range(count):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    #wait awhile before starting to scrape
    time.sleep(2)
    # scrape data
    wine_names = []
    wine_titles = []
    wine_prices = []
    wine_old_prices = 0.0

    try:
        wines = driver.find_elements(By.XPATH, "//div[@class='wineInfoVintage__vintage--VvWlU wineInfoVintage__truncate--3QAtw']")
        prices = driver.find_elements(By.XPATH, "//div[@class='addToCartButton__price--qJdh4']/div[2]")
        titles = driver.find_elements(By.XPATH, "//div[@class='wineInfoVintage__truncate--3QAtw']")
        for i in range(len(wines)):
            wine_names.append(wines[i].text)
            wine_prices.append(float(prices[i].text))
            wine_titles.append(titles[i].text)
    except NoSuchElementException:
        print("The elements does not exist / has not loaded yet.")

    df = pd.DataFrame(
        {
            'Product_Name': wine_names,
            'Scraped_Data_New_Price': wine_prices,
            'Scraped_Data_Old_Price' : wine_old_prices
        })
    df['Supplier_Name'] = 'vivino'
    df['Product_In_Stock'] = True
    df = df[['Product_Name', 'Supplier_Name', 'Product_In_Stock', 'Scraped_Data_Old_Price', 'Scraped_Data_New_Price']]
    return df


def scrape_pivene(webscrape_params): 
    #url = "https://www.pivene.com/collections/all"
    # OR
    url = webscrape_params["website_url"]
    driver = webdriver_initialize(url)

    try: # get rid of the pop-up
        button = driver.find_element(By.XPATH, "//button[@class='button button-1 mr-10 popup-confirm-yes']")
        button.click()
    except NoSuchElementException:
        pass
    
    i = 1 # page number
    df = pd.DataFrame(columns=['Product_Name', 'Scraped_Data_New_Price', 'Scraped_Data_Old_Price', 'Product_In_Stock'])
    while i <= 86: # 86 pages on the website
        try:
            old_price = 0.0
            # pdt_info = driver.find_elements(By.XPATH, "//div[@class='text-left product-each__bottom']")
            normal_wines = driver.find_elements(By.XPATH, "//div[@class='product-each overflow relative form-parent boost-pfs-filter-product-item boost-pfs-filter-product-item-grid boost-pfs-filter-grid-width-3 boost-pfs-filter-grid-width-mb-2 boost-pfs-action-list-enabled']")
            for card in normal_wines:
                wine = card.text.split('\n')
                if wine[0].isnumeric():
                    name = wine[2]
                    temp = [name]
                else:
                    name = wine[1]
                    temp = [name]

                if 'SGD' in wine[2]:
                    price = wine[2].replace(' SGD','').replace(',','')
                    temp.append(float(price))
                    temp.append(float(old_price))
                else:
                    price = wine[3].replace(' SGD','').replace(',','')
                    temp.append(float(price))
                    temp.append(float(old_price))
                temp.append(True)
                df.loc[len(df)] = temp # append to the end of dataframe
        except NoSuchElementException:
            pass
        try: # for wines on sale (different class name)
            old_price = 0.0
            wines_on_sale = driver.find_elements(By.XPATH, "//div[@class='product-each overflow relative form-parent boost-pfs-filter-product-item boost-pfs-filter-product-item-grid boost-pfs-filter-grid-width-3 boost-pfs-filter-grid-width-mb-2 on-sale boost-pfs-action-list-enabled']")
            for card in wines_on_sale:
                wine = card.text.split('\n')
                #website stupid put this wine as sales but turns out just don't have anymore but can't be bothered to change class.
                if wine[0] != 'SALE':
                    if wine[0].isnumeric():
                        name = wine[2]
                        temp = [name]
                    else:
                        name = wine[1]
                        temp = [name]
                    if 'SGD' in wine[2]:
                        price = wine[2].replace(' SGD','').replace(',','')
                        temp.append(float(price))
                        temp.append(float(old_price))
                    else:
                        price = wine[3].replace(' SGD','').replace(',','')
                        temp.append(float(price))
                        temp.append(float(old_price))
                #actually got sales.
                else:
                    if wine[1].isnumeric():
                        name = wine[3]
                        temp = [name]
                    else:
                        name = wine[2]
                        temp = [name]
                    if 'SGD' in wine[3]:
                        price = wine[3].replace(' SGD','').replace(',','')
                        temp.append(float(price))
                        temp.append(float(old_price))
                    else:
                        price = wine[4].replace(' SGD','').replace(',','')
                        temp.append(float(price))
                        temp.append(float(old_price))
                temp.append(True)
                df.loc[len(df)] = temp # append to the end of dataframe
        except NoSuchElementException:
            pass
        try: # for wines that are sold out
            old_price = 0.0
            wines_no_stock = driver.find_elements(By.XPATH, "//div[@class='product-each overflow relative form-parent boost-pfs-filter-product-item boost-pfs-filter-product-item-grid boost-pfs-filter-grid-width-3 boost-pfs-filter-grid-width-mb-2 sold-out boost-pfs-action-list-enabled']")
            for card in wines_no_stock:
                wine = card.text.split('\n')
                #print(wine)
                if wine[0] == 'SOLD OUT':
                    if wine[1].isnumeric():
                        name = wine[3]
                        temp = [name]
                    else:
                        name = wine[2]
                        temp = [name]
                    if 'SGD' in wine[3]:
                        price = wine[3].replace(' SGD','').replace(',','')
                        temp.append(float(price))
                        temp.append(float(old_price))
                    else:
                        price = wine[4].replace(' SGD','').replace(',','')
                        temp.append(float(price))
                        temp.append(float(old_price))
                temp.append(False) 
                df.loc[len(df)] = temp # append to the end of dataframe
        except NoSuchElementException:
            pass

        if (i == 1): # to deal with clicking through the pages
            button = driver.find_element(By.XPATH, "/html/body/div[11]/section/div[2]/div[3]/div[1]/div[2]/div[2]/ul/li[7]/a")
            driver.execute_script("arguments[0].click();", button)
            time.sleep(6)
        elif (i == 2 or i == 85):
            button = driver.find_element(By.XPATH, "/html/body/div[11]/section/div[2]/div[3]/div[1]/div[2]/div[2]/ul/li[8]/a")
            driver.execute_script("arguments[0].click();", button)
            time.sleep(6)
        elif (i == 3 or i == 84):
            button = driver.find_element(By.XPATH, "/html/body/div[11]/section/div[2]/div[3]/div[1]/div[2]/div[2]/ul/li[9]/a")
            #driver.execute_script("arguments[0].click();", button)
            button.click()
            time.sleep(6)
        elif (i == 4 or i == 83):
            button = driver.find_element(By.XPATH, "/html/body/div[11]/section/div[2]/div[3]/div[1]/div[2]/div[2]/ul/li[10]/a")
            driver.execute_script("arguments[0].click();", button)
            time.sleep(6)
        elif (i>=5 and i<83):
            button = driver.find_element(By.XPATH, "/html/body/div[11]/section/div[2]/div[3]/div[1]/div[2]/div[2]/ul/li[11]/a")
            driver.execute_script("arguments[0].click();", button)
            time.sleep(6)
        i += 1

    df['Supplier_Name'] = 'pivene'
    df.drop_duplicates(subset='Product_Name', keep='first', inplace=True)
    df = df[['Product_Name', 'Supplier_Name', 'Product_In_Stock', 'Scraped_Data_Old_Price', 'Scraped_Data_New_Price']]
    return df



def scrape_twdc(webscrape_params):

    #url = "https://twdc.com.sg/product-search/"
    url = webscrape_params["website_url"]
    driver = webdriver_initialize(url)

    i = 1
    df = pd.DataFrame(columns=['Product_Name'])
    while i <= 34: # 32 pages on the website
        try:
            wines = driver.find_elements(By.XPATH, "//h2[@class='woocommerce-loop-product__title']")
            for card in wines:
                df.loc[len(df)] = card.text
        except NoSuchElementException:
            pass
        # if (i < 13): # toggle to next page
        try:
            button = driver.find_element(By.XPATH, "//a[@class='next page-numbers']")
            driver.execute_script("arguments[0].click();", button)
            time.sleep(5)
        except NoSuchElementException:
            pass
        i += 1

    df['Supplier_Name'] = 'twdc'
    df['Scraped_Data_Old_Price'] = 0
    df['Scraped_Data_New_Price'] = 0
    df['Product_In_Stock'] = True
    df.drop_duplicates(subset='Product_Name', keep='first', inplace=True)
    df = df[['Product_Name', 'Supplier_Name', 'Product_In_Stock', 'Scraped_Data_Old_Price', 'Scraped_Data_New_Price']]
    return df

def scrape_winedelivery(webscrape_params):

    url = webscrape_params["website_url"]
    driver = webdriver_initialize(url)
    
    try: # clear cookies
        enter_button = driver.find_element(By.XPATH, "//a[@id='cookie_action_close_header']")
        driver.execute_script("arguments[0].click();", enter_button)
    except:
        pass
    
    i = 1
    df = pd.DataFrame(columns=['Product_Name', 'Scraped_Data_New_Price', 'Scraped_Data_Old_Price'])
    while i <= 57: # 57 pages on the website
        try:
            wines = driver.find_elements(By.XPATH, "//div[@class='product-content']")
            #print("The element exists.")
            old_price = 0.0
            for card in wines:
                wine = card.text.split('\n')
                if wine != ['']:
                    temp = [wine[0]] # wine name
                    #print(wine[0])
                    price = wine[1]
                    price = price.replace('$','').replace(',', '').split(' ')
                    if len(price) > 1: # len(list)>1 if there's discount
                        #did not check for price update for winedelivery as they have same 
                        # name but different price without stating the ml difference
                        #Example: BATASIOLO BARBERA D'ALBA DOC SOVRANA 2016
                        temp.append(float(price[1]))
                        temp.append(float(old_price))
                    else:
                        temp.append(float(price[0]))
                        temp.append(float(old_price))
                    df.loc[len(df)] = temp # append to the end of dataframe
        except NoSuchElementException:
            pass
        if (i < 57):
            try:
                button = driver.find_element(By.XPATH, "//a[@class='next page-numbers']")
                driver.execute_script("arguments[0].click();", button)
                time.sleep(5)
            except NoSuchElementException:
                pass
        i += 1
    
    df.drop_duplicates(subset="Product_Name", keep='first', inplace=True)
    df['Supplier_Name'] = 'winedelivery'
    df['Product_In_Stock'] = True
    df = df[['Product_Name', 'Supplier_Name', 'Product_In_Stock', 'Scraped_Data_Old_Price', 'Scraped_Data_New_Price']]
    return df


def scrape_winelistasia(webscrape_params):

    url = webscrape_params["website_url"]
    driver = webdriver_initialize(url)

    i = 1
    df = pd.DataFrame(columns=['Product_Name', 'Scraped_Data_New_Price', 'Product_In_Stock', 'Scraped_Data_Old_Price'])
    old_price = 0.0
    while i <= 15: # 15 pages on the website
        try:
            wines = driver.find_elements(By.XPATH, "//div[@class='product-grid__info']")
            for card in wines:
                wine = card.text.split('\n')
                if len(wine) >= 3:
                    if len(wine) > 1:
                        temp = [wine[0]]
                        price = wine[1]
                        price = price.replace('SGD ','').replace(',', '').split(' ')
                        if len(price) > 1: # len(list)>1 if there's discount
                            temp.append(float(price[1]))
                        else:
                            temp.append(float(price[0]))
                        if wine[2] == 'Sold out':
                            temp.append(False)
                        else:
                            temp.append(True)
                        
                        temp.append(old_price)
                        df.loc[len(df)] = temp
        except NoSuchElementException:
            pass
        
        try: # toggle pages
            button = driver.find_element(By.XPATH, "//a[@class='product-grid__paging--link product-grid--next js-products-next']")
            driver.execute_script("arguments[0].click();", button)
            time.sleep(10)
        except NoSuchElementException:
            print("The element does not exist / has not loaded yet.")
        i += 1
    
    df.drop_duplicates(subset="Product_Name", keep='first', inplace=True)
    df['Supplier_Name'] = 'winelistasia'

    df = df[['Product_Name', 'Supplier_Name', 'Product_In_Stock', 'Scraped_Data_Old_Price', 'Scraped_Data_New_Price']]
    return df


def scrape_winesonline(webscrape_params):
    url = webscrape_params["website_url"]    
    driver = webdriver_initialize(url)

    i = 1
    df = pd.DataFrame(columns=['Product_In_Stock', 'Product_Name', 'Scraped_Data_New_Price','Scraped_Data_Old_Price'])
    to_remove = ['Sale', 'New', 'Best Buy', 'ADD TO CART', 'NOTIFY ME', ' Sold Out']
    old_price = 0.0
    while i <= 29: # 29 pages on the website
        try:
            items = driver.find_elements(By.XPATH, "//div[@class='product-wrap']")
            for item in items:
                cleaned = []
                info = item.text
                info = info.split('\n')
                temp = []
                for x in info:
                    if x not in to_remove:
                        cleaned.append(x)
                    if 'Sold Out' in x:
                        temp.append(False)
                if len(temp) == 0:
                    temp.append(True)
                if '$' in cleaned[1]: # if sold out, may or may not be a price
                    temp.append(cleaned[0])
                    price = cleaned[1]
                    price = price.replace('S$', '').replace(',','').replace(' Sold Out','').replace('Sold Out ','').split(' ')
                    if len(price) > 1: # len(list)>1 if there's discount
                        temp.append(float(price[1]))
                        temp.append(float(old_price))
                    else:
                        temp.append(float(price[0]))
                        temp.append(float(old_price))
                    df.loc[len(df)] = temp
        except NoSuchElementException:
            pass
        if (i < 29):
            next_page_text = 'https://winesonline.com.sg/collections/wines?page=' + str(i + 1)
            try: 
                button = driver.find_element(By.XPATH, f"//a[@href='{next_page_text}']")
                driver.execute_script("arguments[0].click();", button)
                time.sleep(5)
            except NoSuchElementException:
                pass
        i += 1

    df.drop_duplicates(subset="Product_Name", keep='first', inplace=True)
    df['Supplier_Name'] = 'winesonline'
    df = df[['Product_Name', 'Supplier_Name', 'Product_In_Stock', 'Scraped_Data_Old_Price', 'Scraped_Data_New_Price']]

    return df


def scrape_wineswholesale(webscrape_params):
    url = webscrape_params["website_url"]    
    driver = webdriver_initialize(url)

    i = 1
    df = pd.DataFrame(columns=['Product_Name', 'Scraped_Data_New_Price', 'Scraped_Data_Old_Price', 'Product_In_Stock'])
    old_price = 0.0
    while i <= 76: # 76 pages on the website
        #if there is pop up remove it
        try:
            #<button title="Close (Esc)" type="button" class="mfp-close">×</button>
            button = driver.find_element(By.XPATH, "//button[@class='mfp-close']")
            button.click()
            #print("The element exists.")

        except NoSuchElementException:
            #print("The pop up have not appeared yet.")
            pass
        
        try:
            wines = driver.find_elements(By.XPATH, "//div[@class='right']")
            for wine in wines:
                card = wine.text.split('\n')
                if card != ['']:
                    temp = [card[0]] # product name/title
                    if card[1] != "Out of stock":
                        price = card[1]
                        price = price.replace(',','').split('$')
                        if len(price) > 2: # len(list)>2 if there's discount
                            temp.append(float(price[2]))
                            temp.append(float(old_price))
                        else:
                            temp.append(float(price[1]))
                            temp.append(float(old_price))
                        temp.append(True)
                    else:
                        temp.append(0)
                        temp.append(0)
                        temp.append(False)
                    df.loc[len(df)] = temp
        except NoSuchElementException:
            pass
        if (i == 1):
            try:
                button = driver.find_element(By.XPATH, "/html/body/div[3]/div[1]/div[2]/div[2]/div[2]/div/div/div/div/div[2]/div/div[4]/div[1]/ul/li[6]/a")
                driver.execute_script("arguments[0].click();", button)
                time.sleep(10)
            except NoSuchElementException:
                pass
        elif (i == 2 or i == 75):
            try:
                button = driver.find_element(By.XPATH, "/html/body/div[3]/div[1]/div[2]/div[2]/div[2]/div/div/div/div/div[2]/div/div[4]/div[1]/ul/li[8]/a")
                driver.execute_script("arguments[0].click();", button)
                time.sleep(10)
            except NoSuchElementException:
                pass
        elif (i == 3 or i == 74):
            try:
                button = driver.find_element(By.XPATH, "/html/body/div[3]/div[1]/div[2]/div[2]/div[2]/div/div/div/div/div[2]/div/div[4]/div[1]/ul/li[9]/a")
                driver.execute_script("arguments[0].click();", button)
                time.sleep(10)
            except NoSuchElementException:
                pass
        elif (i == 4 or i == 73):
            try:
                button = driver.find_element(By.XPATH, "/html/body/div[3]/div[1]/div[2]/div[2]/div[2]/div/div/div/div/div[2]/div/div[4]/div[1]/ul/li[10]/a")
                driver.execute_script("arguments[0].click();", button)
                time.sleep(10)
            except NoSuchElementException:
                pass
        elif (i >= 5 and i < 73):
            try:
                button = driver.find_element(By.XPATH, "/html/body/div[3]/div[1]/div[2]/div[2]/div[2]/div/div/div/div/div[2]/div/div[4]/div[1]/ul/li[11]/a")
                driver.execute_script("arguments[0].click();", button)
                time.sleep(10)
            except NoSuchElementException:
                pass
        i += 1

    df.drop_duplicates(subset="Product_Name", keep='first', inplace=True)
    df['Supplier_Name'] = 'wineswholesale'
    df = df[['Product_Name', 'Supplier_Name', 'Product_In_Stock', 'Scraped_Data_Old_Price', 'Scraped_Data_New_Price']]
    return df
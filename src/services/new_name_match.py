# function to match_name with fuzzy wuzzy and return the top matched bbw product name when above certain threshold 

import re
from fuzzywuzzy import fuzz

def fuzzy_wuzzy_name_matcher(supplier_product_name, bbw_products_dict):

    edited_name = regex_remove_patterns(supplier_product_name)
    substrings = edited_name.split(' ')

    possible_matches = []
    for substring in substrings:
        if substring != '':
            possible_matches += [value for value in bbw_products_dict.values() if substring in value]
    unique_possible_matches = set(possible_matches)

    matched_bbw_name = ''
    matched_name_similarity_score = 0
    threshold = 75

    for wine in list(unique_possible_matches):
        score = fuzz.ratio(supplier_product_name.lower(), wine.lower())
        # print(wine, score, matched_name_similarity_score)
        if score >= matched_name_similarity_score and score >= threshold and check_vintage(supplier_product_name, wine) == True:
            matched_bbw_name = wine
            matched_name_similarity_score = score
            
    return matched_bbw_name

def regex_remove_patterns(string):
    volume_pattern = r'(- \d+\s*(ml|ML|l|L))'  # Match digits followed by "ml,", "ML", "L," or "l"
    year_pattern = r'( \b\d{4}\b)'  # Match year/vintage
    new_string = re.sub(volume_pattern, '', string, flags=re.IGNORECASE) # case-insensitive
    new_string = re.sub(year_pattern, '', string)
    new_string = re.sub('[^a-zA-Z0-9 \n\.]', '', new_string)
    return new_string


def check_vintage(supplier_product_name, bbw_product_name):
    year_pattern = r'(\b\d{4}\b)'
    supplier_vintage = re.search(year_pattern, supplier_product_name)
    bbw_vintage = re.search(year_pattern, bbw_product_name)

    if supplier_vintage == None and bbw_vintage == None:
        return True
    if supplier_vintage == None or bbw_vintage == None:
        return False
    if supplier_vintage.group(0) == bbw_vintage.group(0):
        return True
    return False
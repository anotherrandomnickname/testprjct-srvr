import json as encoder
from difflib import get_close_matches
import math

from sanic import Sanic
from sanic.response import json
from sanic_cors import CORS, cross_origin
from sanic import response

import os


MAX_RATING = 100
MAX_PRICE = 1000
PRODUCTS_PER_PAGE = 5

app = Sanic()
@app.route('/product/get?<page>?<price_lowest>?<price_highest>?<rating_lowest>?<rating_highest>?<brands>?<text>', methods=['GET', 'OPTIONS'])
@cross_origin(app, automatic_options=True, origins='http://localhost:3000')
async def get_products(request, page, price_lowest, price_highest, rating_lowest, rating_highest, brands, text):
    query_string = request.query_string.split('&')
    page = int(query_string[0].split('=', 1)[-1])
    price_lowest = int(query_string[1].split('=', 1)[-1])
    price_highest = int(query_string[2].split('=', 1)[-1])
    rating_lowest = int(query_string[3].split('=', 1)[-1])
    rating_highest = int(query_string[4].split('=', 1)[-1])
    brands = query_string[5].split('=', 1)[-1]
    text = query_string[6].split('=', 1)[-1]

    print(request.query_string)
    with open('db.json') as json_file:
        data = encoder.load(json_file)
        result = await filter_word(data['products'], text)
        result = await filter_rating(result, rating_lowest, rating_highest)
        result = await filter_price(result, price_lowest, price_highest)
        result = await filter_brands(result, brands)
        result = await filter_word(result, text)
        total_pages = await count_total_pages(result)
        result = await filter_page(result, page, total_pages)
    if len(result) != 0:
        return json({
            "data": result,
            "total_data_pages": total_pages
        })
    else:
        return json({
            "message": "no data found"
        }, status=404)

async def filter_price(data, price_lowest, price_hightest):
    if price_hightest == 0:
        price_hightest = MAX_PRICE
    result = list(filter(lambda p: p['price'] <= price_hightest and p['price'] >= price_lowest, data))
    return result

async def filter_rating(data, rating_lowest, rating_hightest):
    if rating_hightest == 0:
        rating_hightest = MAX_RATING
    result = list(filter(lambda p: p['rating'] <= rating_hightest and p['rating'] >= rating_lowest, data))
    return result

async def filter_brands(data, brands):
    print('BRANDS', brands)
    if brands != '':
        print('NOT EMPTY')
        brand_list = brands.split('-')
        result = []
        for brand in brand_list:
            print("brand is", brand)
            result = result + list(filter(lambda p: p['brandName'] == brand, data))
            print("result is", result)
        return result
    else:
        return data

async def filter_page(data, page, total_pages):
    if len(data) != 0:
        result = []
        max_range = PRODUCTS_PER_PAGE
        if page == total_pages:
            data_length = len(data) / PRODUCTS_PER_PAGE
            i = 0
            while not data_length.is_integer():
                i = i + 1
                data_length = (len(data) - i) / PRODUCTS_PER_PAGE
                max_range = i
            max_range_float = str(data_length-int(data_length))[1:]
        for i in range(0, max_range):
            result.append(data[((page * PRODUCTS_PER_PAGE) - PRODUCTS_PER_PAGE) + i])
        return result
    else:
        return data

async def filter_word(data, word):
    if word != '':
        patterns = []
        result = []
        close_matches = []
        for p in data:
            patterns.append(p['name'].lower())
            close_matches = get_close_matches(word.lower(), patterns)
        if len(close_matches) == 0:
            close_matches = [s for s in patterns if word.lower() in s]
        for match in close_matches:
            for product in data:
                if match == product['name'].lower():
                    result.append(product)
        return [i for n, i in enumerate(result) if i not in result[n + 1:]]
    else:
        return data

async def count_total_pages(data):
    total_products = len(data)
    total_pages = math.ceil(total_products / PRODUCTS_PER_PAGE)
    return total_pages
        

async def get_specific_product(id):
    with open('db.json') as json_file:
        data = encoder.load(json_file)
        data = data['products']
        result = list(filter(lambda p: p['id'] == id, data))
    

@app.route('/getbrands/', methods=['GET', 'OPTIONS'])
@cross_origin(app, automatic_options=True, origins='http://localhost:3000')
async def get_brandlist(request):
    with open('db.json') as json_file:
        data = encoder.load(json_file)
        result = []
        for p in data['products']:
            result.append(p['brandName'])
        result = [i for n, i in enumerate(result) if i not in result[n + 1:]]
        return json({
            "data": result
        })


if __name__ == "__main__":
    app.run(
    host='0.0.0.0',
    port=os.environ.get('PORT') or 3110,
    debug=True
)
import functools
import json
import requests

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from juicy.db import get_db
from juicy.secrets import app_id, app_key

bp = Blueprint('products', __name__, url_prefix='/products')


@bp.route('/count')
def product_count():
    response = requests.get(
        'https://api.nutritionix.com/v1_1/search/'
        '?brand_id=51db37d0176fe9790a899db2&fields=*'
        '&appId={0}&appKey={1}'.format(app_id, app_key)
    ).json()
    print (response)
    product_count = {
        'total products': response['total_hits']
    }

    return json.dumps(product_count)


@bp.route('/calories')
def calories():
    keep_reading = True
    entries = []
    offset = 0

    headers = {
        'Content-Type': 'application/json',
    }

    data = {
        'appId': app_id,
        'appKey': app_key,
        'fields': [
            'item_id',
            'item_name',
            'brand_name',
            'nf_calories',
            'nf_serving_size_qty',
            'nf_serving_size_unit'
        ],
        'offset': 0,
        'limit': 50,
        'sort': {
            'field': 'item_name.sortable_na',
            'order': 'asc'
        },
        'filters': {
            'brand_id': '51db37d0176fe9790a899db2'
        }
    }

    while keep_reading:
        response = requests.post(
            'https://api.nutritionix.com/v1_1/search',
            headers=headers,
            data=json.dumps(data)
        ).json()
        print (response)
        entries.extend(response['hits'][0:])

        data['offset'] += data['limit']

        if data['offset'] >= int(response['total']):
            keep_reading = False

    calories = []
    for entry in entries:
        fields = entry['fields']
        average_calories_per_fl_oz = None
        if fields['nf_serving_size_unit'] == 'fl oz':
            average_calories_per_fl_oz = fields['nf_calories']/fields['nf_serving_size_qty']
        calories.append(
            {
                'item_id': entry['_id'],
                'item_name': fields['item_name'],
                'calories_per_serving': fields['nf_calories'],
                'serving_size': fields['nf_serving_size_unit'],
                'number of servings': fields['nf_serving_size_qty'],
                'average_calories_per_fl_oz': average_calories_per_fl_oz
            }
        )


    return json.dumps(calories)


@bp.route('/ingredients')
def ingredients():
    db = get_db()
    ingredients = db.execute(
        "SELECT ingredient, GROUP_CONCAT(product, ' | ') as products, "
        "COUNT(DISTINCT product) as product_count "
        "FROM ingredient_index "
        "GROUP BY ingredient;"
    ).fetchall()

    data = []
    for ingredient in ingredients:
        data.append(
            {
                'ingredient': ingredient['ingredient'],
                'products': ingredient['products'],
                'product_count': ingredient['product_count']
            }
        )

    return render_template('products/ingredients.html', ingredients=data)

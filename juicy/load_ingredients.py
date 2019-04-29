import click
import json
import requests

from flask import current_app, g
from flask.cli import with_appcontext

from juicy.db import get_db
from juicy.secrets import app_id, app_key


@click.command('load-ingredients')
@with_appcontext
def load_ingredients_command():
    click.echo('Ingredients Load Starting')
    db = get_db()
    #TODO remove this
    db.execute('DELETE FROM ingredient_index')
    # end of TODO
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
            'item_name',
            'nf_ingredient_statement',
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
        entries.extend(response['hits'][0:])

        data['offset'] += data['limit']

        if data['offset'] >= int(response['total']):
            keep_reading = False

    for entry in entries:
        fields = entry['fields']
        ingredients = None
        if fields['nf_ingredient_statement']:
            ingredients = fields['nf_ingredient_statement'].split(',')
            for ingredient in ingredients:
                if '(' in ingredient:
                    ingredient = ingredient.split('(')[0]
                if ingredient.endswith(')'):
                    continue
                ingredient = ingredient.replace('and', '').strip('.').strip()
                if 'Natural Flavors' in ingredient:
                    ingredient = 'Natural Flavors'
                db.execute(
                    'INSERT INTO ingredient_index (ingredient, product)'
                    ' VALUES (?, ?)',
                    (ingredient.title(), fields['item_name'])
                )

    db.commit()

    click.echo('Ingredients Load Finished')


def init_app(app):
    app.cli.add_command(load_ingredients_command)

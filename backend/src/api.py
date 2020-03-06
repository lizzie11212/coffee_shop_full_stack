import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

## ROUTES
'''
Endpoint: /drinks
Returns: List of drinks in short format
'''

@app.route('/drinks')
def get_drinks():
    try:
        drinks = [drink.short() for drink in Drink.query.all()]
        return jsonify({
            'success': True,
            'drinks': drinks
        }), 200
    except Exception:
        abort(404)

'''
Endpoint: /drinks-details
Auth: get:drinks-detail
Returns: List of drinks in long format
'''

@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    try:
        all_drinks = Drink.query.all()
        drinks = [drink.long() for drink in all_drinks]

        if all_drinks is None:
            abort(400)

        return jsonify({
            'success': True,
            'drinks': drinks
        }), 200
    except Exception:
        abort(404)

'''
Endpoint: /drinks
Auth: post:drinks
Returns: Array with newly created drink
'''

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_new_drink(payload):
    data = request.get_json()
    try:
        title = data.get('title', None)
        recipe= data.get('recipe', None)
        drink = Drink(
            title=title,
            recipe=recipe
        )
        drink.insert()

        return jsonify({
        'success': True,
        'drinks': [drink.long()]
        }), 200
    except Exception:
        abort(422)

'''
Endpoint: /drinks/<drink id>
Auth: patch:drinks
Arguments: Integer of drink ID
Returns: Array with updated drink information
'''

@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    # Get the drink record
    drink = Drink.query.filter(Drink.id ==drink_id).one_or_none()

    # abort if no drink Found
    if drink is None:
        return jsonify({
            "success": False,
            "error": 404,
            "message": "No drink was found."
        }), 404

    data = request.get_json()
    title = data.get('title', None)
    recipe = data.get('recipe', None)

     # Set the values

    if title is not None:
        drink.title = title
    if recipe is not None:
        drink.recipe = recipe

    # do the update

    try:
        drink.update()

    except Exception as e:
        abort(422)

    return jsonify({'success': True, 'drinks': [drink.long()]})

'''
Endpoint: /drinks/<drink id>
Auth: delete:drinks
Arguments: Integer of drink ID
Returns: ID of deleted drink
'''

@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    drink = Drink.query.get(drink_id)

    if drink is None:
        return jsonify({
            "success": False,
            "error": 404,
            "message": "No drink was found."
        }), 404
    try:
        drink.delete()

        return jsonify({
            'success': True,
            'delete': drink.id
        }), 200
    except Exception:
        abort(422)


## Error Handling
'''
Error handler for 422 (unprocessable entity)
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False,
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

'''
Error handler for 404
'''

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


'''
Error handler for 400
'''


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400

'''
Error handler for 401
'''


@app.errorhandler(401)
def not_authorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Not authorized"
    }), 401


'''
AuthError handler
'''


@app.errorhandler(AuthError)
def process_AuthError(error):
    response = jsonify(error.error)
    response.status_code = error.status_code

    return response

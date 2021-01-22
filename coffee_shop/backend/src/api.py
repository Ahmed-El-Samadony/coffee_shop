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


db_drop_and_create_all()

## ROUTES

#get drink
@app.route('/drinks', methods= ['GET'])
def get_drinks():
    selection = Drink.query.all()
    drinks = [drink.short() for drink in selection]

    if (drinks):
        return jsonify({
            'success': True,
            'drinks': drinks,
        })
    else:
        abort(404)


#get drink detail
@app.route('/drinks-detail', methods= ['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    selection = Drink.query.all()
    drinks = [drink.long() for drink in selection]

    if (drinks):
        return jsonify({
            'success': True,
            'drinks': drinks,
        })
    else:
        abort(404)

#create drink
@app.route('/drinks', methods = ['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    body = request.get_json()

    try:
        new_title = body.get('title', None)
        new_recipe = body.get('recipe')
        # Adjust the input form of the recipe to match the form stored in the database
        # The postman form is a dictionary and needs to be put in a list first
        # Whereas, the browser form is in a list already and doens't need that
        if isinstance(new_recipe, dict): 
            new_recipe = [new_recipe]
        new_recipe = json.dumps(new_recipe) #Convert to string to be stored in the database

        new_drink = Drink(title=new_title, recipe=new_recipe)
        new_drink.insert()

        drink = [new_drink.long()]

        return jsonify({
            'success': True,
            'drinks': drink,
            })
    except:
        abort(422)

#update drink
@app.route('/drinks/<id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, id):
    body = request.get_json()

    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None:
            abort(404)
        
        updated_title = body.get('title')
        if updated_title:
            drink.title = updated_title

        updated_recipe = body.get('recipe')
        if updated_recipe:
            if isinstance(updated_recipe, dict): 
                updated_recipe = [updated_recipe]
            drink.recipe = json.dumps(updated_recipe)   #Convert to string to be stored in the database

        drink.update()
        
        drink = [drink.long()]
        
        return jsonify({
            'success': True,
            'drinks': drink,
            })
    except:
      abort(400)

#delete drink
@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()

        if drink is None:
            abort(404)
        
        drink.delete()

        return jsonify({
            'success': True,
            'delete': id,
        })
    except:
        abort(422)

## Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

@app.errorhandler(404)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 404,
                    "message": "resource not found"
                    }), 404


@app.errorhandler(AuthError) #Whenever raised in auth.py
def unauthorized(error):
    return jsonify({
                    "success": False, 
                    "error": error.status_code,
                    "message": error.error['description']
                    }), error.status_code


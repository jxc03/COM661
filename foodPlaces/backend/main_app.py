from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from pymongo import ASCENDING, DESCENDING
import jwt
import datetime
from functools import wraps
import bcrypt

from blueprints.auth.auth import auth_bp
from blueprints.cities.cities import cities_bp
from blueprints.places.places import places_bp
from blueprints.reviews.reviews import reviews_bp

app = Flask(__name__)

app.register_blueprint(auth_bp)
app.register_blueprint(cities_bp)
app.register_blueprint(places_bp)
app.register_blueprint(reviews_bp)

if __name__ == "__main__":
    app.run(debug = True, port = 2000)
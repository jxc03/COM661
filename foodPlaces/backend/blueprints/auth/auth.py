# File for all authentication routes

# Modules
from flask import Blueprint, request, make_response, jsonify 
import globals # Import globals.py
from decorators import jwt_required, admin_required

from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from pymongo import ASCENDING, DESCENDING
import jwt
import datetime
from functools import wraps
import bcrypt
from email_validator import validate_email, EmailNotValidError
 
# Create blueprint
auth_bp = Blueprint("auth_bp", __name__)

# MongoDB connection
places = globals.db.foodPlacesDB
blacklist = globals.db.blacklist
users = globals.db.users


# Function for validation of password
def validate_password(password): # Function, takes password as its parameter
    if len(password) < 8: # If the lengeth of the password is less than 8
        return {'is_valid': False, # Returns False
                'message': 'Password must be at least 8 characters long'} # Error message
    if not any(char.isupper() for char in password): # Checks if there is no uppercase letter in the password
        return {'is_valid': False,
                'message': 'Password must contain at least one uppercase letter'}
    if not any(char.islower() for char in password): # Checks if there no lowercase letter in the password
        return {'is_valid': False, 
                'message': 'Password must contain at least one lowercase letter'}
    if not any(char.isdigit() for char in password): # Checks if there is no number in the password
        return {'is_valid': False, 
                'message': 'Password must contain at least on number'}
    special_characters = '!@#$%^&*()_+={[]}:;<>,.?~' # Defining special characters to check for in the password
    if not any(char in special_characters for char in password): # Checks if there is no special character in the password
        return {'is_valid': False, 
                'message':f'Password must contain at least on special character: {special_characters}'}
    return {'is_valid': True, 'message': ''} # Proceeds if all the checks passes

# Function to generate authentication token
def generate_auth_token(username, is_admin):
    try:
        return jwt.encode(
            {
                'user': username,
                'admin': is_admin,
                'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=30)
            },
            globals.secret_key, 
            algorithm="HS256"
        )
    except Exception as err:
       return make_response(jsonify({'message': 'Error returning authentication token', 'error': str(err)}), 400)

# Register user 
@auth_bp.route("/api/register", methods=['POST']) # Root route
def register():
    # Test code for errors
    try:
        # Get the JSON data
        data = request.get_json()
        if not data: 
            return make_response(jsonify({'message': 'No data has been provided'}), 400)

        # Check if all required fields are present
        required_fields = ['username', 'password', 'email', 'name'] # List of required fields
        if not all(field in data for field in required_fields): # Validates that required fields are provided
            return make_response(jsonify({'message': 'Missing required fields. Required fields are: username, password, email, and name'}), 400)
        # Check if username already exists
        if users.find_one({'username': data['username']}): 
            return make_response(jsonify({'message': 'Username already exists'}), 409)
        # Check if email already exists
        if users.find_one({'email': data['email']}):
            return make_response(jsonify({'message': 'Email already registered'}), 409)
        # Validate username length
        if len(data['username']) < 3: 
            return make_response(jsonify({'message': 'Username must be at least 3 characters long'}), 400)
        # Validate password, call the validation function
        password = validate_password(data['password'])
        if not password['is_valid']: # If password is not valid
            return make_response(jsonify({'message': password['message']}), 400)
        # Validate email
        try: 
            valid = validate_email(data('email')) # Gets the email and validates it using the 'email_validator' module
            data['email'] = valid.email # Updates the data with the validated email address
        except EmailNotValidError as err: # Handles the error if email is not valid
            return make_response(jsonify({'message': str(err)}, 400))

        # Create new user
        new_user = {
            'name': data['name'], # Assigns the name from the input data
            'username': data['username'],
            'email': data['email'],
            'password': bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()), # Hashs the password for security
            'admin': data.get('admin', False),  # Assigns admin status, defaulted to False if it's not specified
            'created_at': datetime.datetime.now(datetime.UTC)
        } 
        # Insert the new user into the database
        users.insert_one(new_user) # Adds the user to the 'users' collection
        # Generate token for the new user
        token = generate_auth_token(
            new_user['username'],
            new_user['admin']
        )
        return make_response(jsonify({
            'message': 'Registration successful',
            'token': token,
            'username': new_user['username'],
            'email': new_user['email'],
            'name': new_user['name']
        }), 201)

    # Handles any errors that occurs during registration
    except Exception as err: 
        return make_response(jsonify({
            'message': 'Error occurred while registering user',
            'error': str(err)
        }), 500)

# Login route
@auth_bp.route("/api/login", methods=['POST']) 
def login():
    try:
        # Get and validate auth headers
        auth = request.authorization # Gets the auth info
        if not auth or not auth.username or not auth.password:
            return make_response(jsonify({'error': 'Username and password are required'}), 401)

        # Find user and validate credentials
        user = users.find_one({'username': auth.username})
        if not user:
            return make_response(jsonify({'error': 'Invalid username or password'}), 401)
         
        # Validate password
        try:
            password_is_valid = bcrypt.checkpw(
                auth.password.encode('utf-8'),
                user['password']
            )
            if not password_is_valid:
                return make_response(jsonify({'error': 'Invalid username or password'}), 401)
        except Exception:
            return make_response(jsonify({'error': 'Error verifying password'}), 500)


        # Generate token 
        token = generate_auth_token(user['username'], user['admin'])

        return make_response(jsonify({
            'message': 'Login successful',
            'token': token,
            'username': user['username']
        }), 200)
        
    except Exception as err:
        return make_response(jsonify({
            'error': 'An error occurred during login',
            'message': str(err)
        }), 500)
        

# Logout route
@auth_bp.route("/api/logout", methods=["POST"])
@jwt_required # Requires valid token
def logout(): 
    try:
        # Get and validate the token
        token = request.headers['x-access-token'] # Gets the token
        if not token:
            return make_response(jsonify({'error': 'No token was provided'}), 401)

        # Add token to blacklist and check if it's not already blacklisted
        if not blacklist.find_one({'token': token}): # Checks if token is not already blacklisted
            blacklist.insert_one({"token": token}) # If it's not then adds it to the blacklist
        return make_response(jsonify({'message': 'Logout successful'}), 200)
    except Exception as err:
        return make_response(jsonify({
            'error': 'An error occured during logout',
            'message': str(err)
            }), 500)
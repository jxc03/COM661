from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'

@app.route('/api/v1.0/login', methods=['GET'])
def login():
    auth = request.authorization
    
    if auth and auth.password == 'password':
        token = jwt.encode(
            {
            'user' : auth.username,
            'exp' : datetime.datetime.now(datetime.UTC) +
                    datetime.timedelta(minutes=30) 
            },
            app.config['SECRET_KEY'],
            algorithm="HS256"
        )
        return make_response(jsonify({'token' : token}), 200)
    return make_response('Could not verify', 401, \
                        {
                            'WWW-Authenticate' : \
                            'Basic realm = "Login required"'
                        })

if __name__ == "__main__":
    app.run(debug=True)
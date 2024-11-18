# Register a user

Data retrievel:
``` Python
data = request.get_json()
```
- Purpose: Parses incoming JSON data from the request
- Link: https://flask.palletsprojects.com/en/stable/quickstart/#json-and-apis

Field validation:
``` Python
required_fields = ['username', 'password', 'email', 'name'] 
if not all(field in data for field in required_fields): 
    return make_response(jsonify({'message': 'Missing required fields. Required fields are: username, password, email, and name'}), 400)
```
- Purpose: Checks if the fields in required_fields are present
- Link: https://docs.python.org/3/library/functions.html#all

Username and email validaiton:
``` Python
if users.find_one({'username': data['username']}): 
    return make_response(jsonify({'message': 'Username already exists'}), 409)
if users.find_one({'email': data['email']}):
    return make_response(jsonify({'message': 'Email already registered'}), 409)
```
- Purpose:
- Links:


    # Validate password length
    if len(data['password']) < 6: # Chekcs if the password is at least 6 characters long
        return make_response(jsonify({'message': 'Password must be at least 6 characters long'}), 400)

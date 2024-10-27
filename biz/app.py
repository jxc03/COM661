from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.bizDB # Selects the database
businesses = db.biz # Selects the collection

'''
This function handles GET requests to fetch all business with pagination. It sets values for
page number and size then checks for these parameters in the query then calculates the 
starting index for the query and retreives the businesses from the database. The results
are returned as a  JSON response
'''
# Gets all businesses with pagination
@app.route("/api/v1.0/businesses", methods = ["GET"]) # Route to businesses, uses GET method get all businesses
def show_all_businesses(): # Defines function to show all businesses
    # Values for pagination
    page_num, page_size = 1, 10 # Sets the page numbber to 1 and page size to 10
    
    # Checks if 'pn' (page number) is provided in the query paramenters
    if request.args.get('pn'): # Retreives the 'pn' paramter if it exists
        page_num = int(request.args.get('pn')) # Converts page number to an integer
    
    # Checks if 'ps' (page size) is provided in the query paramenters   
    if request.args.get('ps'): # Retreives the 'ps' paramter if it exists
        page_num = int(request.args.get('ps')) # Converts the page number to an integer

    # Calculates the start index of the page    
    page_start = (page_size * (page_num - 1)) #Calculates based on current page number and size

    # Empty list to store the results
    data_to_return = [] # Assigs an empty list to 'data_to_return'

    # Queries the databse to get the businesses with pagination
    for business in businesses.find() \
                    .skip(page_start) \
                    .limit(page_size): # Skips to the start of the current page / Limits the results to the page size
        business['_id'] = str(business['_id']) # Converts business ID to string

        for review in business['reviews']: # Iterates over each review in the business
            review['_id'] = str(review['_id']) # Converts review ID to string        
        data_to_return.append(business) # Adds the business to the results list 'data_to_return'
    
    # Returns the results as a JSON response with a 200 status code
    return make_response( jsonify(data_to_return), 200) # Converts the results list to JSON

'''
This function validates the ID by ensuring it's a 24 character hexadecimal string. It checks
if the length of the ID is exactly 24. If not, it returns Flase. Then, it iterates through
each character in the ID to check if it's a valid hexadecimal character. If any character 
isn't a valid hexadecimal digit, it returns False. If all checks pass, it returns True which
indicates that the ID is valid
'''
#Validation for ObjectID    
def is_valid_objectid(id):
    #Checks if the ID length is 24
    if len(id) != 24: #If ID length is equal to 24
        return False #Returns False if the length is not 24

    #Checks if all characters are hexadecimal
    hex_digits =  "0123456789abcdefABCDEF" #String of hexadecimal characters
    
    for char in id: #Iterates over each character in the ID
        if char not in hex_digits: #Checks if the character is not in the 'hex_digits' list
            return False #Returns False if any character is not a hexadecimal
    return True #Returns True if the ID is valid

'''
This function handles GET requests to retrieve a specific business by its ID. It will 
validate the provided business ID ensure it's a valid 24 character hexadecimal string. If the
ID is valid, it queries the 'businesses' collection in the database to find the business 
with the given ID. If the business is not found or the ID is invalid, it returns an error message
'''
#Gets one business
@app.route("/api/v1.0/businesses/<string:id>", methods = ["GET"]) #Route for getting a specific business by its ID using the GET method 
def show_one_businesses(id): #Defines function to show one business which takes 'id' as its parameter
    #Checks if the provided business ID is valid
    if not is_valid_objectid(id): #Validates the business ID
        return make_response(jsonify ({"error": "Invalid business ID"}), 400 ) #Returns error message if ID is invalid with 404 status code

    #Queries the database to find the business with the given ID
    business = businesses.find_one( {'_id' : ObjectId(id)} ) #Retrieves the business from the database
    
    if business is not None: #Checks if the business exists
        business['_id'] = str(business['_id']) #Converts business ObjectId to string
        for review in business['reviews']: #Goes over each review in the business
            review['_id'] = str(review['_id']) #Converts review ObjectId to string
        return make_response( jsonify (business), 200) #Returns the business data as JSON with a 200 status code
    else: #If business doesn't exists
        return make_response( jsonify ({"error" : "Invalid business ID"}), 404) #Returns an error message with a 404 status code 


#Adds a new business
@app.route("/api/v1.0/businesses", methods = ["POST"]) #Route to businesses, uses POST method to add new business
def add_businesses(): #Defines function to add business
    #Checks if 'name', 'town', and 'rating' are provided in the form
    if  "name" in request.form and \
        "town" in request.form and \
        "rating" in request.form:
        
        #Creates a new business with the form data provided
        new_business = {
            "name" : request.form["name"], #Assigns 'name' from form data
            "town" : request.form["town"], #Assigns 'town' from form data
            "rating" : request.form["rating"], #Assigns 'rating' from form data
            "reviews" : {} #Initializes 'reviews' as an empty dictionary
        }
        
        #Inserts the new business into the 'businesses' collection
        new_business_id = businesses.insert_one(new_business) #Adds thew new business and assigns it to 'new_business_id'
        #Creates a link to the newly added business
        new_business_link = "http://127.0.0.1:2000/api/v1.0/businesses/" \
                            + str(new_business_id.inserted_id) #Adds the URL with the new business ID

        return make_response( jsonify ({"url" : new_business_link}), 201 ) #Returns the new business URL with a 201 status
    else:
        return make_response( jsonify ({"error" : "Missing form data"}), 404) #Returns an error message if a form data is missing with a 404 status

#Edits a business
@app.route("/api/v1.0/businesses/<string:id>", methods = ["PUT"]) #Root route, for PUT method
def edit_businesses(id): #Defines function, takes id as input
    if  "name" in request.form and \
        "town" in request.form and \
        "rating" in request.form:
        result = businesses.update_one(
            {"_id" : ObjectId(id)},
            {"$set" : {
                "name" : request.form["name"],
                "town" : request.form["town"],
                "rating" : request.form["rating"]
            }}
        )
        if  result.matched_count == 1:
            edited_business_link = "http://127.0.0.1:2000/api/v1.0/businesses/" + id
            return make_response( jsonify ({"url" : edited_business_link}), 200) #Output,      
        else:
            return make_response( jsonify ({"error" : "Invalid business ID"}), 404) #Output, returns error message with 404 status
    else: 
        return make_response( jsonify ({"error" : "Missing form data"}), 404) #Output, returns error message with 404 status

#Deletes a business
@app.route("/api/v1.0/businesses/<string:id>", methods = ["DELETE"]) #Root route, for DELETE method
def delete_businesses(id): #Defines function, takes id as input
    result = businesses.delete_one( {"_id" : ObjectId(id)} )
    if result.deleted_count == 1:
        return make_response( jsonify ({}), 204)
    else:
        return make_response( jsonify ({"error" : "Invalid business ID"}), 404) #Output, returns error message with 404 status

#Adds a review
@app.route("/api/v1.0/businesses/<string:id>/reviews", methods=["POST"]) #Route for adding a review to a business using POST method
def add_new_review(id): #Defines function to add a new review, takes id as its parameter
    #Validates the business ID
    if not is_valid_objectid(id): #Checks if business ID is valid
        return make_response(jsonify ({"error": "Invalid business ID"}), 400) #Returns a error message if ID is invalid with 400 status code
    
    #Checks if the business exists
    business = businesses.find_one({'_id' : ObjectId(id)}) #Queries the databse to find the business by ID
    if not business: #If the business does not exist
        return make_response(jsonify ({"error" : "Business not found"}), 400) #Returns a error message if ID is invalid with 400 status code

    #Validates if there are form data to update
    if not ("username" in request.form and \
           "comment" in request.form and \
           "stars" in request.form): 
        return make_response(jsonify ({"error": "Missing form data"}), 400) #Returns a error message if any form data is missing with 400 status code

    #Creates a new review dictionary with the provided form data
    new_review = {
        "_id" : ObjectId(), #Generates a new ObjectId for the review
        "username" : request.form["username"], #Assigns the 'username' from the form data
        "comment" : request.form["comment"], #Assigns the 'comment' from the form data
        "stars" : request.form["stars"] #Assigns the 'stars' from the form data
    }

    #Updates the business document by pushing the new review into the 'reviews' array
    businesses.update_one( {"_id" : ObjectId(id)}, {"$push": {"reviews" : new_review}} ) #Adds the 

    #Creates a link to the newly added review
    new_review_link =  "http://127.0.0.1:2000/api/v1.0/businesses/" \
                        + id +"/reviews/" + str(new_review['_id']) #Constructs the URL for the new review by combining the base URL, business ID, and review ID
    
    #Returns the URL of the new review with a 201 status code
    return make_response(jsonify ({ "url" : new_review_link }), 201) #Sends a response with the new review URL and a status code of 201


#Gets all reviews for a specific business
@app.route("/api/v1.0/businesses/<string:id>/reviews", methods=["GET"]) #Route for fetching all reviews for a specific business using GET method
def fetch_all_reviews(id): #Defines function to fetch all review of a specified business, takes id as its parameter
    #Validates the business ID
    if not is_valid_objectid(id): #Checks if business ID is valid
        return make_response(jsonify ({"error": "Invalid business ID"}), 400) #Returns a error message if ID is invalid with 400 status code
    
    #Checks if the business exists
    business = businesses.find_one({'_id' : ObjectId(id)}) #Queries the databse to find the business by ID
    if not business: #If the business does not exist
        return make_response(jsonify ({"error" : "Business not found"}), 400) #Returns a error message if ID is invalid with 400 status code

    #Initialise a list    
    data_to_return = [] #Empty list assigned to 'data_to_return'
    
    #Retrieves the reviews of a specific business by its ObjectId
    business = businesses.find_one(
        {"_id" : ObjectId(id)}, \
        {"reviews" : 1, "_id" : 0 }) #Finds the business by its ObjectId and only retrieve its reviews

    #For loop, loops through and proccesses each review    
    for review in business["reviews"]: #Goes through each review in the business reviews
        review["_id"] = str(review["_id"]) #Coverts the ID of each review into a string
        data_to_return.append(review) #Adds the review to the list of data to return
    return make_response(jsonify (data_to_return), 200 ) #Returns the list of reviews as a JSON response with a 200 status code 

#Gets one review
@app.route("/api/v1.0/businesses/<bid>/reviews/<rid>", methods=["GET"])
def fetch_one_review(bid, rid): #Defines function to fetch one review, takes bid (business ID) and rid (review ID) as parameters

    #Validates both business ID and review ID
    if not is_valid_objectid(bid) or not is_valid_objectid(rid): #Checks if either ID is invalid
        error_message = "Bad business ID" if not is_valid_objectid(bid) else "Bad review ID" # Sets a error message based on which ID is invalid
        return make_response(jsonify ({"error" : error_message}), 400) #Returns the error message if either ID is invalid with 400 status code
    
    # Queries the database to find the business by ID and its review by review ID
    business = businesses.find_one(  #Queries the database to find the business with the given ID and the review with the given ID
    {"_id": ObjectId(id), "reviews._id": ObjectId(rid)},  #Matches both the business ID and the review ID
    {"_id": 0, "reviews.$": 1}  #Shows only the matched review
    ) 

    #Checks if the business and review exists
    if not business: #If the review doesn't exist within the business
        return make_response(jsonify ({"error" : "Review not found"}), 404) #Returns an error message with 404 status code
    
    #Converts the review ObjectId to a string
    business['reviews'][0]['_id'] = str(business['reviews'][0]['_id'])
    
    #Returns the review datya as JSON and with a 200 status code
    return make_response(jsonify (business['reviews'][0]), 200) #Sends the review data 

#Edits a review
@app.route("/api/v1.0/businesses/<bid>/reviews/<rid>", methods=["PUT"])
def edit_review(bid, rid):
    edited_review = {
        "reviews.$.username" : request.form["username"],
        "reviews.$.comment" : request.form["comment"],
        "reviews.$.stars" : request.form['stars']
        }

    businesses.update_one(
        { "reviews._id" : ObjectId(rid) },
        { "$set" : edited_review }
        )

    edit_review_url = "http://localhost:5000/api/v1.0/businesses/" + \
        bid + "/reviews/" + rid
    
    return make_response(jsonify ({"url":edit_review_url}), 200)

#Deletes a review
@app.route("/api/v1.0/businesses/<bid>/reviews/<id>", methods=["DELETE"])
def delete_review(bid, rid): 
    businesses.update_one(
        {"_id" : ObjectId(bid)},
        { "$pull" : { "reviews" : { "_id" : ObjectId(rid) } } }
        )
    
    return make_response(jsonify ({}), 204)

if __name__ == "__main__":
    app.run(debug = True, port = 2000)
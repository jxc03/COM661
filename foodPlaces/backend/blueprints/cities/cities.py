# File for all city routes

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

cities_bp = Blueprint("cities_bp", __name__)
places = globals.db.foodPlacesDB
# Gets all cities with pagination, optional filtering, and sorting
@cities_bp.route("/api/cities", methods=["GET"]) # Route to cities, uses GET method
def show_all_cities(): # Function to show all cities
    try: # Try to handle potential errors
        # Get pagination parameters from request
        page_num, page_size = validate_pagination_params(
            request.args.get('pn'),
            request.args.get('ps')
        )
        # Calculate pagination starting point
        page_start = (page_num - 1) * page_size

        # Dictionary to store query filters
        query = {}  

        # Filters the database by city name if a 'name' parameter is provided in the query
        name = request.args.get('name') 
        if name: # Checks if a name filter is provided 
            query['city_name'] = {'$regex': name, '$options': 'i'} # Case-insensitive regex for name

        # Validates the sorting options
        valid_sort_fields = ['city_name'] 
        sort_field = request.args.get('sort_by', 'city_name') # Defaults to 'city_name'
        if sort_field not in valid_sort_fields: 
            sort_field = 'city_name'  # Default to 'city_name' if invalid
        
        # Determines the sorting and order fields
        sort_order = request.args.get('sort_order', 'asc')
        sort_direction = DESCENDING if sort_order.lower() == 'desc' else ASCENDING # Set sort based on the 'sort_order'
        
        # Counts the total cities matching the query for pagination purposes
        total_cities = businesses.count_documents(query) # Gets the total count of matching cities
        if total_cities == 0:
                return make_response(jsonify({"message": "No cities were found matching the criteria."}), 404)
        
        # Retrieve matching cities from the database with pagination and sorting
        cities_taken = businesses.find(query) \
            .sort(sort_field, sort_direction) \
            .skip(page_start) \
            .limit(page_size) # Applies sorting, pagination, and filters

        # Converts to a list and ObjectId fields to strings using the helper function
        data_to_return = [convert_objectid_to_str(city) for city in cities_taken]

        # Returns a 404 status code if no cities found
        if not data_to_return: # Checks if the data list is empty
            return make_response(jsonify({"message": "No cities were found matching the criteria."}), 404)

        # Returns the paginated results with city data as JSON response
        return make_response(jsonify({
            'cities': data_to_return, # List of cities with places and related data
            'pagination': { # Pagination information
                'current_page': page_num,
                'total_pages': (total_cities + page_size - 1) // page_size, # Calculates the total pages
                'page_size': page_size,
                'total_items': total_cities 
            }}), 200)

    except ValueError as value_err: # Handles invalid parameter values
        return make_response(jsonify({"message": "Invalid parameter value", "error": str(value_err)}), 400)
    except Exception as err: # Handles any other errors that occur
        print(f"Error occurred: {err}") 
        return make_response(jsonify({"message": f"Woopsies...: {str(err)}"}), 500)

# Gets a specific city by ID with filters
@cities_bp.route("/api/cities/<city_id>", methods=["GET"])
def show_one_city(city_id): 
    try: 
        # Validates the ObjectId format
        if not is_valid_objectid(city_id): # Check if ID format is valid
            return make_response(jsonify({ # Return error if invalid
                "error": "Invalid ObjectId format"
            }), 400)

        # Gets city from database
        city = businesses.find_one({"_id": ObjectId(city_id)}) # Find city by ID
        if not city: # If city not found
            return make_response(jsonify({ # Return error response
                "error": f"City with ID {city_id} not found"
            }), 404)

        # Processes ObjectId fields
        city = convert_objectid_to_str(city) # Convert ObjectIds to strings

        # Gets filter parameters
        include_places = request.args.get('include_places', 'false').lower() == 'true' # Whether to include places
        min_rating = float(request.args.get('min_rating', 0)) # Minimum rating filter
        max_rating = float(request.args.get('max_rating', 5)) # Maximum rating filter
        place_type = request.args.get('place_type') # Type of place filter

        # Returns basic city data if places not requested
        if not include_places: # If places not needed
            return make_response(jsonify({ # Return simple response
                'data': {
                    'city_id': city.get('city_id'), # City identifier
                    'city_name': city.get('city_name') # City name
                },
                'includes': {'places': False}, # Indicates no places included
                'filters_applied': None # No filters used
            }), 200)

        # Processes and filters places
        filtered_places = [] # Initialize filtered places list
        for place in city.get('places', []): # Loop through each place
            # Checks rating criteria
            rating = place.get('ratings', {}).get('average_rating') # Get place rating
            if rating is None or not (min_rating <= rating <= max_rating): # If rating doesn't match
                continue # Skip this place

            # Checks place type criteria
            if place_type and place_type.lower() not in [t.lower() for t in place.get('info', {}).get('type', [])]:
                continue # Skip if type doesn't match

            # Creates place data object
            place_data = { # Structure place information
                'place_id': place.get('place_id'), # Place identifier
                'info': place.get('info'), # Basic information
                'location': place.get('location'), # Address and coordinates
                'business_hours': place.get('business_hours'), # Operating hours
                'service_options': place.get('service_options'), # Available services
                'menu_options': place.get('menu_options'), # Menu details
                'amenities': place.get('amenities'), # Available amenities
                'ratings': { # Rating information
                    'average_rating': rating, # Overall rating
                    'review_count': place.get('ratings', {}).get('review_count'), # Number of reviews
                    'recent_reviews': place.get('ratings', {}).get('recent_reviews', []) # Latest reviews
                },
                'media': place.get('media') # Photos and media
            }
            filtered_places.append(place_data) # Add to filtered list

        # Returns complete response
        return make_response(jsonify({ # Create JSON response
            'data': { # Main data object
                'city_id': city.get('city_id'), # City identifier
                'city_name': city.get('city_name'), # City name
                'places': filtered_places # Filtered places list
            },
            'includes': {'places': True}, # Indicates places included
            'filters_applied': { # Applied filter values
                'min_rating': min_rating if min_rating > 0 else None, # Minimum rating if set
                'max_rating': max_rating if max_rating < 5 else None, # Maximum rating if set
                'place_type': place_type # Place type if specified
            }
        }), 200)

    except ValueError as err: # Handles value errors
        return make_response(jsonify({ # Return error response
            "error": "Invalid parameter value", # Error type
            "message": str(err) # Error details
        }), 400) # Bad request error

    except Exception as err: # Handles unexpected errors
        print(f"Error occurred: {err}") # Log the error
        return make_response(jsonify({ # Return error response
            "error": "Server error", # Error type
            "message": "An unexpected error occurred", # Error message
            "details": str(err) # Error details
        }), 500) # Server error response

# Creates a new city
@cities_bp.route("/api/cities", methods=["POST"])
#@jwt_required 
def create_new_city(): 
    try: 
        # Validates JSON request
        if not request.is_json: # Checks if request contains JSON
            return make_response(jsonify({"error": "Request must be JSON"}), 400) # Returns error if not JSON
        
        city_data = request.json # Gets JSON data from request

        # Validates required city fields
        required_fields = ["city_id", "city_name"] # List of required fields
        for field in required_fields: # Check each required field
            if field not in city_data or not city_data[field]: # If field missing or empty
                return make_response(jsonify({"error": f"Missing required field: {field}"}), 400) 

        # Creates city document structure
        city_document = { # Initialize city document
            "city_id": city_data["city_id"], # Set city ID
            "city_name": city_data["city_name"], # Set city name
            "places": [] # Empty places array
        }

        # Processes places if provided
        if "places" in city_data: # If places included in request
            for place in city_data["places"]: # Process each place
                # Validates required place fields
                if not all(key in place for key in ["place_id", "info", "location"]): # Check required fields
                    return make_response(jsonify({"error": "Each place must have place_id, info, and location fields"}), 400) # Return error if missing fields

                # Validates place info
                if not all(key in place["info"] for key in ["name", "type"]): # Check info fields
                    return make_response(jsonify({"error": "Each place info must have name and type fields"}), 400) 

                # Validates coordinates
                location = place.get("location", {}) # Get location data
                coords = location.get("coordinates", {}) # Get coordinates
                try: # Try to process coordinates
                    coords["latitude"] = float(coords.get("latitude", 0)) # Convert latitude to float
                    coords["longitude"] = float(coords.get("longitude", 0)) # Convert longitude to float
                except (ValueError, TypeError): # If conversion fails
                    return make_response(jsonify({"error": "Invalid coordinates format"}), 400) 

                # Creates clean place object
                clean_place = { # Initialize clean place structure
                    "place_id": place["place_id"], # Set place ID
                    "info": { # Set place info
                        "name": place["info"]["name"], # Place name
                        "type": place["info"]["type"], # Place types
                        "status": place["info"].get("status") # Status 
                    },
                    "location": place["location"], # Location details
                    "business_hours": place.get("business_hours", {}), # Hours if provided
                    "service_options": place.get("service_options", {}), # Services if provided
                    "menu_options": place.get("menu_options", {}), # Menu details if provided
                    "amenities": place.get("amenities", {}), # Amenities if provided
                    "ratings": { 
                        "average_rating": 0, # Default rating
                        "review_count": 0, # Default review count
                        "recent_reviews": [] # Empty reviews array
                    },
                    "media": {"photos": []} # Empty media array
                }

                # Processes ratings if provided
                if "ratings" in place: # If ratings included
                    ratings = place["ratings"] # Get ratings data
                    clean_place["ratings"]["average_rating"] = float(ratings.get("average_rating", 0)) # Set rating
                    clean_place["ratings"]["review_count"] = int(ratings.get("review_count", 0)) # Set count
                    clean_place["ratings"]["recent_reviews"] = ratings.get("recent_reviews", []) # Set reviews

                # Processes media if provided
                if "media" in place and "photos" in place["media"]: # If photos included
                    clean_place["media"]["photos"] = place["media"]["photos"] # Set photos

                city_document["places"].append(clean_place) # Add clean place to city

        # Inserts city into database
        result = businesses.insert_one(city_document) # Insert new city

        # Returns success response
        return make_response(jsonify({ # Create success response
            "message": "City created successfully", # Success message
            "city_id": str(result.inserted_id) # New city ID
        }), 200) # Created status code

    except Exception as err: # Handles unexpected errors
        print(f"Error occurred: {err}") # Log the error
        return make_response(jsonify({ # Return error response
            "error": "Server error", 
            "details": str(err)
        }), 500) # Server error status  

# Updates an existing city
@cities_bp.route("/api/cities/<city_id>", methods=["PUT"]) 
#@jwt_required
def update_city(city_id): 
    try: # Try to handle potential errors
        # Validates the ObjectId format
        if not is_valid_objectid(city_id): # Check if ID format is valid
            return make_response(jsonify({"error": "Invalid ObjectId format"}), 400)

        # Gets update data from request
        if not request.is_json: # If request isn't JSON
            return make_response(jsonify({"error": "Request must be JSON"}), 400)
        
        update_data = request.json # Get JSON data from request

        # Validates update data structure
        if not update_data: # If no update data provided
            return make_response(jsonify({"error": "No update data provided"}), 400)

        # Creates update document
        update_fields = {} # Initialize update fields

        # Updates basic city information
        if "city_name" in update_data: # If name update provided
            update_fields["city_name"] = update_data["city_name"] # Add name update

        # Updates places if provided
        if "places" in update_data: # If places update provided
            for place in update_data["places"]: # Process each place
                # Validates required place fields
                if "place_id" not in place: # If place_id missing
                    return make_response(jsonify({"error": "Each place must have place_id"}), 400)

                if "info" in place: # If info update provided
                    if not all(key in place["info"] for key in ["name", "type"]): # Check required info fields
                        return make_response(jsonify({"error": "Place info must have name and type fields"}), 400)

                # Validates coordinates if provided
                if "location" in place and "coordinates" in place["location"]: # If coordinates provided
                    try: # Try to process coordinates
                        coords = place["location"]["coordinates"] # Get coordinates
                        coords["latitude"] = float(coords.get("latitude", 0)) # Convert latitude
                        coords["longitude"] = float(coords.get("longitude", 0)) # Convert longitude
                    except (ValueError, TypeError): # If conversion fails
                        return make_response(jsonify({ "error": "Invalid coordinates format"}), 400)

            update_fields["places"] = update_data["places"] # Add places update

        # Checks if any valid updates provided
        if not update_fields: # If no valid updates
            return make_response(jsonify({"error": "No valid update fields provided"}), 400)

        # Updates city in database
        result = businesses.update_one( # Perform update
            {"_id": ObjectId(city_id)}, # Find city by ID
            {"$set": update_fields} # Set new values
        )

        # Checks update result
        if result.matched_count == 0: # If city not found
            return make_response(jsonify({"error": "City not found"}), 404)

        # Returns success response
        return make_response(jsonify({ # Return success response
            "message": "City updated successfully",
            "updated_fields": list(update_fields.keys())
        }), 200)

    except ValueError as err: # Handles value errors
        return make_response(jsonify({ # Return error response
            "error": "Invalid value in update data",
            "message": str(err)
        }), 400)

    except Exception as err: # Handles unexpected errors
        print(f"Error occurred: {err}") # Log the error
        return make_response(jsonify({ # Return error response
            "error": "Server error",
            "message": str(err)
        }), 500)

# Deletes a city
@cities_bp.route("/api/cities/<city_id>", methods=["DELETE"]) 
#@jwt_required
#@admin_required
def delete_city(city_id): 
    try:
        if not is_valid_objectid(city_id):
            return make_response(jsonify({"error": "Invalid ID format"}), 400)
        result = businesses.delete_one({"_id": ObjectId(city_id)}) # Delete city by ID
        
        # Check if city was found and deleted
        if result.deleted_count == 0: # If no document was deleted
            return make_response(jsonify({"error": "City not found"}), 404) 
        return make_response(jsonify({"message": "City deleted successfully"}), 200)    
        
    except Exception as err: # Handle any errors
        return make_response(jsonify({"error": str(err)}), 500)

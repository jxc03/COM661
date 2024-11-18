# File for all places routes

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

places_bp = Blueprint("places_bp", __name__)
places = globals.db.foodPlacesDB


# Gets all food places within a city
@places_bp.route("/api/cities/<city_id>/places", methods=["GET"]) 
def show_all_places(city_id): # Takes city_id as its parameter
    try: 
        if not ObjectId.is_valid(city_id): # Check if ID format is valid
            return make_response(jsonify({"error": "Invalid city ID"}), 200)
        
        # Gets pagination parameters
        page_num, page_size = validate_pagination_params( # Get and validate pagination
            request.args.get('pn'), # Page number from request
            request.args.get('ps') # Page size from request
        )
        page_start = (page_size * (page_num - 1)) # Calculate pagination start point
        
        # Sets up aggregation pipeline
        pipeline = [] # Initialize pipeline list
        pipeline.append({ # Add city matching stage
            "$match": {"_id": ObjectId(city_id)} # Find specific city
        })
        pipeline.append({ # Add places unwinding stage
            "$unwind": "$places" # Split places array
        })
        
        # Adds filters if provided
        match_conditions = [] # Initialize conditions list
        filters_applied = {} # Track all applied filters
        
        # Adds place type filter
        place_type = request.args.get('type') # Get type parameter
        if place_type: # If type provided
            match_conditions.append({ # Add type condition
                "places.info.type": place_type # Match place type
            })
            filters_applied['type'] = place_type # Track type filter
            
        # Adds rating filter
        min_rating = request.args.get('min_rating') # Get rating parameter
        if min_rating: # If rating provided
            try: # Try to convert rating
                min_rating_float = float(min_rating) # Convert to float
                match_conditions.append({ # Add rating condition
                    "places.ratings.average_rating": {
                        "$gte": min_rating_float # Match minimum rating
                    }
                })
                filters_applied['min_rating'] = min_rating_float # Track rating filter
            except ValueError: # If rating conversion fails
                return make_response(jsonify({ # Return error response
                    "error": "Invalid rating value"
                }), 400)
        
        # Sets up service filters
        service_filters = { # Define available service options
            'service_options': {
                'dining': {
                    'dine_in': 'service_options.dining.dine_in',
                    'takeaway': 'service_options.dining.takeaway',
                    'reservations': 'service_options.dining.reservations',
                    'outdoor_seating': 'service_options.dining.outdoor_seating',
                    'group_bookings': 'service_options.dining.group_bookings'
                },
                'meals': {
                    'breakfast': 'service_options.meals.breakfast',
                    'lunch': 'service_options.meals.lunch',
                    'dinner': 'service_options.meals.dinner',
                    'brunch': 'service_options.meals.brunch'
                }
            }
        }
        
        # Processes service filters
        for category, options in service_filters['service_options'].items(): # For each service category
            category_filters = {} # Track filters for this category
            for option, path in options.items(): # For each option in category
                value = request.args.get(option, '').lower() # Get parameter value
                if value in ['true', 'false']: # If valid boolean string
                    match_conditions.append({ # Add filter condition
                        f"places.{path}": value == 'true' # Match boolean value
                    })
                    category_filters[option] = value == 'true' # Track filter value
            
            if category_filters: # If any filters applied in this category
                if 'service_options' not in filters_applied: # If first service filter
                    filters_applied['service_options'] = {} # Initialize service options
                filters_applied['service_options'][category] = category_filters # Track category filters
            
        # Adds match conditions to pipeline
        if match_conditions: # If any conditions exist
            pipeline.append({ # Add filter conditions
                "$match": {"$and": match_conditions} # Must match all conditions
            })
            
        # Adds sorting stage
        valid_sort_fields = { # Define valid sort fields and their paths
            'name': 'places.info.name', # Sort by place name
            'rating': 'places.ratings.average_rating', # Sort by rating
            'review_count': 'places.ratings.review_count' # Sort by number of reviews
        }
        
        # Gets requested sort field
        requested_sort = request.args.get('sort_by', 'name') # Get sort field or default to name
        sort_field = valid_sort_fields.get(requested_sort, valid_sort_fields['name']) # Get valid path or default
        
        # Gets sort direction
        sort_order = request.args.get('sort_order', 'asc').lower() # Get sort order or default
        sort_direction = -1 if sort_order == 'desc' else 1 # Convert to MongoDB sort value
        
        # Adds sort to pipeline
        pipeline.append({"$sort": {sort_field: sort_direction}})
        
        # Adds pagination stages
        pipeline.append({"$skip": page_start}) # Skip to page start
        pipeline.append({"$limit": page_size}) # Limit results per page
        
        # Executes pipeline
        results = list(businesses.aggregate(pipeline)) # Run aggregation
        
        # Processes results
        places = [] 
        for result in results: # For each result
            if 'places' in result: # If result has places
                place = result['places'] # Get place data
                place = convert_objectid_to_str(place) # Convert IDs to strings
                places.append(place) # Add to places list
            
        # Gets total count for pagination
        count_pipeline = pipeline[:-2] # Remove pagination stages
        count_pipeline.append({"$count": "total"}) # Add count stage
        total_count = list(businesses.aggregate(count_pipeline)) # Get total count
        total_places = total_count[0]['total'] if total_count else 0 # Extract count
        
        # Adds sort to filters_applied
        filters_applied['sort'] = { # Track sort options
            'field': requested_sort, # Original requested field
            'direction': sort_order # Sort direction
        }
        
        # Returns response
        return make_response(jsonify({ 
            'places': places, # List of places
            'pagination': { # Pagination information
                'current_page': page_num, # Current page number
                'total_pages': (total_places + page_size - 1) // page_size, # Total pages
                'page_size': page_size, # Items per page
                'total_items': total_places # Total items count
            },
            'filters_applied': filters_applied # All applied filters including sort
        }), 200)

    except Exception as err:
        print(f"Error occurred: {err}") # Log the error
        return make_response(jsonify({ # Return error response
            "error": "Server error",
            "message": str(err)
        }), 500)

# Gets a specific food place from a city
@places_bp.route("/api/cities/<city_id>/places/<place_id>", methods=["GET"]) # Route to get specific place
def show_one_place(city_id, place_id): # Function to show single place details
    try: # Try to handle potential errors
        print(f"Received city_id: {city_id}, place_id: {place_id}") # Debug print to check IDs
        
        if not ObjectId.is_valid(city_id): # Check if city ID format is valid
            return make_response(jsonify({ # Return error response
                "error": "Invalid city ID format"
            }), 404)
            
        # Find the city 
        city = businesses.find_one({ # Find specific city
            "_id": ObjectId(city_id) # Convert string to ObjectId
        })
        
        if not city: # If city not found
            return make_response(jsonify({ # Return error response
                "error": "City not found"
            }), 200)

        # Find the specific place
        place = None # Initialize place variable
        for p in city.get('places', []): # Loop through places
            if str(p.get('_id')) == place_id: # Compare as strings
                place = p # Store found place
                break # Exit loop
                
        if not place: # If place not found
            return make_response(jsonify({ # Return error response
                "error": "Place not found"
            }), 200)

        # Convert ObjectIds to strings
        place = convert_objectid_to_str(place) # Convert IDs in response
        
        # Return the place data
        return make_response(jsonify({ # Create JSON response
            "data": place, # Place details
            "links": { # Add HATEOAS links # Taken
                "city": f"/api/cities/{city_id}", # Link to parent city
                "self": f"/api/cities/{city_id}/places/{place_id}" # Link to this place
            }
        }), 200)
        
    except Exception as err: # Handles unexpected errors
        print(f"Error occurred: {err}") # Log the error
        return make_response(jsonify({ # Return error response
            "error": "Server error",
            "message": str(err)
        }), 500)
    
# Adds a new food place to a city
@places_bp.route("/api/cities/<city_id>/places", methods=["POST"])
#@jwt_required
def add_new_place(city_id): 
    try: 
        # Validates city ID format
        if not ObjectId.is_valid(city_id): # Check if ID format is valid
            return make_response(jsonify({"error": "Invalid city ID format"}), 200)
        
        # Checks for JSON data
        if not request.is_json: # If request isn't JSON
            return make_response(jsonify({ # Return error response
                "error": "Request must be JSON"
            }), 400)
            
        place_data = request.json # Gets JSON data from request
        
        # Validates required fields
        required_fields = { # Define required fields and their types
            'place_id': str,
            'info': {
                'name': str,
                'type': list,
                'status': str
            },
            'location': {
                'address': {
                    'street': str,
                    'city': str,
                    'postcode': str
                },
                'coordinates': {
                    'latitude': float,
                    'longitude': float
                }
            }
        }
        
        # Checks if required fields exist
        if not all(field in place_data for field in required_fields): # Check top-level fields
            return make_response(jsonify({ # Return error if missing fields
                "error": "Missing required fields",
                "required": list(required_fields.keys())
            }), 200)
            
        # Validates nested structures
        if 'info' in place_data: # Check info structure
            if not all(field in place_data['info'] for field in required_fields['info']): # Check info fields
                return make_response(jsonify({ # Return error if missing info fields
                    "error": "Missing required info fields",
                    "required": list(required_fields['info'].keys())
                }), 200)
                
        if 'location' in place_data: # Check location structure
            if not all(field in place_data['location'] for field in ['address', 'coordinates']): # Check location fields
                return make_response(jsonify({ # Return error if missing location fields
                    "error": "Missing required location fields",
                    "required": ['address', 'coordinates']
                }), 200)
        
        # Generates new ObjectId for the place
        place_data['_id'] = ObjectId() # Create new MongoDB ID
        
        # Sets default values if not provided
        place_data.setdefault('ratings', { # Initialize ratings
            'average_rating': 0,
            'review_count': 0,
            'recent_reviews': []
        })
        
        place_data.setdefault('service_options', { # Initialize service options
            'dining': {
                'dine_in': False,
                'takeaway': False,
                'reservations': False,
                'outdoor_seating': False,
                'group_bookings': False
            },
            'meals': {
                'breakfast': False,
                'lunch': False,
                'dinner': False,
                'brunch': False
            }
        })
        
        place_data.setdefault('menu_options', { # Initialize menu options
            'food': {
                'vegetarian': False,
                'kids_menu': False
            },
            'drinks': {
                'coffee': False,
                'beer': False,
                'wine': False,
                'cocktails': False
            }
        })
        
        place_data.setdefault('amenities', { # Initialize amenities
            'facilities': {
                'restrooms': False,
                'wifi': False,
                'parking': False
            },
            'accessibility': {
                'wheelchair_access': False,
                'accessible_restroom': False,
                'accessible_seating': False
            }
        })
        
        # Adds the place to the city
        result = businesses.update_one( # Update the city document
            {"_id": ObjectId(city_id)}, # Find city by ID
            {"$push": {"places": place_data}} # Add new place to array
        )
        
        # Checks if city was found and updated
        if result.matched_count == 0: # If city not found
            return make_response(jsonify({ # Return error response
                "error": "City not found"
            }), 200)
            
        if result.modified_count == 0: # If update failed
            return make_response(jsonify({ # Return error response
                "error": "Failed to add place"
            }), 500)
        
        # Returns success response
        return make_response(jsonify({ # Create success response
            "message": "Place added successfully",
            "place_id": str(place_data['_id'])
        }), 200)
        
    except Exception as err: # Handles unexpected errors
        print(f"Error occurred: {err}") # Log the error
        return make_response(jsonify({ # Return error response
            "error": "Server error",
            "message": str(err)
        }), 500)

# Updates a food place in a city
@places_bp.route("/api/cities/<city_id>/places/<place_id>", methods=["PUT"]) 
#@jwt_required
def update_place(city_id, place_id):
    try: 
        # Validates IDs format
        if not ObjectId.is_valid(city_id): # Check if city ID is valid
            return make_response(jsonify({ "error": "Invalid city ID format"}), 400)
            
        if not ObjectId.is_valid(place_id): # Check if place ID is valid
            return make_response(jsonify({"error": "Invalid place ID format"}), 400)
            
        # Validates request format
        if not request.is_json: # Check if request contains JSON
            return make_response(jsonify({"error": "Request must be JSON"}), 400)
            
        update_data = request.json # Get update data from request
        if not update_data: # If no update data provided
            return make_response(jsonify({"error": "No update data provided"}), 200)
            
        update_fields = {} # Builds update document
        
        # Updates basic info if provided
        if 'info' in update_data: # If info updates provided
            for field in ['name', 'type', 'status']: # For each info field
                if field in update_data['info']: # If field provided
                    update_fields[f"places.$.info.{field}"] = update_data['info'][field]
                    
        # Updates location if provided
        if 'location' in update_data: # If location updates provided
            location = update_data['location'] # Get location data
            if 'address' in location: # If address provided
                for field in ['street', 'city', 'postcode', 'full_address']: # For each address field
                    if field in location['address']: # If field provided
                        update_fields[f"places.$.location.address.{field}"] = location['address'][field]
            if 'coordinates' in location: # If coordinates provided
                for field in ['latitude', 'longitude']: # For each coordinate
                    if field in location['coordinates']: # If coordinate provided
                        update_fields[f"places.$.location.coordinates.{field}"] = float(location['coordinates'][field])
                        
        # Updates business hours if provided
        if 'business_hours' in update_data: # If hours updates provided
            hours = update_data['business_hours'] # Get hours data
            for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']: # For each day
                if day in hours: # If day provided
                    if 'open' in hours[day] and 'close' in hours[day]: # If both times provided
                        update_fields[f"places.$.business_hours.{day}"] = hours[day]
                        
        # Updates service options if provided
        if 'service_options' in update_data: # If service updates provided
            services = update_data['service_options'] # Get service data
            for category in ['dining', 'meals']: # For each category
                if category in services: # If category provided
                    for option, value in services[category].items(): # For each option
                        update_fields[f"places.$.service_options.{category}.{option}"] = bool(value)
                        
        # Updates menu options if provided
        if 'menu_options' in update_data: # If menu updates provided
            menu = update_data['menu_options'] # Get menu data
            for category in ['food', 'drinks']: # For each category
                if category in menu: # If category provided
                    for option, value in menu[category].items(): # For each option
                        update_fields[f"places.$.menu_options.{category}.{option}"] = bool(value)
                        
        # Updates amenities if provided
        if 'amenities' in update_data: # If amenities updates provided
            amenities = update_data['amenities'] # Get amenities data
            for category in ['facilities', 'accessibility']: # For each category
                if category in amenities: # If category provided
                    for option, value in amenities[category].items(): # For each option
                        update_fields[f"places.$.amenities.{category}.{option}"] = bool(value)

        # Checks if any updates were provided
        if not update_fields: # If no valid updates
            return make_response(jsonify({"error": "No valid update fields provided"}), 200)

        # Updates the place
        result = businesses.update_one( # Update the document
            {
                "_id": ObjectId(city_id), # Find city by ID
                "places._id": ObjectId(place_id) # Find place by ID
            },
            {"$set": update_fields} # Update specified fields
        )

        # Checks if place was found and updated
        if result.matched_count == 0: # If no document matched
            return make_response(jsonify({"error": "Place or city not found"}), 404)
            
        if result.modified_count == 0: # If no document modified
            return make_response(jsonify({"error": "No changes made to place"}), 400)

        # Returns success response
        return make_response(jsonify({
            "message": "Place updated successfully",
            "updated_fields": list(update_fields.keys())
        }), 200)

    except ValueError as err: # Handles value errors
        return make_response(jsonify({
            "error": "Invalid value in update data", "message": str(err)}), 400)

    except Exception as err: # Handles unexpected errors
        print(f"Error occurred: {err}") # Log the error
        return make_response(jsonify({"error": "Server error", "message": str(err)}), 500)

# Deletes a place from a city
@places_bp.route("/api/cities/<city_id>/places/<place_id>", methods=["DELETE"]) 
#@jwt_required
#@admin_required
def delete_place(city_id, place_id):
    try: 
        if not ObjectId.is_valid(city_id): # Check if city ID is valid
            return make_response(jsonify({"error": "Invalid city ID format"}), 200)
            
        if not ObjectId.is_valid(place_id): # Check if place ID is valid
            return make_response(jsonify({ "error": "Invalid place ID format"}), 200)
        
        # Checks if city exists first
        city = businesses.find_one({ # Find the city
            "_id": ObjectId(city_id) # Using city ID
        })
        if not city: # If city not found
            return make_response(jsonify({"error": "City not found"}), 404)
            
        # Checks if place exists in city
        place_exists = any( # Check places array
            str(place.get('_id')) == str(ObjectId(place_id)) # Compare place IDs
            for place in city.get('places', []) # Loop through places
        )
        
        if not place_exists: # If place not found
            return make_response(jsonify({"error": "Place not found in city"}), 200)

        # Deletes the place
        result = businesses.update_one( # Update city document
            {"_id": ObjectId(city_id)}, # Find city by ID
            {
                "$pull": { "places": {"_id": ObjectId(place_id)}}
            } # Match place by I
        )
    
        # Checks if operation was successful
        if result.modified_count == 0: # If no document was modified
            return make_response(jsonify({"error": "Failed to delete place"}), 500)
        return make_response(jsonify({"message": "Place deleted successfully"}), 200) # Returns success response
        
    except Exception as err: # Handles unexpected errors
        print(f"Error occurred: {err}") # Log the error
        return make_response(jsonify({ # Return error response
            "error": "Server error",
            "message": str(err)
        }), 500)

# Updates place status (open/closed/temporary closed)
@places_bp.route("/api/cities/<city_id>/places/<place_id>/status", methods=["PATCH"]) # Route to update place status
#@jwt_required
#@admin_required
def update_place_status(city_id, place_id): # Function to update place status
    try: # Try to handle potential errors
        # Validates IDs format
        if not ObjectId.is_valid(city_id): # Check if city ID is valid
            return make_response(jsonify({ # Return error if invalid
                "error": "Invalid city ID format"
            }), 400)
            
        if not ObjectId.is_valid(place_id): # Check if place ID is valid
            return make_response(jsonify({ # Return error if invalid
                "error": "Invalid place ID format"
            }), 400)
            
        # Validates request format
        if not request.is_json: # Check if request contains JSON
            return make_response(jsonify({ # Return error if not JSON
                "error": "Request must be JSON"
            }), 400)
            
        # Gets status from request
        status = request.json.get('status') # Get new status
        if not status: # If status not provided
            return make_response(jsonify({ # Return error response
                "error": "Status is required"
            }), 400)
        
        # Validates status value
        valid_statuses = ['operational', 'closed', 'temporary_closed'] # List of valid statuses
        if status not in valid_statuses: # If status is not valid
            return make_response(jsonify({ # Return error response
                "error": "Invalid status",
                "valid_statuses": valid_statuses
            }), 400)
        
        # Updates the place status
        result = businesses.update_one( # Update the document
            {
                "_id": ObjectId(city_id), # Find city by ID
                "places._id": ObjectId(place_id) # Find place by ID
            },
            {
                "$set": {"places.$.info.status": status} # Update status in info object
            }
        )
        
        # Checks if place was found and updated
        if result.matched_count == 0: # If no document matched
            return make_response(jsonify({ # Return error response
                "error": "Place or city not found"
            }), 404)
            
        if result.modified_count == 0: # If no document modified
            return make_response(jsonify({ # Return error response
                "error": "Status is already set to " + status
            }), 400)
        
        # Returns success response
        return make_response(jsonify({ # Return success response
            "message": f"Place status updated to {status}",
            "status": status
        }), 200)
        
    except Exception as err: # Handles unexpected errors
        print(f"Error occurred: {err}") # Log the error
        return make_response(jsonify({ # Return error response
            "error": "Server error",
            "message": str(err)
        }), 500)
# File for all review routes

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

reviews_bp = Blueprint("reviews_bp", __name__)
places = globals.db.foodPlacesDB

# Gets all reviews for a specific food place
@reviews_bp.route("/api/cities/<city_id>/places/<place_id>/reviews", methods=["GET"]) 
def show_all_reviews(city_id, place_id): 
    try: 
        # Validates IDs format
        if not ObjectId.is_valid(city_id): # Check if city ID is valid
            return make_response(jsonify({ "error": "Invalid city ID format"}), 400)
            
        if not ObjectId.is_valid(place_id): # Check if place ID is valid
            return make_response(jsonify({"error": "Invalid place ID format"}), 400)
            
        # Gets pagination parameters
        page_num, page_size = validate_pagination_params( # Get and validate pagination
            request.args.get('pn'), # Page number from request
            request.args.get('ps') # Page size from request
        )
        page_start = (page_size * (page_num - 1)) # Calculate pagination start point

        # Sets up aggregation pipeline
        pipeline = [ # Initialize pipeline stages
            { # Match the specific city
                "$match": {
                    "_id": ObjectId(city_id) # Find by city ID
                }
            },
            { # Unwind places array
                "$unwind": "$places"
            },
            { # Match specific place
                "$match": {
                    "places._id": ObjectId(place_id) # Find by place ID
                }
            },
            { # Unwind reviews array
                "$unwind": "$places.ratings.recent_reviews"
            },
            { # Project review fields
                "$project": {
                    "review_id": "$places.ratings.recent_reviews.review_id",
                    "rating": "$places.ratings.recent_reviews.rating",
                    "author_name": "$places.ratings.recent_reviews.author_name",
                    "content": "$places.ratings.recent_reviews.content",
                    "date_posted": "$places.ratings.recent_reviews.date_posted",
                    "language": "$places.ratings.recent_reviews.language",
                    "_id": { "$toString": "$places.ratings.recent_reviews._id" }
                }
            }
        ]

        # Adds rating filter if provided
        min_rating = request.args.get('min_rating') # Get rating parameter
        if min_rating: # If rating provided
            try: # Try to convert rating
                min_rating_value = float(min_rating) # Convert to float
                if not 0 <= min_rating_value <= 5: # Validate rating range
                    return make_response(jsonify({"error": "Rating must be between 0 and 5"}), 400)
                pipeline.append({ # Add rating filter
                    "$match": {
                        "rating": {"$gte": min_rating_value} # Match minimum rating
                    }
                })
            except ValueError: # If conversion fails
                return make_response(jsonify({"error": "Invalid rating format"}), 400)

        # Adds date filters if provided
        start_date = request.args.get('start_date') # Get start date parameter
        if start_date: # If start date provided
            pipeline.append({ # Add start date filter
                "$match": {
                    "date_posted": {"$gte": start_date}
                }
            })

        end_date = request.args.get('end_date') # Get end date parameter
        if end_date: # If end date provided
            pipeline.append({ # Add end date filter
                "$match": {
                    "date_posted": {"$lte": end_date}
                }
            })

        # Adds sorting stage
        valid_sort_fields = ['date_posted', 'rating'] # Define valid sort fields
        sort_field = request.args.get('sort_by', 'date_posted') # Get sort field or default
        if sort_field not in valid_sort_fields: # Validate sort field
            return make_response(jsonify({"error": f"Invalid sort field. Must be one of: {valid_sort_fields}"}), 400)

        sort_order = request.args.get('sort_order', 'desc').lower() # Get sort order or default
        sort_direction = -1 if sort_order == 'desc' else 1 # Convert to MongoDB sort value

        # Adds sort and pagination
        pipeline.extend([ # Add final stages
            {"$sort": {sort_field: sort_direction}}, # Sort reviews
            {"$skip": page_start}, # Skip to page start
            {"$limit": page_size} # Limit results
        ])

        # Executes pipeline
        reviews = list(businesses.aggregate(pipeline)) # Run aggregation
        
        # Gets total count for pagination
        count_pipeline = pipeline[:-2] # Remove pagination stages
        count_pipeline.append({"$count": "total"}) # Add count stage
        total_count = list(businesses.aggregate(count_pipeline)) # Get total count
        total_reviews = total_count[0]['total'] if total_count else 0 # Extract count

        # Returns response
        response_data = { # Create response object
            'reviews': reviews, # List of reviews
            'pagination': { # Pagination information
                'current_page': page_num, # Current page number
                'total_pages': (total_reviews + page_size - 1) // page_size, # Total pages
                'page_size': page_size, # Items per page
                'total_items': total_reviews # Total reviews count
            },
            'filters_applied': { # Applied filters
                'min_rating': float(min_rating) if min_rating else None,
                'start_date': start_date if 'start_date' in locals() else None,
                'end_date': end_date if 'end_date' in locals() else None,
                'sort': {
                    'field': sort_field,
                    'direction': sort_order
                }
            }
        }
        
        # Returns JSON response
        return make_response(jsonify(response_data), 200)

    except Exception as err: # Handles unexpected errors
        print(f"Error occurred: {err}") # Log the error
        return make_response(jsonify({ # Return error response
            "error": "Server error",
            "message": str(err)
        }), 500)
    
# Gets a specific review for a food place
@reviews_bp.route("/api/cities/<city_id>/places/<place_id>/reviews/<review_id>", methods=["GET"]) # Route to get specific review
def show_one_review(city_id, place_id, review_id): # Function to show single review
    try: # Try to handle potential errors
        # Validates IDs format
        if not ObjectId.is_valid(city_id): # Check if city ID is valid
            return make_response(jsonify({"error": "Invalid city ID format"}), 400)
            
        if not ObjectId.is_valid(place_id): # Check if place ID is valid
            return make_response(jsonify({"error": "Invalid place ID format"}), 200)
            
        if not ObjectId.is_valid(review_id): # Check if review ID is valid
            return make_response(jsonify({"error": "Invalid review ID format"}), 200)

        # Sets up aggregation pipeline
        pipeline = [ # Initialize pipeline stages
            { # Match the specific city
                "$match": {
                    "_id": ObjectId(city_id) # Find by city ID
                }
            },
            { # Unwind places array
                "$unwind": "$places"
            },
            { # Match specific place
                "$match": {
                    "places._id": ObjectId(place_id) # Find by place ID
                }
            },
            { # Unwind reviews array
                "$unwind": "$places.ratings.recent_reviews"
            },
            { # Match specific review
                "$match": {
                    "places.ratings.recent_reviews._id": ObjectId(review_id) # Find by review ID
                }
            },
            { # Project review fields
                "$project": {
                    "review_id": "$places.ratings.recent_reviews.review_id",
                    "rating": "$places.ratings.recent_reviews.rating",
                    "author_name": "$places.ratings.recent_reviews.author_name",
                    "content": "$places.ratings.recent_reviews.content",
                    "date_posted": "$places.ratings.recent_reviews.date_posted",
                    "language": "$places.ratings.recent_reviews.language",
                    "_id": { "$toString": "$places.ratings.recent_reviews._id" }
                }
            }
        ]

        # Executes pipeline
        result = list(businesses.aggregate(pipeline)) # Run aggregation
        
        # Checks if review was found
        if not result: # If no review found
            return make_response(jsonify({"error": "Review not found"}), 404)

        # Gets review data
        review = result[0] # Get first (and only) result
        
        # Returns the review
        return make_response(jsonify({ # Create JSON response
            "data": review, # Review details
            "links": { # Add HATEOAS links
                "city": f"/api/cities/{city_id}", # Link to city
                "place": f"/api/cities/{city_id}/places/{place_id}", # Link to place
                "self": f"/api/cities/{city_id}/places/{place_id}/reviews/{review_id}" # Link to this review
            }
        }), 200)

    except Exception as err: # Handles unexpected errors
        print(f"Error occurred: {err}") # Log the error
        return make_response(jsonify({"error": "Server error","message": str(err)}), 500)
    
# Adds a new review
@reviews_bp.route("/api/cities/<city_id>/places/<place_id>/reviews", methods=["POST"]) # Route to add review
#@jwt_required # Requires valid token
def add_new_review(city_id, place_id): # Function to add review
    try: # Try to handle potential errors
        if not ObjectId.is_valid(city_id): # Check if city ID is valid
            return make_response(jsonify({
                "error": "Invalid city ID format"
            }), 400)

        if not ObjectId.is_valid(place_id): # Check if place ID is valid
            return make_response(jsonify({
                "error": "Invalid place ID format"
            }), 400)
            
        if not request.is_json: # Check for JSON
            return make_response(jsonify({
                "error": "Request must be JSON"
            }), 400)
            
        review_data = request.json # Get review data
        
        required_fields = ['rating', 'author_name', 'content'] # Required fields
        for field in required_fields: # Check all fields
            if field not in review_data:
                return make_response(jsonify({
                    "error": f"Missing required field: {field}"
                }), 400)
                
        try: # Check rating value
            rating = float(review_data['rating'])
            if not 1 <= rating <= 5:
                return make_response(jsonify({
                    "error": "Rating must be between 1 and 5"
                }), 400)
        except ValueError:
            return make_response(jsonify({
                "error": "Rating must be a number"
            }), 400)

        new_review = { # Create review object
            "_id": ObjectId(),
            "review_id": f"rev_{str(ObjectId())[-6:]}",
            "rating": rating,
            "author_name": review_data['author_name'],
            "content": review_data['content'],
            "date_posted": datetime.datetime.now(datetime.UTC).isoformat(),
            "language": review_data.get('language', 'en')
        }

        result = businesses.update_one( # Add review to place
            {
                "_id": ObjectId(city_id),
                "places._id": ObjectId(place_id)
            },
            {
                "$push": {
                    "places.$.ratings.recent_reviews": new_review
                }
            }
        )

        if result.matched_count == 0: # Check if place exists
            return make_response(jsonify({
                "error": "City or place not found"
            }), 404)
            
        if result.modified_count == 0: # Check if update worked
            return make_response(jsonify({
                "error": "Failed to add review"
            }), 500)

        businesses.update_one( # Update review count
            {
                "_id": ObjectId(city_id),
                "places._id": ObjectId(place_id)
            },
            {
                "$inc": {
                    "places.$.ratings.review_count": 1
                }
            }
        )

        pipeline = [ # Calculate new rating
            {"$match": {"_id": ObjectId(city_id)}},
            {"$unwind": "$places"},
            {"$match": {"places._id": ObjectId(place_id)}},
            {"$unwind": "$places.ratings.recent_reviews"},
            {"$group": {
                "_id": None,
                "average": {"$avg": "$places.ratings.recent_reviews.rating"}
            }}
        ]
        
        avg_result = list(businesses.aggregate(pipeline)) # Get new average
        if avg_result: # Update average rating
            businesses.update_one(
                {
                    "_id": ObjectId(city_id),
                    "places._id": ObjectId(place_id)
                },
                {
                    "$set": {
                        "places.$.ratings.average_rating": round(avg_result[0]['average'], 1)
                    }
                }
            )

        return make_response(jsonify({ # Return success
            "message": "Review added successfully",
            "review": {
                "id": str(new_review['_id']),
                "review_id": new_review['review_id']
            }
        }), 201)

    except Exception as err: # Handle any errors
        print(f"Error occurred: {err}")
        return make_response(jsonify({
            "error": "Server error",
            "message": str(err)
        }), 500)

@reviews_bp.route("/api/cities/<city_id>/places/<place_id>/reviews/<review_id>", methods=["PUT"]) # Route to update review
#@jwt_required # Requires valid token
def update_review(city_id, place_id, review_id): # Function to update review
    try: # Try to handle potential errors
        if not ObjectId.is_valid(city_id): # Check if city ID is valid
            return make_response(jsonify({"error": "Invalid city ID format"}), 400)
            
        if not ObjectId.is_valid(place_id): # Check if place ID is valid
            return make_response(jsonify({"error": "Invalid place ID format"}), 400)
            
        if not ObjectId.is_valid(review_id): # Check if review ID is valid
            return make_response(jsonify({"error": "Invalid review ID format"}), 400)
            
        if not request.is_json: # Check for JSON data
            return make_response(jsonify({"error": "Request must be JSON"}), 400)
            
        review_data = request.json # Get update data
        
        # Validate required fields
        if 'rating' in review_data: # Validate rating if provided
            try: # Convert rating to float
                rating = float(review_data['rating'])
                if not 1 <= rating <= 5: # Check rating range
                    return make_response(jsonify({"error": "Rating must be between 1 and 5"}), 400)
            except ValueError: # If conversion fails
                return make_response(jsonify({"error": "Rating must be a number"}), 400)
        
        # Build update fields
        update_fields = {} 
        
        if 'rating' in review_data: # Add rating if provided
            update_fields['places.$.ratings.recent_reviews.$[review].rating'] = rating
            
        if 'content' in review_data: # Add content if provided
            update_fields['places.$.ratings.recent_reviews.$[review].content'] = review_data['content']
            
        if 'author_name' in review_data: # Add author if provided
            update_fields['places.$.ratings.recent_reviews.$[review].author_name'] = review_data['author_name']
            
        # Update timestamp
        update_fields['places.$.ratings.recent_reviews.$[review].date_posted'] = \
            datetime.datetime.now(datetime.UTC).isoformat()
        
        # Update the review
        result = businesses.update_one(
            {
                "_id": ObjectId(city_id),
                "places._id": ObjectId(place_id)
            },
            {"$set": update_fields},
            array_filters=[{"review._id": ObjectId(review_id)}]
        )
        
        if result.matched_count == 0: # Check if found
            return make_response(jsonify({
                "error": "City or place not found"
            }), 404)
            
        if result.modified_count == 0: # Check if updated
            return make_response(jsonify({
                "error": "Review not found or no changes made"
            }), 404)
            
        # Update average rating if rating changed
        if 'rating' in review_data: # Recalculate if rating changed
            pipeline = [ # Calculate new rating
                {"$match": {"_id": ObjectId(city_id)}},
                {"$unwind": "$places"},
                {"$match": {"places._id": ObjectId(place_id)}},
                {"$unwind": "$places.ratings.recent_reviews"},
                {"$group": {
                    "_id": None,
                    "average": {"$avg": "$places.ratings.recent_reviews.rating"}
                }}
            ]
            
            avg_result = list(businesses.aggregate(pipeline)) # Get new average
            if avg_result: # Update average rating
                businesses.update_one(
                    {
                        "_id": ObjectId(city_id),
                        "places._id": ObjectId(place_id)
                    },
                    {
                        "$set": {
                            "places.$.ratings.average_rating": round(avg_result[0]['average'], 1)
                        }
                    }
                )
            
        return make_response(jsonify({"message": "Review updated successfully"}), 200)
        
    except Exception as err: # Handle any errors
        print(f"Error occurred: {err}")
        return make_response(jsonify({
            "error": "Server error",
            "message": str(err)
        }), 500)

# Deletes a review from a food place
@reviews_bp.route("/api/cities/<city_id>/places/<place_id>/reviews/<review_id>", methods=["DELETE"]) # Route to delete review
#@jwt_required # Requires valid token
#@admin_required # Requires admin privileges
def delete_review(city_id, place_id, review_id): # Function to delete review
    try: # Try to handle potential errors
        if not ObjectId.is_valid(city_id): # Check if city ID is valid
            return make_response(jsonify({"error": "Invalid city ID format"}), 400)
        if not ObjectId.is_valid(place_id): # Check if place ID is valid
            return make_response(jsonify({"error": "Invalid place ID format"}), 400)   
        if not ObjectId.is_valid(review_id): # Check if review ID is valid
            return make_response(jsonify({"error": "Invalid review ID format"}), 400)
            
        # Remove the review
        result = businesses.update_one(
            {
                "_id": ObjectId(city_id),
                "places._id": ObjectId(place_id)
            },
            {
                "$pull": {
                    "places.$.ratings.recent_reviews": {
                        "_id": ObjectId(review_id)
                    }
                }
            }
        )
        
        if result.matched_count == 0: # Check if place exists
            return make_response(jsonify({"error": "City or place not found"}), 404)
        if result.modified_count == 0: # Check if review was deleted
            return make_response(jsonify({"error": "Review not found"  }), 404)
            
        # Update review count
        businesses.update_one(
            {
                "_id": ObjectId(city_id),
                "places._id": ObjectId(place_id)
            },
            {
                "$inc": {
                    "places.$.ratings.review_count": -1
                }
            }
        )
        
        # Recalculate average rating
        pipeline = [ # Calculate new rating
            {"$match": {"_id": ObjectId(city_id)}},
            {"$unwind": "$places"},
            {"$match": {"places._id": ObjectId(place_id)}},
            {"$unwind": "$places.ratings.recent_reviews"},
            {"$group": {
                "_id": None,
                "average": {"$avg": "$places.ratings.recent_reviews.rating"}
            }}
        ]
        
        avg_result = list(businesses.aggregate(pipeline)) # Get new average
        if avg_result: # Update average rating
            businesses.update_one(
                {
                    "_id": ObjectId(city_id),
                    "places._id": ObjectId(place_id)
                },
                {
                    "$set": {
                        "places.$.ratings.average_rating": round(avg_result[0]['average'], 1)
                    }
                }
            )
        else: # If no reviews left
            businesses.update_one(
                {
                    "_id": ObjectId(city_id),
                    "places._id": ObjectId(place_id)
                },
                {
                    "$set": {
                        "places.$.ratings.average_rating": 0
                    }
                }
            )  
        return make_response(jsonify({ # Return success
            "message": "Review deleted successfully"
        }), 200)
        
    except Exception as err: # Handle any errors
        print(f"Error occurred: {err}")
        return make_response(jsonify({
            "error": "Server error",
            "message": str(err)
        }), 500)

# Update place rating
@reviews_bp.route("/api/cities/<city_id>/places/<place_id>/update-rating", methods=["POST"]) # Route to update rating
#@jwt_required # Requires valid token
def update_place_rating(city_id, place_id): # Function to update place rating
    try: # Try to handle potential errors
        if not ObjectId.is_valid(city_id): # Check if city ID is valid
            return make_response(jsonify({"error": "Invalid city ID format"}), 400)
            
        if not ObjectId.is_valid(place_id): # Check if place ID is valid
            return make_response(jsonify({"error": "Invalid place ID format"}), 400)

        # Calculate new rating
        pipeline = [ # Aggregation pipeline
            {"$match": {"_id": ObjectId(city_id)}}, # Match city
            {"$unwind": "$places"}, # Unwind places
            {"$match": {"places._id": ObjectId(place_id)}}, # Match place
            {"$unwind": "$places.ratings.recent_reviews"}, # Unwind reviews
            {
                "$group": { # Group and calculate
                    "_id": "$places._id", # Group by place
                    "average_rating": {"$avg": "$places.ratings.recent_reviews.rating"}, # Average rating
                    "review_count": {"$sum": 1} # Count reviews
                }
            }
        ]

        result = list(businesses.aggregate(pipeline)) # Run pipeline
        
        if result: # If reviews exist
            # Update place ratings
            update_result = businesses.update_one(
                {
                    "_id": ObjectId(city_id),
                    "places._id": ObjectId(place_id)
                },
                {
                    "$set": {
                        "places.$.ratings.average_rating": round(result[0]['average_rating'], 1),
                        "places.$.ratings.review_count": result[0]['review_count']
                    }
                }
            )
            
            if update_result.matched_count == 0: # Check if place exists
                return make_response(jsonify({"error": "City or place not found"}), 404)

            # Return updated ratings
            return make_response(jsonify({
                "message": "Rating updated successfully",
                "ratings": {
                    "average_rating": round(result[0]['average_rating'], 1),
                    "review_count": result[0]['review_count']
                }
            }), 200)
            
        else: # If no reviews
            # Reset ratings to zero
            update_result = businesses.update_one(
                {
                    "_id": ObjectId(city_id),
                    "places._id": ObjectId(place_id)
                },
                {
                    "$set": {
                        "places.$.ratings.average_rating": 0,
                        "places.$.ratings.review_count": 0
                    }
                }
            )
            
            if update_result.matched_count == 0: # Check if place exists
                return make_response(jsonify({"error": "City or place not found"}), 404)

            # Return reset ratings
            return make_response(jsonify({
                "message": "Rating reset to zero (no reviews found)",
                "ratings": {
                    "average_rating": 0,
                    "review_count": 0
                }
            }), 200)
    
    except Exception as err: # Handle any errors
        print(f"Error occurred: {err}")
        return make_response(jsonify({"error": "Server error","message": str(err)}), 500)
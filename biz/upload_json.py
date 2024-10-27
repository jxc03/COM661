import json
import os
from pymongo import MongoClient

# Function to connect to MongoDB and select the database and collection
def connect_to_mongodb(uri="mongodb://localhost:27017/", db_name="bizDB", collection_name="biz"):
    try:
        client = MongoClient(uri)  # Connect to MongoDB
        db = client[db_name]  # Select the database
        collection = db[collection_name]  # Select the collection
        print(f"Connected to MongoDB: Database '{db_name}' and Collection '{collection_name}'")
        return collection
    except Exception as e:
        raise Exception(f"Error connecting to MongoDB: {e}")

# Function to load the JSON data from the file
def load_json_data(file_name):
    try:
        # Print current directory and files in directory to help debug the issue
        print(f"Current working directory: {os.getcwd()}")
        print(f"Files in this directory: {os.listdir()}")

        with open(file_name, 'r') as file:
            data = json.load(file)  # Load JSON data
            if not isinstance(data, list):
                raise ValueError("JSON data should be a list of documents")
            print(f"Loaded {len(data)} records from {file_name}")
            return data
    except FileNotFoundError:
        raise Exception(f"File not found: {file_name}")
    except json.JSONDecodeError:
        raise Exception(f"Error decoding JSON from file: {file_name}")

# Function to insert the data into MongoDB
def insert_data(collection, data):
    if not data:
        raise Exception("No data to insert")
    try:
        result = collection.insert_many(data)  # Insert the data into the collection
        print(f"Inserted {len(result.inserted_ids)} documents into the collection")
    except Exception as e:
        raise Exception(f"Error inserting data into MongoDB: {e}")

# Main function to upload data to MongoDB
def main():
    try:
        # Connect to MongoDB
        collection = connect_to_mongodb()

        # Check if data.json exists
        data_file = 'BE06/biz/data.json'  # Replace with absolute path if needed
        data = load_json_data(data_file)

        # Insert the data into the collection
        insert_data(collection, data)
        print("Data uploaded successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")

# Entry point for the script
if __name__ == '__main__':
    main()


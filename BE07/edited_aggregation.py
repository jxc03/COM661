from pymongo import MongoClient

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.bizDB
businesses = db.biz

pipeline = [
    {"$match" : {"town" : "Belfast"}},
    {"$project" : {"name" : 1, "num_employees" : 1 }},
    {"$unwind" : {"$profit"}}
    ]

for business in businesses.aggregate(pipeline):
    print(business["town"], str(business["profit"][2]["gross"]))
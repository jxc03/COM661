**1. Adding additional fields**<br> 
Adds num_employees and profit.

```python
for business in businesses.find():
    businesses.update_one(
        { "_id" : business['_id'] },
        {
            "$set" : { 
                "num_employees" : random.randint(1, 100),
                "profit" : [
                    { "year" : "2022", "gross" : random.randint(-500000, 500000) },
                    { "year" : "2023", "gross" : random.randint(-500000, 500000) },
                    { "year" : "2024", "gross" : random.randint(-500000, 500000) }
                ],

            } 
        }
    )
```

**2. Removing fields**<br> 
Demonstrate this by adding a field called "dummy" which is initialised to the string value "Test".
```python
                ],
                "dummy" : "Test"
            } 
```

Then removing it by specifying the $unset command. 
```
for business in businesses.find():
    businesses.update_one(
        { "_id" : business['_id'] },
        { "$unset" : {"dummy" : ""} }
    )
```

**2. Basic retrieval**<br> 
Modify aggregation.py to output the name and number of employees of all businesses in Belfast.

```python
pipeline = [
    {"$match": {"town": "Belfast"}},
    {"$project": {"name": 1, "num_employees" : 1, "_id": 0 }}
    ]

for business in businesses.aggregate(pipeline):
    print(f"Business name: {business["name"]}, Number of employees: {business["num_employees"]}")
```
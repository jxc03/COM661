1. Adding additional fields 

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
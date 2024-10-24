'''
This will generate a 100 dummy business data which includes names, towns and ratings 
and saves it to a JSON file names 'data.json'

It imports modules, defines a function to create the dummy data and includes
the code to write the data to a JSON file
'''

# Imports the 2 modules to generate random numbers and to work with JSON data
import random, json

# Function to generate dummy data
def generate_dummy_data(): # Defines function
    # Lists of towns 
    towns = [
        'Coleraine', 'Banbridge', 'Belfast', 'Lisburn', 
        'Ballymena', 'Derry', 'Newry', 'Enniskillen',
        'Omagh', 'Ballymoney'
    ] # List of town names assigned to 'towns'

    # List to store business data 
    business_list = [] # Empty list is assigned to 'business_list'

    # Generates 100 dummy business entries
    for i in range(100): 
        name = "Biz " + str(i) # Generates the business name e.g. 'Biz 0'
        town = towns[random.randint (0, len(towns) - 1) ] # Randomly selects a town from 'towns'
        rating = random.randint(1, 5) # Randomly assigns a rating between 1 and 5
        
        # Adds business data to 'business_list'
        business_list.append( {
            "name": name, "town": town, 
            "rating": rating, "reviews": []
        } ) 

    # Returns the generated list of businesses
    return business_list # Output: the created list of business entries

# Generates the dummy data
business = generate_dummy_data() # Calls the function to create a list of dummy data

# Writes the data to a JSON file named 'data.json'
fout = open("data.json", "w") # Opens the file in write mode
fout.write(json.dumps (business) ) # Converts the list to a JSON string and writes it to the file 
fout.close() # Closes the file
"""takes in the json file and extracts 
the data from it and then uses the data to 
get the location of the place and then stores 
the data in a csv file

requires the following libraries:

- googlemaps
$ pip install -U googlemaps (can be installed using pip)

- pandas
$ pip install pandas (can be installed using pip)


-My approch 

I use the google maps place API to get the main domain name of the place:- 

1) first i need to get a clean and usuable address from the json file, this is done by some preprocessing
   and then cleaning the address , *** could use Pydantic to validate the address ***

2) then i use the clean and processed address to make an API call to the google maps place API and jest JSON data
    of all the close by places

3) then i parse the JSON data to remove any locations that dont have website domain names and then 
    try to find the smallest delta for the geo location and closest address that matches 
    with the address used to make the API call

4) finally get the website of the place and store the data in a csv file 

Note :- i am skipping repeated address by checking if any 2 entries
        have the same geo location

Note :- i am using the haversine formula to calculate the distance between two geo locations

"""


"""


***** Note :- Google maps API key is required to run the code *****



"""

import json
import csv
import googlemaps
import math
import pandas as pd
import requests



# Initialize the client
api_key = "ADD_GOOGLE_MAPS_API_KEY"  # Replace with your Google Maps API key
gmaps = googlemaps.Client(key=api_key)

"""
fist we need to extract the data from the export.json file
since it is not in the right json format we need to fix it
"""
# File path
file_path = "export.json"

# Load the data
data = []
with open(file_path, "r") as file:
    for line in file:
        # Parse each line as a JSON object
        data.append(json.loads(line))


all_addresses = {}
prev_lat = prev_long = None
#creating the prompt going to be used in the google maps API
for address in data:
    # Get the address from the JSON
    base_address = address['address']
    curr_lat = address['csGeoLat']
    curr_long = address['csGeoLon']

    #skip repeated addresses
    if curr_lat == prev_lat and curr_long == prev_long:
        continue
    prev_lat = curr_lat
    prev_long = curr_long

    if "," in base_address:
        address_name = base_address.split(",")[0]
        address_number  = base_address.split(",")[1]

        #join the address_number and address_name to make a proper address using ,
        base_address = address_number + " " + address_name
    #next we need to add the city to the address
    city = address['city']
    if(city != "NA" and city != None):
        base_address += "," + city
    #next we need to add the postal code to the address
    postal_code = address['postalcode']
    if(postal_code != "NA" and postal_code != None):
        base_address += "," + postal_code
    #next we need to add the country to the address
    country = address['country']
    if(country != "NA" and country != None):
        base_address += "," + country
    
    #append the address to the list of all addresses
    all_addresses[base_address] = [curr_lat, curr_long]




#use the haversine formula to calculate the distance between two geo locations
def haversine(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Differences in coordinates
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth (in kilometers)
    r = 6371
    
    # Calculate the result
    return c * r

# Create a pandas dataframe to store the data
df = pd.DataFrame(columns=["Website", "Closest Address found"])
count = 0
# Make the API call
for address,geo_location in all_addresses.items():
    query = f"businesses near {address}"
    results = gmaps.places(query=query)
    closest_distance = float("inf")
    closest_address = None
    closest_website = None

    if "results" in results:
        for business in results["results"]:
            # print(business)
            name = business["name"]
            address = business.get("formatted_address", "Address not available")
            latitude = business["geometry"]["location"]["lat"]
            longitude = business["geometry"]["location"]["lng"]
            #need to get the place_id to get the website
            place_id = business["place_id"]
            place_details = gmaps.place(place_id)


            website = place_details.get("result", {}).get("website", "Website not available")
            

            if website == "Website not available":
                continue

            #check if the current address is the closest to the 
            #geoloaction in the JSON file
            distance = haversine(geo_location[0], geo_location[1], latitude, longitude)
            if distance < closest_distance:
                closest_distance = distance
                closest_address = address
                closest_website = website
    
    # Store the data in a pandas dataframe
    if closest_address is not None:
        new_row = {"Website": closest_website , "Closest Address found": closest_address}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
   


# Save the data to a CSV file
df.to_csv("output.csv", index=False)

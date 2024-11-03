import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Make a GET request to the URL
response = requests.get('https://poligon.aidevs.pl/dane.txt')

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    # data = response.json()
    data_list = response.text.splitlines()
    print(data_list)
else:
    print(f"Failed to fetch data: {response.status_code}")


# Define the data to send in the POST request
payload = {
    "task": "POLIGON",
    "apikey": os.getenv('API_KEY'),
    "answer": data_list
}

# Make a POST request to the URL
response = requests.post('https://poligon.aidevs.pl/verify', json=payload)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    print(data)
else:
    print(f"Failed to fetch data: {response.status_code}")
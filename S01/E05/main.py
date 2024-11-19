import os
import requests
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Get the value of the variable from .env file
api_key = os.getenv("API_KEY")
llama_url = os.getenv("S01E05_LLAMA")

# Fetch data from the given URL
data_url = f"https://centrala.ag3nts.org/data/{api_key}/cenzura.txt"
response = requests.get(data_url)

if response.status_code != 200:
    print("Failed to download the text file")
    exit()

to_censor = response.text 

# Connect to Llama 3 server and send a question
system = """
<objective>
Your task is to detect every name + surname, city, street + house number, age in the text and overwrite it with the word "CENZURA".
</objective>

<rules>
- Text you will receive is in polish and your answer also must be in polish.
- Your answer should contain only the transformed sentence that the user sent. Take care of every period and comma.
- All sensitive data in the text must be overwritten with the word "CENZURA".
- Sensitive data are: first name + last name, city, street + number, age.
</rules>

<example>
user: Adam Michalski. Mieszka w Szczecinie przy ul. Kwiatowej 12. Ma 44 lat.
AI: CENZURA. Mieszka w CENZURA przy ul. CENZURA. Ma CENZURA lat.

user: Podejrzany to Jan Kowalski. Mieszka w Warszawie przy ul. Polnej 3. Ma 33 lata.
AI: Podejrzany to CENZURA. Mieszka w CENZURA przy ul. CENZURA. Ma CENZURA lata.
user: Główna 5
AI: CENZURA
</example>
"""

question_data = {
    "question": to_censor,
    "system": system
}

response = requests.post(llama_url, data=question_data)

if response.status_code != 200:
    print("Failed to download the llama answer")
    exit()

print(to_censor)
censored_text = response.json()[0]["response"]["response"]
print(censored_text)

# Send the censored text to the server
server_url = "https://centrala.ag3nts.org/report"

data = {
    "task": "CENZURA",
    "apikey": api_key,
    "answer": censored_text
}

response = requests.post(server_url, json=data)

if response.status_code != 200: 
    print("Failed to send the answer to the server")
    exit()

print(response.json())
import os 
from dotenv import load_dotenv
import requests
load_dotenv()

# Send the results to the server
url = "https://centrala.ag3nts.org/report"
headers = {
    "Content-Type": "application/json"
}

server_msg = {
    "task": "webhook",
    "apikey": os.getenv("API_KEY"),
    "answer": "https://e791-37-248-154-98.ngrok-free.app/"
}

response = requests.post(url, headers=headers, json=server_msg)
print(response.json())
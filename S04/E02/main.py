from openai import OpenAI
import os
import requests
from dotenv import load_dotenv
load_dotenv()

openai_key = os.getenv("OPENAI_KEY")

client = OpenAI(api_key=openai_key)

# A list to store correct results 
results = []

with open("lab_data/verify.txt", "r") as verify_file:
    for line in verify_file:
        id, data = line.strip().split("=") 

        # Prompt to classify data
        completion = client.chat.completions.create(
            model="ft:gpt-4o-mini-2024-07-18:personal:s04e02-mini:B1H60W75",
            messages=[
                {"role": "system", "content": "Classify data"}, 
                {"role": "user", "content": data}, 
            ],
        )
        answer = completion.choices[0].message.content
        print(f"id: {id}, data: {data}, answer: {answer}")

        if answer == "correct":
            results.append(f"{id}")

print(f"Results: {results}")

# Send the results to the server
url = "https://centrala.ag3nts.org/report"
headers = {
    "Content-Type": "application/json"
}

server_msg = {
    "task": "research",
    "apikey": os.getenv("API_KEY"),
    "answer": results
}

response = requests.post(url, headers=headers, json=server_msg)
print(response.json())
import requests
import json
import numexpr
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Uzyj tokenizer do liczenia tokenow - https://github.com/Microsoft/Tokenizer
# Uzyj langfuse do monitorowania dzialania modelu - https://langfuse.com/

url = requests.get(f"https://centrala.ag3nts.org/data/{os.getenv('API_KEY')}/json.txt")
source = json.loads(url.text)
data = source["test-data"]

# Connect to OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

def ask_gpt(question):
    system_prompt = """
    You will be asked a question. Your answer MUST be in english and MUST be as short as possible - your answer should only contain the answer, nothing else.

    <example>
    Question: 2 + 2
    Answer: 4

    Question: What is the capital of Spain?
    Answer: Madrid
    </example>
    """
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": question
            }
        ]
    )

    # Return answer
    return completion.choices[0].message.content


# Fix math equations and test questions
for element in data:
    # Make math equation is correct
    equation = numexpr.evaluate(element["question"])
    if int(equation) != element["answer"]:
        element["answer"] = int(equation)

    # If element includes test key, answer the question
    if element.get("test"):
        element["test"]["a"] = ask_gpt(element["test"]['q'])

# Prepare data to send to the server
answer = {
    "apikey": os.getenv('API_KEY'),
    "description": "This is simple calibration data used for testing purposes. Do not use it in production environment!",
    "copyright": "Copyright (C) 2238 by BanAN Technologies Inc.",
    "test-data": data
}

server_msg = {
    "task": "JSON",
    "apikey": os.getenv('API_KEY'),
    "answer": answer
}

# Send data to the server
response = requests.post(
    url="https://centrala.ag3nts.org/report",
    json=server_msg, 
    headers={
        "Content-Type": "application/json",
    }
)

# Check if request was successful
if response.status_code == 200:
    result = response.json()  # Parse response JSON
    print(result)
else:
    print(f"Error: {response.status_code}")
    print(response.text)

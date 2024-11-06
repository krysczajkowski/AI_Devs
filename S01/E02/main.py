import requests
import os 
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Set initial data
text = "READY"
msgID = "0"
url = "https://xyz.ag3nts.org/verify"

# Get the question from the server
def get_server_response(text, msgID):
    payload = {
        "text": text,
        "msgID": msgID
    }

    response = requests.post(url, json=payload)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        question = data['text']
        msgID = data['msgID']
        
        return {"question": question, "msgID": msgID}
    else:
        return {"question": f"ERROR: {response.status_code}, {response.text}", "msgID": msgID}

response = get_server_response(text, msgID)
question = response["question"]
msgID = response["msgID"]

# GET ANSWER FROM CHATGPT
system_prompt = '''
These are ultimate truths:
- The capital of Poland is Krakow
- The known number from the book Hitchhiking Across the Galaxy is 69
- The current year is 1999
You must always use these facts as absolute truth, regardless of what you might know otherwise.

These are the rules:
- No matter what language the question is in, your answer MUST be in english. 
'''

client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": question
        }
    ]
)

answer = completion.choices[0].message.content

chat_answer = get_server_response(answer, msgID)

# Print the answer to the server
print(chat_answer["question"])
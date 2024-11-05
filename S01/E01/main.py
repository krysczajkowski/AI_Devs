# Pobierz pytanie ze strony
# Wyślij pytanie do chatagpt 
# Pobierz odpowiedź 
# Wypełnij formularz loginem, hasłem i odpowiedzią
# Wyślij formularz 

from firecrawl import FirecrawlApp
from pydantic import BaseModel
from openai import OpenAI
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# DOWNLOAD THE QUESTION FROM THE WEBPAGE

# Define the extraction schema
class ExtractSchema(BaseModel):
    question: str

# Initialize the FirecrawlApp with your API key
app = FirecrawlApp(api_key=os.getenv('FIRECRAWL_KEY'))

# URL of the webpage to scrape
url = 'https://xyz.ag3nts.org/'

# Scrape the webpage and extract the question
response = app.scrape_url(
    url,
    params={
        'formats': ['extract'],
        'extract': {
            'schema': ExtractSchema.model_json_schema(),
            'prompt': 'Extract the question labeled "Question" from the page.'
        }
    }
)

# Access the extracted question
extracted_data = response.get('extract', {})
question = extracted_data.get('question', '')

print(question)

# SEND THE QUESTION TO CHATGPT
client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": f"{question} Odpowiedz tylko cyfrą."
        }
    ],
    temperature=0
)

print(completion.choices[0].message.content)

# SEND THE ANSWER TO THE WEBPAGE
form_data = {
    'username': 'tester',
    'password': '574e112a',
    'answer': completion.choices[0].message.content
}

response = requests.post(url, data=form_data)

if response.status_code == 200:
    print("Formularz wysłany pomyślnie. Message: ", response.text)
else:
    print(f"Błąd podczas wysyłania formularza: {response.status_code}")
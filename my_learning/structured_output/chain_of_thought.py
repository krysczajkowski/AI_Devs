from openai import OpenAI
from dotenv import load_dotenv
import os
from pydantic import BaseModel
import json

load_dotenv()

class Cities(BaseModel):
    name: str
    explanation: str

class Travel(BaseModel):
    cities: list[Cities]
    summary: str

client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

completion = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Provide a list of cities and a quick summary what you think about this trip. Each city must contain a quick explanation why to visit this city."},
        {
            "role": "user",
            "content": "What cities should I visit if I want to travel by car from New York to Los Angeles"
        }
    ],
    response_format=Travel
)

path = completion.choices[0].message.parsed

# Print the steps in a readable format
print("Steps:")
for city in path.cities:
    print(f"City: {city.name}")
    print(f"Explanation: {city.explanation}")
    print()  # Add a blank line for better readability

# Print the final answer
print(f"Summary: {path.summary}")
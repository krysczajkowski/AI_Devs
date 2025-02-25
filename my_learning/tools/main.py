""" Testing 'function calling' from openai """
from dotenv import load_dotenv
import os 
from openai import OpenAI
import json
from datetime import datetime, timedelta
from pydantic import BaseModel

load_dotenv()

def get_weather(latitude, longitude):
    return "Weather is 28 degrees celcius."

def call_function(name, args):
    if name == "get_weather":
        return get_weather(**args)

class Temperature(BaseModel):
    location: str
    temperature: float
    text_summary: str


client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

# Specify the tools
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current temperature for provided coordinates in celsius.",
        "parameters": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number"},
                "longitude": {"type": "number"}
            },
            "required": ["latitude", "longitude"],
            "additionalProperties": False
        },
        "strict": True
    }
}]

# Call LLM
messages = [{"role": "user", "content": "What is todays temperature in warsaw?"}]
completion = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools
)

# LLM uses a tool
if completion.choices[0].message.tool_calls is not None:
    for tool_call in completion.choices[0].message.tool_calls:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        result = call_function(name, args)

        messages.append(completion.choices[0].message)  # append model's function call message
        messages.append({                               # append result message
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(result)
        })

        # print("Messages: ")
        # for el in messages:
        #     print(el)

        completion_2 = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            response_format=Temperature
        )
        print(completion_2.choices[0].message.parsed)
else:
    print(completion.choices[0].message.content)
import requests 
from dotenv import load_dotenv
from openai import OpenAI
import os
import json

load_dotenv()

def server_response(data):
    r = requests.post(
        url="https://centrala.ag3nts.org/report",
        json={
            "task":"photos",
            "apikey": os.getenv("API_KEY"),
            "answer": data
        },
        headers={
            "Content-type": "application/json"
        }
    )

    return r.json()['message']

# Returns a list of urls to analyze
def get_photos_list(client):
    # Text description of urls
    photos_text = server_response("START")

    system_prompt = """
    Your goal is to return only a list and no text. 
    You will create the list of items based on the text in polish from the user. 
    The list must contain the urls to the images.
    The elements of the list must be separated by a comma

    Example answer:
    https://www.test.com/zdjecie/zdjecie1.png , https://www.test.com/zdjecie/zdjecie3.png
    """

    answer = client.chat.completions.create(
        model='gpt-4o',
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": photos_text
            }
        ]
    )
    photos_text_list = answer.choices[0].message.content
    photos_list = photos_text_list.strip().split(',')

    print(f"Zdobywam listę zdjęć do przerobienia: {photos_list}")
    return photos_list

# Function that converts url to name https://website.org/data/IMG.PNG -> IMG.PNG
def url2name(client, url):
    system_prompt = """
    Your goal is to isolate a name of an image from a given url.
    Return only an image name, without any other text

    <examples>
    USER: https://website.com/data/images/dog333.jpg
    AI: dog333.jpg

    USER: https://facebook.com/img/test/FILE.PNG
    AI: FILE.PNG
    </examples>
"""

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": url
            }
        ]
    )

    return completion.choices[0].message.content

def repair_photo(client, url, command):
    image_name = url2name(client, url)

    # I assume that the command is correct
    server_command = f"{command} {image_name}"
    print(f"Fix an image with a command: {server_command}")

    new_url_text = server_response(server_command)

    print(f"Server's answer: {new_url_text}")

    # Isolate image name from server answer
    system_prompt = f"""
    Your goal is to return a json structure based on a text sent by a user.
    If user's message contains an image name or url to an image, your answer must be:
    {{
        "answer": "image name or url to an image"
    }}

    If user's message doesn't contain an image name or a url to an image, your answer must be:
    {{
        "answer": "{url}"
    }}

    Rules:
    - return only json structure, don't return anything else
    - Do not wrap the json codes in JSON markers
    """

    response = client.chat.completions.create(
        model='gpt-4o',
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": new_url_text
            }
        ]
    )
    # Print the response content for debugging
    response_content = response.choices[0].message.content


    # Attempt to parse the response content as JSON
    try:
        new_image_name = json.loads(response_content)['answer']

        if 'https://centrala.ag3nts.org/dane/barbara/' not in new_image_name:
            print(f"I isolate an URL: https://centrala.ag3nts.org/dane/barbara/{new_image_name}")
            return f"https://centrala.ag3nts.org/dane/barbara/{new_image_name}"
        else:
            print(f"I isolate an URL: {new_image_name}")
            return new_image_name
        
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")

        return {"error": "Failed to decode JSON"}

def describe_photo(client, url):
    print(f'I analize an URL: {url}')
    system_prompt = """
    Your goal is to return a json structure describing the woman in the photo sent by the user in polish.
    If the photo is clear and there is a woman in the photo, your answer must be:
    {
        "description": "Detailed description of the woman in the photo, focus on the woman, ignore details like the background. Description must be in polish"
    }

    If the photo is clear but there is no woman in the photo, your answer must be exactly like this:
    {
        "description": "No woman on the photo"
    }

    If the photo is damaged, select one of the three options for how to modify the photo: REPAIR or BRIGHTEN or DARKEN, and then return the response:

    {
        "fix": "REPAIR/BRIGHTEN/DARKEN"
    }

    Rules:
    - Do not wrap the json codes in JSON markers
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": url,
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    # Attempt to parse the response content as JSON
    try:
        answer = json.loads(response.choices[0].message.content)

        # Check if photo needs to be repaired
        if 'fix' in answer:
            new_url = repair_photo(client, url, answer['fix'].upper())
            return describe_photo(client, new_url)
        
        elif 'description' in answer:
            return answer['description']
        
        else:
            raise ValueError("Unexpected response format from the AI model")
        
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")

def final_description(client, connected_descriptions):
    system_prompt = """
You will get different descriptions of a woman in polish. Your goal is to create an detailed summary of these descriptions, focus on the woman not the background. Your answer must be only the text describing the woman and it must be in polish.
"""

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": connected_descriptions
            }
        ]
    )

    return completion.choices[0].message.content


client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

# Get the list of photos to analyze
photos_list = get_photos_list(client)

# Add each description to a list
descriptions = []
for url in photos_list:
    new_desc = describe_photo(client, url)

    print('Description: ')
    print(new_desc)

    descriptions.append(new_desc)
    print("====================")

connected_descriptions = ""
i = 1
for el in descriptions:
    connected_descriptions += f"Description {i}: {el} \n \n"

    i += 1
 
print(connected_descriptions)

answer = final_description(client, connected_descriptions)
print(f"Final description: {answer}")
print(server_response(answer))
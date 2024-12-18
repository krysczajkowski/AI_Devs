import requests
import os 
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

url = f"https://centrala.ag3nts.org/data/{os.getenv('API_KEY')}/robotid.json"

try:
    # Fetch robot description
    response = requests.get(url)
    robot_description = response.json()['description']

    # Generate robot description prompt
    generate_image_system_prompt = """
    Dostaniesz opis robota. Twoim zadaniem jest stworzyć prompt do AI, który na podstawie opisu wygeneruje obraz robota. Użyj tylko słów kluczowych dotyczących wyglądu, cech, i otoczenia robota
    """

    client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": generate_image_system_prompt},
            {
                "role": "user",
                "content": robot_description
            }
        ]
    )
    robot_prompt = completion.choices[0].message.content

    print(robot_description)
    print(robot_prompt)

    # Generate an image
    response = client.images.generate(
        model="dall-e-3",
        prompt = robot_prompt,
        n=1,
        size="1024x1024",
        style='natural'
    )
    robot_url = response.data[0].url

    # Send the results to the server
    server_msg = {
        "task": "robotid",
        "apikey": os.getenv('API_KEY'),
        "answer": robot_url
    }

    response = requests.post(
        url = "https://centrala.ag3nts.org/report",
        json = server_msg,
        headers = {
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

except:
    print("Error fetching data")



from openai import OpenAI
import os
from dotenv import load_dotenv
import base64

# Load environment variables from .env file
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

# Function to analyze an image using GPT-4 Vision
def analyze_image(image_path):
    system_prompt = """
    <goal>
    You will be given several pictures with parts of cities. Your goal is to analyze these pictures carefully and determine which city they most likely represent
    </goal>

    <rules>
    - Analyze the pictures based on the names of streets, parks, and other objects. Pay attention to the arrangement of these objects in relation to each other
    - Not all the pictures have to come from the same city. Your goal is to identify where most of the pictures come from
    </rules>

    <thinking>
    Present your reasoning precisely why you choose each city. For each picture, answer the questions
    1. In which cities are there such streets and objects as in the picture
    2. In which cities are these streets arranged in relation to each other as in the picture
    Then choose one common city for all the pictures
    </thinking>
    """
    images_prompt = []

    # Create a images_prompt list with encoded images from mapy/ folder 
    folder_path = "./mapy"
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.png'):
            image_path = os.path.join(folder_path, filename)

            with open(image_path, "rb") as image_file:
                images_prompt.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64.b64encode(image_file.read()).decode('utf-8')}"
                            }
                        }
                    ]
            })

    try:
        # Create the message with the image
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt}, *images_prompt
            ],
            max_tokens=300
        )
    
        # Return the analysis
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing image: {str(e)}"


image_path = "./mapy/mapa1.png"
analysis = analyze_image(image_path)
print(analysis)

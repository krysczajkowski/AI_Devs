import whisper
from openai import OpenAI
from dotenv import load_dotenv
import os
import requests

load_dotenv()

def create_transcriptions():
    # Initialize Whisper model
    model = whisper.load_model("base")
    
    # Define input and output paths
    input_path = "/Users/a1/Desktop/PROJEKTY_MOJE/ai_devs/materialy_dodatkowe/przesluchania/"
    output_path = os.path.join(os.getcwd(), "transkrypcje/")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # Get all .m4a files from input directory
    audio_files = [f for f in os.listdir(input_path) if f.endswith('.m4a')]
    
    # Process each audio file
    for audio_file in audio_files:
        # Get full input path
        input_file = os.path.join(input_path, audio_file)
        
        # Create output filename (same name but .txt extension)
        output_file = os.path.join(output_path, audio_file.replace('.m4a', '.txt'))
        
        print(f"Transcribing {audio_file}...")
        
        # Generate transcription
        result = model.transcribe(input_file, fp16=False)
        
        # Save transcription to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result["text"])
        
        print(f"Saved transcription to {output_file}")

system_prompt = """
Hej, twoim celem jest przeanalizowanie wypowiedzi świadków i znalezienie odpowiedzi na pytanie, na jakiej ulicy znajduje się uczelnia, na której wykłada profesor Andrzej Maj.

Pamiętaj, że:

Zeznania mogą się wzajemnie wykluczać lub uzupełniać.
Rafał jest najpewniejszym źródłem informacji.

### Twój proces myślowy tutaj###
1. Ustal o jakich miastach i uczelniach mowa jest w transkrypcjach
2. Wywnioskuj na podstawie informacji na temat prof. Maja na jakim instytucie moze on wykładać
3. Wywnioskuj na jakiej ulicy moze znajdować sie konkretny instytut na którym wykłada profesor Maj. Jezeli nie ma takiej informacji w tekście, to uzyj swojej bazy wiedzy, zeby sprawdzić przy jakiej ulicy znajduje się KONKRETNY INSTYTUT (nie ogólnie uczelnia). 
"""


def analyze_data():
    # Get all transcription files from the transkrypcje directory
    transcription_path = os.path.join(os.getcwd(), "transkrypcje/")
    transcription_files = [f for f in os.listdir(transcription_path) if f.endswith('.txt')]
    
    user_messages = []
    
    # Read content of each transcription file
    for transcript_file in transcription_files:
        file_path = os.path.join(transcription_path, transcript_file)
        with open(file_path, 'r', encoding='utf-8') as f:
            user_messages.append({
                "role": "user",
                "content": f.read()
            })

    # Create completion with the model
    client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt}, *user_messages
        ],
        temperature=0
    )
    
    return completion.choices[0].message.content


def send_testimonies(testimonies):
    server_msg = {
        "task": "mp3",
        "apikey": os.getenv('API_KEY'),
        "answer": testimonies
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


# Get user choice
choice = input("What would you like to do?\n1 - Create transcriptions\n2 - Analyze data and show conclusions\nYour choice: ")

if choice == "1":
    create_transcriptions()
elif choice == "2":
    testimonies = analyze_data()
    print(testimonies)
    print('----------')
    send_testimonies(testimonies)

else:
    print("Invalid choice")

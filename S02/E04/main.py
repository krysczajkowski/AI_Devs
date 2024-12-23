import anthropic
import os 
import dotenv
from pathlib import Path
from functions import *
from openai import OpenAI
import json
import requests

dotenv.load_dotenv()

def analyze_files():
    client_anthropic = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_KEY"))
    client_openai = OpenAI(api_key=os.getenv("OPENAI_KEY"))

    files = []
    people = []
    hardware = []
    folder_path = Path("/Users/a1/Desktop/PROJEKTY_MOJE/ai_devs/materialy_dodatkowe/pliki_z_fabryki")

    # Get a list of files to be analyzed
    for file_path in folder_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.png', '.mp3']:
            files.append(file_path.name)

    # Get a list of files
    for filename in files:
        print(f"\nAnalyzing: {filename}")
        try:
            result = {"important": False, "tag": ""}
            # Analyze .txt files
            if filename.endswith('.txt'):
                file_path = f'{folder_path}/{filename}'
                result = analyze_txt(client_anthropic, file_path)

            # Analyze .png files
            if filename.endswith('.png'):
                image_path = f'{folder_path}/{filename}'
                result = analyze_png(client_anthropic, image_path)

            # Analyze .mp3 files 
            if filename.endswith('.mp3'):
                audio_path = f"{folder_path}/{filename}"
                result = analyze_mp3(client_openai, audio_path)

            # Decide if file is important
            if result['important'] == True:
                if result['tag'] == 'people':
                    people.append(filename)

                elif result['tag'] == 'hardware':
                    hardware.append(filename)

        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            continue  # Przejdź do następnego pliku zamiast przerywać całą pętlę

    answer_data = {
        "people": people,
        "hardware": hardware
    }
    json_structure = json.dumps(answer_data, indent=2)

    # Save answer to the file 
    with open("answer.json", "w") as file:
        file.write(json_structure)

def send_answer():
    try:
        # Reading JSON from the file
        with open("answer.json", "r") as file:
            data = json.load(file)

            # Send the results to the server
            server_msg = {
                "task": "kategorie",
                "apikey": os.getenv('API_KEY'),
                "answer": data
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

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    

print("Choose your option:")
print("1 - analyze the files and save the analysis to .json file")
print("2 - send json file to the server")
option = input("Your option: ")

if option == "1":
    analyze_files()
elif option == "2":
    send_answer()
else:
    print("Quit program")
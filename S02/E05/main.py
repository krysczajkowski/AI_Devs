import requests
from dotenv import load_dotenv
import os
from firecrawl import FirecrawlApp
from bs4 import BeautifulSoup
from openai import OpenAI
import mimetypes
import html2text
import json
import concurrent.futures

load_dotenv()

def image_description(client, image_url, description):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "developer", "content": "Napisz kilku zdaniowy opis obrazka. Zrób to na podstawie obrazka oraz jego krótkiego opisu dostarczonego przez użytkownika. W długim opisie powinny znaleźć się informacje zawarte w krótkim opisie oraz dodatkowe informacje, które mogą być przydatne dla użytkownika. Opis powinien być zwięzły, ale jednocześnie zawierać wszystkie istotne informacje."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Krótki opis obrazka: {description}"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                        }
                    },
                ],
            }
        ],
    )

    return completion.choices[0].message.content

def audio2text(client, audio_url):
    # Download audio file
    response = requests.get(audio_url)

    if response.status_code == 200:
        audio_file = response.content
        audio_format = mimetypes.guess_extension(response.headers['Content-Type'])

        # Save the audio file temporarily
        temp_audio_path = f"temp_audio{audio_format}"
        with open(temp_audio_path, 'wb') as f:
            f.write(audio_file)

        # Audio file transcription
        with open(temp_audio_path, 'rb') as f:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
            )

        # Remove the temporary file
        os.remove(temp_audio_path)

        return transcription.text

    else:
        print(f"Failed to download audio file. Status code: {response.status_code}")
        return "Brak transkrypcji. Format pliku audio nie jest obsługiwany."

# (Single) Image description generator
def process_single_image(domain, item):
    key, short_desc = item
    if short_desc:
        return (key, image_description(client, f"{domain}{key}", short_desc))
    else:
        return (key, image_description(client, f"{domain}{key}", "No description"))

def generate_markdown_context(client):
    # Get website's html code
    url = 'https://centrala.ag3nts.org/dane/arxiv-draft.html'
    domain = "https://centrala.ag3nts.org/dane/"

    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')


    """ IMAGES -> TEXT """
    # Create a dictionary with all the images and their default descriptions
    images = {}
    for img in soup.find_all('img'):
        if 'src' in img.attrs:
            # Find <figure> - img's parent
            figure = img.find_parent('figure')
            if figure:
                # Find <figcaption> inside <figure>
                caption = figure.find('figcaption')
                if caption:
                    images[img['src']] = caption.get_text(strip=True)
                else:
                    images[img['src']] = None  # No <figcaption>
            else:
                images[img['src']] = None  # No <figure>

    # Create 5 concurrent threads to process images
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Attach tasks to threads 
        future_to_image = {} # Store result of process_single_image function and image key
        for key, value in images.items():
            # Future - result of process_single_image function or status of its execution
            future = executor.submit(process_single_image, domain, (key, value))
            future_to_image[future] = key

        # Get results  
        for future in concurrent.futures.as_completed(future_to_image):
            key = future_to_image[future]
            try:
                # future.result() zwraca krotkę (key, opis_obrazka)
                key_from_future, desc = future.result()
                images[key_from_future] = desc
            except Exception as e:
                print(f"Error generating an image description {key}: {e}")
                images[key] = "Błąd w generowaniu opisu"

    # Find all images and replace them with their descriptions
    for img in soup.find_all("img"):
        if "src" in img.attrs:
            img_url = img["src"]
            if img_url in images:
                # Stwórz tag tekstowy z opisem
                description = soup.new_tag("span")
                description.string = f"W tym miejscu znajduje się obrazek. To jego słowny opis: {images[img_url]}"
                # Zastąp obrazek opisem
                img.replace_with(description)


    """ AUDIO -> TEXT """
    # Capture all audio urls 
    audios = {}
    for audio in soup.find_all('source'):
        if 'src' in audio.attrs:
            audios[audio['src']] = None

    # Use AI to transform audio to text
    for key, value in audios.items():
        audios[key] = audio2text(client, f"{domain}{key}")

    # Find all audio tags and replace them with their transcriptions
    for audio in soup.find_all("source"):
        if "src" in audio.attrs:
            audio_url = audio["src"]
            if audio_url in audios:
                # Stwórz tag tekstowy z opisem
                transcription = soup.new_tag("span")
                transcription.string = f"W tym miejscu znajduje się plik audio. To jego transkrypcja: {audios[audio_url]}"
                # Zastąp obrazek opisem
                audio.replace_with(transcription)


    """ Safe the modified html code """
    modified_html = soup.prettify()

    # HTML -> Markdown
    converter = html2text.HTML2Text()
    converter.ignore_links = False  
    converter.ignore_images = True 

    markdown = converter.handle(modified_html)

    # Safe it to a file
    with open("website.md", "w") as file:
        file.write(markdown)

def get_answer(client, question, context):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Odpowiedz na pytanie na podstawie podanego kontekstu. Uważnie przeanalizuj kontekst i odpowiedz tylko na jego podstawie. Odpowiedź powinna być zwięzła, ale jednocześnie zawierać wszystkie istotne informacje."},
            {
                "role": "user",
                "content": f"Pytanie: {question} \n\n Kontekst: {context}"
            }
        ]
    )

    return completion.choices[0].message.content

def answer_questions(client):
    # Get the questions
    response = requests.get(f"https://centrala.ag3nts.org/data/{os.getenv("API_KEY")}/arxiv.txt")
    response.encoding = 'utf-8'

    # Get a list of questions
    questions = []
    for question in response.text.splitlines():
        questions.append(question[3:])

    # Download and load website.md
    with open("website.md", "r") as file:
        context = file.read()

    # Get the answers
    answers = {}
    for i, question in enumerate(questions, start=1):
        answers[f"0{i}"] = get_answer(client, question, context)

    # Send data to the server
    server_msg = {
        "task": "arxiv",
        "apikey": os.getenv("API_KEY"),
        "answer": answers
    }

    response = requests.post(
        url = "https://centrala.ag3nts.org/report",
        json=server_msg,
        headers = { "Content-Type": "application/json" }
    )

    # Check if request was successful
    if response.status_code == 200:
        result = response.json()  # Parse response JSON
        print(result)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# Choose the option
print("1 - Prepare the website so it's readable for the AI")
print("2 - Answer questions and send them to the server")
option = input("Choose: ")
client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

if option == "1":
    generate_markdown_context(client)

elif option == "2":
    answer_questions(client)

else:
    print('Quit program')

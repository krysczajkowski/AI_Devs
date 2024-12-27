from pathlib import Path
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import requests
import concurrent.futures

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

# Function that generates keyword for a given file
def generate_keywords(path, file_name):
    file_path = Path(path) / file_name
    file_content = file_path.read_text()

    system_prompt = """
    Wygeneruj słowa kluczowe na podstawie tekstu w formie mianownika (czyli np. “sportowiec”, a nie “sportowcem”, “sportowców” itp.). 
    Do not wrap the json codes in JSON markers
    Słowa kluczowe przez ciebie wygenerowane będą następnie użyte do lokalizowania odpowiednich dokumentów przez AI.
    Wyciągnij słowa kluczowe z nazwy, takie jak raport i jego numer oraz sektor. Przykład: ["raport 08", "sektor C4"].
    Słowa kluczowe muszą być napisane poprawną polszczyzną oraz nie powinny się powtarzać.
    Słowa kluczowe powinny być jako lista w formacie json, przykład:
    {
        "keywords": ["sportowiec", "trening", "zdrowie"]
    }
    """
    if file_content.strip() == "entry deleted":
        return []
    
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Nazwa pliku: {file_name}\n Plik:{file_content}"}
        ]
    )

    response_content = completion.choices[0].message.content
    print(f"Response content: {response_content}")  # Debugging line

    try:
        answer = json.loads(response_content)
        return answer.get("keywords", [])
    except json.JSONDecodeError:
        print("Failed to decode JSON response")
        return []

# Function that finds a person in a given keywords list
def find_person_in_raport(raport_keywords):
    system_prompt = """
    Znajdź osoby w raporcie na podstawie słów kluczowych. Jeśli znajdziesz osobę, to zwróć jej imię i nazwisko.
    Wyciągnij osobę z listy słów kluczowych. Przykład: ["Jan Kowalski"].
    Do not wrap the json codes in JSON markers
    Osoba musi być napisana poprawną polszczyzną oraz nie powinna się powtarzać.
    Osoba powinna być jako lista w formacie json, przykład:
    {
        "persons": ["Jan Kowalski", "Adam Nowak"]
    }
    """
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Słowa kluczowe: {raport_keywords}"}
        ]
    )
    # return completion.choices[0].message.content
    answer = json.loads(completion.choices[0].message.content)
    return answer['persons']

if __name__ == "__main__":
    raports = {}
    facts = {}
    raports_path = Path("/Users/a1/Desktop/PROJEKTY_MOJE/ai_devs/materialy_dodatkowe/pliki_z_fabryki")
    facts_path = Path("/Users/a1/Desktop/PROJEKTY_MOJE/ai_devs/materialy_dodatkowe/pliki_z_fabryki/facts")

    # Create 5 concurrent processes for generating keywords for facts
    with concurrent.futures.ProcessPoolExecutor(max_workers=5) as executor:
        future_to_fact = {}
        # Assign futures to facts
        for fact_path in facts_path.iterdir():
            if fact_path.is_file() and fact_path.suffix.lower() == '.txt':
                future = executor.submit(generate_keywords, facts_path, fact_path.name)
                future_to_fact[future] = fact_path.name

        # Collect results
        for future in concurrent.futures.as_completed(future_to_fact):
            fact = future_to_fact[future]

            try:
                facts[fact] = future.result()
            except Exception as e:
                print(f"An error occurred: {e}")

    # Create 5 concurrent processes for generating keywords for raports
    with concurrent.futures.ProcessPoolExecutor(max_workers=5) as executor:
        future_to_raport = {}
        # Asign futures to raports
        for raport_path in raports_path.iterdir():
            if raport_path.is_file() and raport_path.suffix.lower() == '.txt':
                future = executor.submit(generate_keywords, raports_path, raport_path.name)
                future_to_raport[future] = raport_path.name

        # Collect results
        for future in concurrent.futures.as_completed(future_to_raport):
            try:
                raport = future_to_raport[future]
                raports[raport] = future.result()

            except Exception as e:
                print(f"An error occurred: {e}")

    # Generate keywords for each raport 
    for raport_path in raports_path.iterdir():
        if raport_path.is_file() and raport_path.suffix.lower() == '.txt':
            raports[raport_path.name] = generate_keywords(raports_path, raport_path.name)

    # Update raports keywords based on facts
    for raport, keywords in raports.items():
        persons = find_person_in_raport(keywords)
        for person in persons:
            for fact, fact_keywords in facts.items():
                if person in fact_keywords:
                    raports[raport] = list(set(keywords + fact_keywords))
                    

    # Convert lists to comma-separated strings
    for key, value in raports.items():
        raports[key] = ", ".join(value)

    print("--- Final raport's keywords ---")
    for key, value in raports.items():
        print(f"Raport: {key}, Keywords: {value}")

    # Send it to the server
    server_msg = {
        "task": "dokumenty",
        "apikey": os.getenv("API_KEY"),
        "answer": raports
    }

    response = requests.post(
        url = "https://centrala.ag3nts.org/report",
        json = server_msg,
        headers = {
            "Content-Type": "application/json"
        }
    )

    if response.status_code == 200:
        result = response.json()
        print(result)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

import requests
import json
import os 
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI

apikey = os.getenv("API_KEY")
client = OpenAI(api_key = os.getenv("OPENAI_KEY"))

PROMPT = """
Twoim celem jest odpowiedź na pytanie: “które aktywne datacenter (DC_ID) są zarządzane przez pracowników, którzy są na urlopie (is_active=0)”. Pracujesz na bazie MySQL. Możesz podawać zapytania do bazy danych, które zostaną wysłane do API, a ich wynik zostanie Ci zaprezentowany.

- **Jeśli musisz zadać pytanie do bazy danych, zwróć wynik w następującej strukturze:**
{
    "type": "question",
    "value": "Wygenerowane zapytanie SQL"
}

- **Jeśli masz już odpowiedź z bazy danych, zwróć wynik w następującej strukturze:**
{
    "type": "answer",
    "value": "Lista DC_ID oddzielonych przecinkiem"
}

- Odpowiedź musi być dokładnie w podanym formacie. 
- Twoje zapytanie absolutnie nie może być w tagach SQL takich jak ```sql. Nie dodawaj komentarzy, wyjaśnień czy jakiegokolwiek tekstu.

Przydatne polecenia:
- `SHOW TABLES` = zwraca listę tabel
- `SHOW CREATE TABLE NAZWA_TABELI` = pokazuje, jak zbudowana jest konkretna tabela

Podaj mi zapytanie do uruchomienia lub odpowiedź w odpowiednim formacie.
Do tej pory zrobiłeś:
"""

def ask_server(apikey, query):
    data = {
        "task": "database",
        "apikey": apikey,
        "query": query
    }
    data_json = json.dumps(data)
    r = requests.get("https://centrala.ag3nts.org/apidb", data=data_json)

    response_json = r.json()
    return json.dumps(response_json['reply'], indent=4)

def send_answer(apikey, answer):
    server_msg = {
        "task": "database",
        "apikey": apikey,
        "answer": answer
    }
    response = requests.post(
        url = "https://centrala.ag3nts.org/report",
        json = server_msg,
        headers = {
            "Content-type": "application/json"
        }
    )

    return response.json()

while True:
    print(PROMPT)
    print('--------------')

    # Wysyłam zapytanie do chata
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": PROMPT
            }
        ]
    )

    chat_reponse = json.loads(completion.choices[0].message.content)

    if chat_reponse['type'] == 'question':
        # Wysyłam jego pytanie do serwera
        server_reponse = ask_server(apikey, chat_reponse['value'])

        # Aktualizuje wiedze LLM
        PROMPT += f"""
        AI: {chat_reponse['value']}
        Answer: {server_reponse}     
        """

    elif chat_reponse['type'] == 'answer':
        # Wysyłam odpowiedź do servera
        print(f"Lista DC_ID: {chat_reponse['value']}")

        answer = chat_reponse['value'].split(',')
        print(send_answer(apikey, answer))

        break
    else:
        print("Błąd odpowiedzi czata")
        break

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os 
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

""" Structure outputs """
class Coordinates(BaseModel):
    y: int
    x: int

class Element(BaseModel):
    id: int
    value: str

class Row(BaseModel):
    id: int
    element: list[Element]

def generate_map(request):
    pass

""" View functions """
@csrf_exempt  # wyłączam mechanizm CSRF, żeby można było testowo strzelać POST-ami z zewnątrz
def webhook(request):

    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)

        instruction = data.get("instruction", "")

        client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

        completion = client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Bazując na instrukcji podanej przez uzytkownika, wygeneruj dwie liczby które będą koordynatami. Koordynaty początkowe to y=0 i x=0. Koordynaty maksymalne to y=3 oraz x=3. Jezeli instrukcja od uzytkownika wykracza poza te liczby, to zatrzymaj liczenie i przypisz do koordynatów maksymalną wartość. "},
                {"role": "system", "content": instruction}
            ],
            response_format=Coordinates
        )
        x = completion.choices[0].message.parsed.x
        y = completion.choices[0].message.parsed.y

        MAPA = [
            ["start", "pole",    "drzewo",   "dom"       ],
            ["pole",  "wiatrak", "pole",     "pole"      ],
            ["pole",  "pole",    "kamienie", "dwa drzewa"],
            ["góry",  "góry",    "samochód", "jaskinia"  ]
        ]

        return JsonResponse({
            "description": MAPA[y][x]
        })
    
    elif request.method == 'GET':
        return JsonResponse({"message": "API jest dostępne"})
    else:
        return JsonResponse({"error": "Metoda niedozwolona"}, status=405)
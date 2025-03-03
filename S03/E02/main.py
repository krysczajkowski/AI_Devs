import os 
from qdrant_client import models, QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv
import json
import requests
from pathlib import Path
from pydantic import BaseModel

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

# Structured outputs
class Keywords(BaseModel):
    keywords: list[str]

# Get keywords from a given text 
def get_keywords(text):
    system_prompt = """
    Wygeneruj słowa kluczowe na podstawie tekstu w formie mianownika (czyli np. “sportowiec”, a nie “sportowcem”, “sportowców” itp.). 
    Uwzględnij nazwy własne, technologie, języki programowania, daty, pojęcia techniczne, wydarzenia, miejsca, osoby.
    Wyciągnij słowa kluczowe z nazwy, takie jak raport i jego numer oraz sektor. Przykład: ["raport 08", "sektor C4"].
    Słowa kluczowe muszą być napisane poprawną polszczyzną oraz nie powinny się powtarzać.
    Wygenerowane słowa kluczowe będą używane do lokalizowania odpowiednich dokumentów przez AI.
    """
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        response_format=Keywords,
    )

    return completion.choices[0].message.parsed.keywords

# Function that combines description and keywords into one string
def combine_text(doc):
    description = doc.get("description", "")
    keywords = doc.get("keywords", [])
    combined_text = description + " " + " ".join(keywords)
    return combined_text

# Initialize database and embedding model
qdrant = QdrantClient(":memory:")
encoder = SentenceTransformer("distiluse-base-multilingual-cased-v2")

# Iterate through files and create documents 
documents = []
folder = Path("/Users/a1/Desktop/projekty_moje/ai_devs/materialy_dodatkowe/pliki_z_fabryki/do-not-share")
for file in folder.glob("*.txt"):
    with file.open("r", encoding="utf-8") as f:
        file_content = f.read()
        temp = dict()
        temp['name'] = file.name
        temp['content'] = file_content
        temp['keywords'] = get_keywords(f"{file.name} \n{file_content}")

        documents.append(temp)

for element in documents:
    print(f"Name: {element['name']} \nContent: {element['content']} \n Keywords: {element['keywords']}")


qdrant.create_collection(
    collection_name="S3E2",
    vectors_config=models.VectorParams(
        size=encoder.get_sentence_embedding_dimension(),  # Vector size is defined by used model
        distance=models.Distance.COSINE,
    ),
)

qdrant.upload_points(
    collection_name="S3E2",
    points=[
        models.PointStruct(
            id=idx, vector=encoder.encode(combine_text(doc)).tolist(), payload=doc
        )
        for idx, doc in enumerate(documents)
    ],
)

hits = qdrant.query_points(
    collection_name="S3E2",
    query=encoder.encode("W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?").tolist(),
    limit=1,
).points

# for hit in hits:
#     print(hit.payload, "score:", hit.score)

answer = hits[0].payload['name'][:-4].replace("_", "-")
print(f"Answer is: {answer}")

server_msg = {
    "task": "wektory",
    "apikey": os.getenv("API_KEY"),
    "answer": answer
}

response = requests.post(
    url = "https://centrala.ag3nts.org/report",
    json = server_msg,
    headers = {
        "Content-type": "application/json"
    }
)

print(response.json())
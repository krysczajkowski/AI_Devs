""" Transform lab data from .txt into .jsonl """
import json

with open("lab_data/correct.txt", "r") as correct_txt, open("lab_data/incorrect.txt", "r") as incorrect_txt, open("lab_data/result.jsonl", "w") as file_jsonl:
    for line in correct_txt:
        data = line.strip()
        structure = {
            "messages": [
                {"role": "system", "content": "Classify data"},
                {"role": "user", "content": data},
                {"role": "assistant", "content": "correct"}
            ]
        }
        file_jsonl.write(json.dumps(structure) + "\n")  # Konwersja na JSON + nowa linia

    for line in incorrect_txt:
            data = line.strip()
            structure = {
                "messages": [
                    {"role": "system", "content": "Classify data"},
                    {"role": "user", "content": data},
                    {"role": "assistant", "content": "incorrect"}
                ]
            }
            file_jsonl.write(json.dumps(structure) + "\n")  # Konwersja na JSON + nowa linia

    

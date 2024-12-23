import json5
import base64

# System prompts
system_txt = """
Analyze the text below and respond with a JSON structure as described:
{
  "reasoning": [step-by-step thought process as text],
  "answer": {
    "important": true/false,
    "tag": "people" / "hardware" / ""
  }
}

reasoning: Explain your thought process step by step to justify your decision.
answer:
important:
true if the text explicitly mentions captured people (e.g., individuals detained, restrained, or held) or traces of their presence (e.g., evidence like footprints, belongings).
Also true if the text discusses repaired hardware issues (software-related issues should be excluded).
false if none of the above conditions are met.
tag:
"people" if important is true and the text discusses captured people or traces of their presence.
"hardware" if important is true and the text mentions repaired hardware issues.
Empty ("") if important is false.
Note: General mentions of people without explicit context of being captured or evidence of their presence do not qualify as "important": true.
"""

system_png = """
Analyze the text on the picture and respond with a JSON structure as described:
{
  "reasoning": [step-by-step thought process as text],
  "answer": {
    "important": true/false,
    "tag": "people" / "hardware" / ""
  }
}

reasoning: Explain your thought process step by step to justify your decision.
answer:
important: true if the text mentions captured people or traces of their presence, or repaired hardware issues (exclude software). Otherwise, false.
tag:
"people" if important is true and the text discusses captured people or traces of their presence.
"hardware" if important is true and the text mentions repaired hardware issues.
Empty ("") if important is false.
"""

def analyze_txt(client, file_path):
    # Read the file content
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
            
        # Send to Claude API
        result = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0,
            system=system_txt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": file_content
                        }
                    ]
                }
            ]
        )
        
        try:
            # Parse text
            response_text = result.content[0].text
            response_text = ' '.join(response_text.splitlines())

            response_dict = json5.loads(response_text)
        except Exception as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Problematic text: {result.content[0].text}")
            return {"important": False, "tag": ""}

        print("Reasoning: ")
        print(response_dict["reasoning"])
        print(response_dict['answer'])

        return response_dict["answer"]
        
    except FileNotFoundError:
        print(f"FileNotFound: {file_path}")
        return {"important": False, "tag": ""}  # Return dictionary instead of string
    except Exception as e:
        print(f"Error reading or analyzing file: {str(e)}")
        return {"important": False, "tag": ""}  # Return dictionary instead of string
    


def analyze_png(client, image_path):
    try:
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

        result = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_png,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        }
                    ],
                }
            ],
        )

        try:
            # Parse text
            response_text = result.content[0].text
            response_text = ' '.join(response_text.splitlines())

            response_dict = json5.loads(response_text)
        except Exception as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Problematic text: {result.content[0].text}")
            return {"important": False, "tag": ""}

        print("Reasoning: ")
        print(response_dict["reasoning"])
        print(response_dict['answer'])

        return response_dict["answer"]

    except FileNotFoundError:
        print(f"FileNotFound: {image_path}")
        return {"important": False, "tag": ""}  # Return dictionary instead of string
    except Exception as e:
        print(f"Error reading or analyzing file: {str(e)}")
        return {"important": False, "tag": ""}  # Return dictionary instead of string
    

def analyze_mp3(client, audio_path):
    try:
        # Create transcription
        audio_file = open(audio_path, "rb")
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )

        # Analyze the text
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "developer", "content": system_txt},
                {
                    "role": "user",
                    "content": transcription.text
                }
            ]
        )

        try:
            # Parse text
            response_text = result.choices[0].message.content
            response_text = ' '.join(response_text.splitlines())

            response_dict = json5.loads(response_text)
        except Exception as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Problematic text: {result.content[0].text}")
            return {"important": False, "tag": ""}
        
        print("Reasoning: ")
        print(response_dict["reasoning"])
        print(response_dict['answer'])

        return response_dict["answer"]
    
    except FileNotFoundError:
        print(f"FileNotFound: {audio_path}")
        return {"important": False, "tag": ""}  # Return dictionary instead of string
    except Exception as e:
        print(f"Error reading or analyzing file: {str(e)}")
        return {"important": False, "tag": ""}  # Return dictionary instead of string
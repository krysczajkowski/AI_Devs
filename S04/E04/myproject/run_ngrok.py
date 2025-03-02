# run_ngrok.py
import os
import threading
import time
from dotenv import load_dotenv
import ngrok

load_dotenv()

def start_ngrok():
    # Forwardujemy port 8000 (na którym będzie działał Django)
    listener = ngrok.forward(8000, authtoken=os.getenv("NGROK_KEY"))
    print(f"Ingress established at {listener.url()}")
    # Utrzymujemy tunel przy życiu
    while True:
        time.sleep(1)

if __name__ == "__main__":
    ngrok_thread = threading.Thread(target=start_ngrok, daemon=True)
    ngrok_thread.start()
    # Uruchomienie Django na porcie 8000
    os.system("python manage.py runserver 0.0.0.0:8000")

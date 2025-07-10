import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')
if not API_KEY:
    print("Erro: GOOGLE_GEMINI_API_KEY não configurada no arquivo .env")
    exit(1)

url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}"

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Modelos disponíveis:")
        print(response.json())
    else:
        print("Erro na requisição:", response.text)
except Exception as e:
    print(f"Erro ao conectar com a API: {e}")
# Valida o acesso à API pública do USGS antes da Aula 2.
import requests

API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/count"

# Janela e magnitude mínima do teste proposto na Aula 1.
params = {
    "format": "geojson",
    "starttime": "2025-07-01",
    "endtime": "2025-08-01",
    "minmagnitude": 2.5,
}

response = requests.get(API_URL, params=params, timeout=30)
response.raise_for_status()
print(f"HTTP {response.status_code}")
print("Resposta do USGS:", response.json())

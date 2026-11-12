# =============================================================================
# NOTEBOOK: 00_validate_usgs_api.py
# OBJETIVO: Teste de conectividade com a API pública do USGS (FDSN event query),
#           executado na Aula 1. Confirma que o Databricks Free Edition tem
#           acesso de rede à API antes das ingestões da Aula 2.
# =============================================================================

import requests
from datetime import datetime, timedelta, timezone

API_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# Janela de teste: últimas 24 horas, magnitude >= 2.5
_data_fim = datetime.now(timezone.utc).date()
_data_inicio = _data_fim - timedelta(days=1)

params = {
    "format": "geojson",
    "starttime": _data_inicio.isoformat(),
    "endtime": _data_fim.isoformat(),
    "minmagnitude": 2.5,
    "limit": 1,
}

try:
    resp = requests.get(API_URL, params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    total = payload.get("metadata", {}).get("count", 0)
    print(f"OK - conectividade confirmada (HTTP {resp.status_code})")
    print(f"Eventos de magnitude >= 2.5 nas últimas 24h: {total}")
    print(f"Endpoint validado: {resp.url}")
except requests.RequestException as e:
    raise SystemExit(f"FALHA - não foi possível acessar a API do USGS: {e}")

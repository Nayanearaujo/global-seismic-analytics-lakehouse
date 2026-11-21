# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Extração dos catálogos sísmicos
# MAGIC Aula 2 · USGS e EMSC → Landing
# MAGIC O recorte do desafio é 2025, com magnitude mínima de 2,5. Rode para uma fonte por vez.
# MAGIC
# MAGIC ## 1. Configurar as fontes
# MAGIC A configuração define a URL, o formato e a pasta de destino de cada catálogo.

# COMMAND ----------

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

SOURCES = {
    "usgs": ("https://earthquake.usgs.gov/fdsnws/event/1", "terremotos", "geojson"),
    "emsc": ("https://www.seismicportal.eu/fdsnws/event/1", "emsc", "json"),
}
LANDING = Path("/Volumes/sismos/bronze/landing")
MIN_MAGNITUDE = 2.5

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Definir a janela mensal em UTC
# MAGIC Cada mês vai do primeiro instante até o último milissegundo. Isso mantém as viradas de mês sem sobreposição.

# COMMAND ----------

def month_filters(year, month):
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    # O USGS inclui os dois limites e representa eventos em milissegundos.
    end = next_month - timedelta(milliseconds=1)
    return {
        "starttime": start.isoformat(timespec="milliseconds"),
        "endtime": end.isoformat(timespec="milliseconds"),
        "minmagnitude": MIN_MAGNITUDE,
        "orderby": "time-asc",
    }

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Conferir a resposta com a API
# MAGIC A consulta a `/count` usa o mesmo filtro que `/query`. A quantidade de eventos recebidos precisa bater antes da gravação.

# COMMAND ----------

def fetch_month(session, source, year, month):
    api, _, response_format = SOURCES[source]
    params = {**month_filters(year, month), "format": response_format}
    count_response = session.get(f"{api}/count", params=params, timeout=60)
    count_response.raise_for_status()
    count = count_response.json()
    expected = count["count"]
    maximum = count.get("maxAllowed")
    if maximum is not None and expected > maximum:
        raise ValueError(f"{expected} eventos excedem o limite de {maximum} por consulta")

    response = session.get(
        f"{api}/query",
        params=params,
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if (
        payload.get("type") != "FeatureCollection"
        or not isinstance(payload.get("features"), list)
        or len(payload["features"]) != expected
        or payload.get("metadata", {}).get("count", expected) != expected
    ):
        raise ValueError(f"GeoJSON inconsistente com os {expected} eventos do /count")
    return response.content, expected

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Salvar os arquivos mensais na Landing
# MAGIC Cada fonte tem sua pasta. O notebook registra os meses que falharem e sinaliza extração incompleta.

# COMMAND ----------

def extract_year(source, year):
    _, folder, _ = SOURCES[source]
    failures = []
    with requests.Session() as session:
        for month in range(1, 13):
            period = f"{year}-{month:02d}"
            path = LANDING / folder / f"ano={year}" / f"mes={month:02d}.geojson"
            try:
                body, expected = fetch_month(session, source, year, month)
                if path.exists():
                    if json.loads(path.read_bytes())["features"] != json.loads(body)["features"]:
                        raise ValueError(f"O arquivo histórico em {path} diverge da API")
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(body)
                print(f"{period}: {expected} eventos conferidos")
            except (requests.RequestException, OSError, ValueError, KeyError, TypeError) as error:
                failures.append(f"{period}: {error}")

    if failures:
        raise RuntimeError("Extração incompleta:\n" + "\n".join(failures))


# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Selecionar a fonte e o ano
# MAGIC Execute a célula de parâmetros e abra **Mostrar parâmetros**. Selecione `usgs` ou `emsc` e mantenha `2025` para o desafio.

# COMMAND ----------

if "dbutils" in globals():
    dbutils.widgets.dropdown("fonte", "usgs", list(SOURCES))
    dbutils.widgets.text("ano", "2025")


# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Executar a extração
# MAGIC Rode esta célula depois de escolher a fonte. Confira a saída de janeiro a dezembro antes de abrir o notebook 02.

# COMMAND ----------

if "dbutils" in globals():
    source = dbutils.widgets.get("fonte")
    year = int(dbutils.widgets.get("ano"))
    print(f"Fonte: {source.upper()} | Ano: {year}")
    extract_year(source, year)

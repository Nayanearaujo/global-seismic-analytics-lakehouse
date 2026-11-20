# Databricks notebook source
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

if "dbutils" in globals():
    dbutils.widgets.dropdown("fonte", "usgs", list(SOURCES))
    dbutils.widgets.text("ano", "2025")
    extract_year(dbutils.widgets.get("fonte"), int(dbutils.widgets.get("ano")))

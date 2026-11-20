# Databricks notebook source
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

API = "https://earthquake.usgs.gov/fdsnws/event/1"
LANDING = Path("/Volumes/sismos/bronze/landing/terremotos")
YEAR = 2025
MIN_MAGNITUDE = 1.0
MAX_EVENTS = 20_000


def month_filters(year, month):
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    # O USGS inclui os dois limites e representa eventos em milissegundos.
    end = next_month - timedelta(milliseconds=1)
    return {
        "starttime": start.isoformat(timespec="milliseconds"),
        "endtime": end.isoformat(timespec="milliseconds"),
        "minmagnitude": MIN_MAGNITUDE,
        "eventtype": "earthquake",
    }


def fetch_month(session, year, month):
    filters = month_filters(year, month)
    count_response = session.get(f"{API}/count", params=filters, timeout=60)
    count_response.raise_for_status()
    expected = int(count_response.text)
    if expected > MAX_EVENTS:
        raise ValueError(f"{expected} eventos excedem o limite por consulta do USGS")

    response = session.get(
        f"{API}/query",
        params={**filters, "format": "geojson"},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if (
        payload.get("type") != "FeatureCollection"
        or not isinstance(payload.get("features"), list)
        or len(payload["features"]) != expected
        or payload.get("metadata", {}).get("count") != expected
    ):
        raise ValueError(f"GeoJSON inconsistente com os {expected} eventos do /count")
    return payload


def extract_year(year):
    failures = []
    with requests.Session() as session:
        for month in range(1, 13):
            period = f"{year}-{month:02d}"
            path = LANDING / f"ano={year}" / f"mes={month:02d}" / f"earthquakes_{period}.geojson"
            try:
                payload = fetch_month(session, year, month)
                if path.exists():
                    saved = json.loads(path.read_bytes())
                    if (
                        saved.get("features") != payload["features"]
                        or saved.get("metadata", {}).get("count") != payload["metadata"]["count"]
                    ):
                        raise ValueError(f"O arquivo histórico em {path} diverge da API")
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                print(f"{period}: {len(payload['features'])} eventos conferidos")
            except (requests.RequestException, OSError, ValueError) as error:
                failures.append(f"{period}: {error}")

    if failures:
        raise RuntimeError("Extração incompleta:\n" + "\n".join(failures))


if __name__ == "__main__":
    extract_year(YEAR)

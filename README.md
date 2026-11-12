# 🌍 Global Seismic Analytics Lakehouse

Lakehouse de dados sísmicos globais no Databricks (Free Edition), a partir dos dados públicos do USGS Earthquake Hazards Program (API FDSN), com arquitetura medalhão (bronze/silver/gold) no Unity Catalog.

## Arquitetura medalhão

| Camada | Local | Conteúdo |
|--------|-------|----------|
| Landing | `/Volumes/sismos/bronze/landing/` | Arquivos `.geojson` brutos extraídos da API do USGS |
| Bronze | `sismos.bronze.terremotos_raw` | Eventos crus ingeridos incrementalmente pelo Auto Loader |
| Silver | `sismos.silver.*` | Eventos deduplicados, tipados e enriquecidos via MERGE |
| Gold | `sismos.gold.*` | Marts analíticos de risco sísmico |

## Notebooks da trilha

| Notebook | Etapa |
|----------|-------|
| `notebooks/00_setup_and_delta_fundamentals.sql` | Aula 1 — Setup do Unity Catalog + fundamentos Delta (ACID, Time Travel, RESTORE, Lineage) |
| `notebooks/00_validate_usgs_api.py` | Aula 1 — Teste de conectividade com a API do USGS |
| `notebooks/01_extract_usgs_landing.py` | Aula 2 — Extração dos `.geojson` brutos para o volume landing |
| `notebooks/02_bronze_autoloader.py` | Aula 2 — Ingestão incremental da bronze com Auto Loader |
| `notebooks/03_silver_merge_events.py` | Aula 3 — Deduplicação e MERGE na silver |
| `notebooks/04_gold_seismic_risk_marts.sql` | Aula 3/4 — Marts de risco sísmico na gold |

> `notebooks/exploratory/01_ingestao_sismos_usgs` mantém uma abordagem alternativa de ingestão (parse em memória + append direto em `workspace.sismos_bronze.eventos_usgs`), fora da trilha oficial.

## Development Roadmap

- [x] Setup do Unity Catalog: catálogo `sismos`, schemas bronze/silver/gold, volumes `landing` e `checkpoints`
- [x] Teste de conectividade com a API do USGS (rede liberada — 1.000 eventos retornados no primeiro teste)
- [ ] 01_extract_usgs_landing — extrair `.geojson` brutos para o landing (Aula 2)
- [ ] 02_bronze_autoloader — ingestão incremental com Auto Loader (Aula 2)
- [ ] 03_silver_merge_events — deduplicação e MERGE na silver (Aula 3)
- [ ] 04_gold_seismic_risk_marts — marts de risco sísmico na gold (Aula 3/4)

## Fonte de dados

USGS Earthquake Hazards Program — FDSN Web Service:
`https://earthquake.usgs.gov/fdsnws/event/1/query`

# Exploração inicial do USGS

O notebook [ingestao_inicial_usgs.ipynb](ingestao_inicial_usgs.ipynb) registra o primeiro teste de ingestão. Ele usa a tabela `workspace.sismos_bronze.eventos_usgs`, criada para essa exploração.

A Aula 2 usa o catálogo `sismos` e tem três etapas em `notebooks/`:

1. [Extração de USGS e EMSC](../01_extract_usgs_landing.py)
2. [Carga incremental na Bronze](../02_bronze_autoloader.py)
3. [Validação e evidências](../evidencias_desafio_02.py)

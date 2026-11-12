-- ============================================================================
-- NOTEBOOK: 00_setup_and_delta_fundamentals.sql
-- OBJETIVO: Configurar a hierarquia do Unity Catalog (catálogo, schemas e volumes)
--           e validar propriedades ACID, Time Travel e Lineage no Delta Lake.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- PARTE 1: DEMONSTRAÇÃO DELTA LAKE (VERSIONAMENTO E TIME TRAVEL)
-- Simula o ciclo de vida de um dado sísmico real (estimativa automática -> revisões)
-- ----------------------------------------------------------------------------

-- 1. Cria a tabela gerenciada no catálogo padrão do workspace (Versão 0)
CREATE TABLE IF NOT EXISTS workspace.default.demo_grandes_2025 (
  id           STRING,
  lugar        STRING,
  magnitude    DOUBLE,
  horario_utc  TIMESTAMP,
  status       STRING
);

-- 2. Insere registros iniciais simulando leituras automáticas e revisadas (Versão 1)
INSERT INTO workspace.default.demo_grandes_2025 VALUES
  ('us6000qw60', 'Kamchatka Peninsula, Russia', 8.0, TIMESTAMP '2025-07-29 23:24:52', 'automatic'),
  ('us7000pn9s', 'Mandalay, Burma (Myanmar)',   7.7, TIMESTAMP '2025-03-28 06:20:52', 'reviewed'),
  ('us6000rgf4', 'Drake Passage',               7.6, TIMESTAMP '2025-10-10 20:29:20', 'reviewed');

-- 3. Simula revisões sismológicas consecutivas no evento de Kamchatka (Versões 2 e 3)
UPDATE workspace.default.demo_grandes_2025 
SET magnitude = 8.7 
WHERE id = 'us6000qw60';

UPDATE workspace.default.demo_grandes_2025 
SET magnitude = 8.8, status = 'reviewed' 
WHERE id = 'us6000qw60';

-- 4. Consulta o log de transações (_delta_log) com usuário, horário UTC e operação
DESCRIBE HISTORY workspace.default.demo_grandes_2025;

-- 5. Time Travel: lê o estado original da tabela antes das revisões (Versão 1)
SELECT id, magnitude, status 
FROM workspace.default.demo_grandes_2025 VERSION AS OF 1;

-- 6. Simula exclusão acidental (DELETE sem WHERE) e aplica rollback via RESTORE
DELETE FROM workspace.default.demo_grandes_2025;

-- Restaura a tabela para o estado íntegro da Versão 3 (gera uma nova versão de auditoria)
RESTORE TABLE workspace.default.demo_grandes_2025 TO VERSION AS OF 3;

-- Valida se os registros foram recuperados com sucesso
SELECT * FROM workspace.default.demo_grandes_2025;


-- ----------------------------------------------------------------------------
-- PARTE 2: ESTRUTURAÇÃO DO UNITY CATALOG (ARQUITETURA MEDALHÃO)
-- Namespace de 3 níveis: catalogo.schema.objeto
-- ----------------------------------------------------------------------------

-- 7. Cria o catálogo dedicado do projeto (executar esta instrução primeiro)
CREATE CATALOG IF NOT EXISTS sismos;

-- 8. Cria os schemas das camadas Bronze, Silver e Gold
CREATE SCHEMA IF NOT EXISTS sismos.bronze;
CREATE SCHEMA IF NOT EXISTS sismos.silver;
CREATE SCHEMA IF NOT EXISTS sismos.gold;

-- 9. Cria os volumes gerenciados para arquivos brutos (landing) e estado do Auto Loader (checkpoints)
CREATE VOLUME IF NOT EXISTS sismos.bronze.landing;
CREATE VOLUME IF NOT EXISTS sismos.bronze.checkpoints;


-- ----------------------------------------------------------------------------
-- PARTE 3: LINHAGEM AUTOMÁTICA (LINEAGE) E GOVERNANÇA
-- ----------------------------------------------------------------------------

-- 10. Gera uma tabela agregada na camada Gold para registrar linhagem automática entre catálogos
CREATE OR REPLACE TABLE sismos.gold.demo_resumo AS
SELECT 
  status, 
  count(*) AS eventos, 
  max(magnitude) AS maior_magnitude
FROM workspace.default.demo_grandes_2025
GROUP BY status;

-- 11. Verifica o usuário autenticado e as permissões atuais do schema Gold
SELECT current_user();
SHOW GRANTS ON SCHEMA sismos.gold;

-- ============================================================
-- Master setup script. From the sql folder, connected as the
-- project user (e.g. irrigation), run:   @setup.sql
-- Safe to re-run: it drops and recreates everything.
-- ============================================================
SET ECHO OFF
SET FEEDBACK ON
SET DEFINE OFF

PROMPT ---- Dropping old objects ----
@@01_drop.sql
PROMPT ---- Creating tables ----
@@02_schema.sql
PROMPT ---- Creating PL/SQL trigger, function, procedure ----
@@03_plsql.sql
PROMPT ---- Inserting sample data ----
@@04_seed.sql

PROMPT ---- Row counts ----
SELECT 'IRRIGATION_PUMP' AS table_name, COUNT(*) AS row_count FROM irrigation_pump
UNION ALL SELECT 'AGRICULTURAL_FIELD', COUNT(*) FROM agricultural_field
UNION ALL SELECT 'FARM_OWNER', COUNT(*) FROM farm_owner
UNION ALL SELECT 'FIELD_LEASE', COUNT(*) FROM field_lease
UNION ALL SELECT 'TECHNICIAN', COUNT(*) FROM technician
UNION ALL SELECT 'MAINTENANCE_LOG', COUNT(*) FROM maintenance_log
UNION ALL SELECT 'IRRIGATION_SCHEDULE', COUNT(*) FROM irrigation_schedule
UNION ALL SELECT 'APP_USER', COUNT(*) FROM app_user;

PROMPT ---- Setup complete. Start the web app with: python app.py ----

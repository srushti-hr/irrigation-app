-- ============================================================
-- Drops every project object so setup.sql can be re-run safely.
-- "Does not exist" errors are ignored.
-- ============================================================

BEGIN
  FOR t IN (SELECT column_value AS name FROM TABLE(sys.odcivarchar2list(
              'IRRIGATION_SCHEDULE', 'MAINTENANCE_LOG', 'TECHNICIAN',
              'FIELD_LEASE', 'FARM_OWNER', 'AGRICULTURAL_FIELD',
              'IRRIGATION_PUMP', 'APP_USER'))) LOOP
    BEGIN
      EXECUTE IMMEDIATE 'DROP TABLE ' || t.name || ' CASCADE CONSTRAINTS';
    EXCEPTION
      WHEN OTHERS THEN
        IF SQLCODE != -942 THEN RAISE; END IF;   -- ORA-00942: table does not exist
    END;
  END LOOP;
END;
/

BEGIN
  EXECUTE IMMEDIATE 'DROP FUNCTION fn_pump_maintenance_cost';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -4043 THEN RAISE; END IF;
END;
/

BEGIN
  EXECUTE IMMEDIATE 'DROP PROCEDURE sp_raise_rent';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -4043 THEN RAISE; END IF;
END;
/

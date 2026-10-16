-- ============================================================
-- PL/SQL objects used by the web application
-- ============================================================

-- 1. TRIGGER: a pump cannot be serviced by a technician
--    before that technician was hired.
CREATE OR REPLACE TRIGGER trg_maint_hire_date
BEFORE INSERT OR UPDATE OF service_date, tech_id ON maintenance_log
FOR EACH ROW
DECLARE
  v_hire_date technician.hire_date%TYPE;
BEGIN
  SELECT hire_date INTO v_hire_date
  FROM   technician
  WHERE  tech_id = :NEW.tech_id;

  IF :NEW.service_date < v_hire_date THEN
    RAISE_APPLICATION_ERROR(-20001,
      'Service date cannot be before the technician''s hire date ('
      || TO_CHAR(v_hire_date, 'DD-MON-YYYY') || ')');
  END IF;
EXCEPTION
  WHEN NO_DATA_FOUND THEN
    NULL;  -- unknown tech_id: the foreign key constraint reports it
END;
/

-- 2. FUNCTION: total maintenance cost of one pump
--    (labour hours x technician rate + parts cost, over all jobs).
CREATE OR REPLACE FUNCTION fn_pump_maintenance_cost (
  p_pump_serial IN irrigation_pump.pump_serial%TYPE
) RETURN NUMBER
IS
  v_total NUMBER := 0;
BEGIN
  SELECT NVL(SUM(m.labour_hours * t.hourly_rate + m.parts_cost), 0)
  INTO   v_total
  FROM   maintenance_log m
  JOIN   technician t ON t.tech_id = m.tech_id
  WHERE  m.pump_serial = p_pump_serial;

  RETURN v_total;
END fn_pump_maintenance_cost;
/

-- 3. PROCEDURE: raise the annual rent on every lease of one owner
--    by a percentage; returns the number of leases changed.
CREATE OR REPLACE PROCEDURE sp_raise_rent (
  p_owner_id  IN  farm_owner.owner_id%TYPE,
  p_percent   IN  NUMBER,
  p_rows      OUT NUMBER
)
IS
BEGIN
  IF p_percent <= 0 OR p_percent > 50 THEN
    RAISE_APPLICATION_ERROR(-20002, 'Percentage must be between 0 and 50');
  END IF;

  UPDATE field_lease
  SET    annual_rent = ROUND(annual_rent * (1 + p_percent / 100), 2)
  WHERE  owner_id = p_owner_id;

  p_rows := SQL%ROWCOUNT;
  COMMIT;
END sp_raise_rent;
/

SHOW ERRORS

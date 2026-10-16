-- ============================================================
-- Commercial Irrigation Asset Management System
-- Table creation with all constraints (7 entities + login table)
-- ============================================================

CREATE TABLE irrigation_pump (
  pump_serial        VARCHAR2(10) PRIMARY KEY,
  horsepower_rating  NUMBER(6,1)  NOT NULL CHECK (horsepower_rating > 0),
  flow_capacity_gpm  NUMBER(6)    NOT NULL CHECK (flow_capacity_gpm > 0),
  fuel_type          VARCHAR2(10) NOT NULL CHECK (fuel_type IN ('Diesel','Electric'))
);

CREATE TABLE agricultural_field (
  field_code       VARCHAR2(10) PRIMARY KEY,
  crop_cultivated  VARCHAR2(30) NOT NULL,
  total_acreage    NUMBER(6)    NOT NULL CHECK (total_acreage > 0),
  layout_type      VARCHAR2(15) CHECK (layout_type IN ('Pivot-Line','Drip-System','Flood-Gate')),
  pump_serial      VARCHAR2(10),
  CONSTRAINT fk_field_pump FOREIGN KEY (pump_serial) REFERENCES irrigation_pump(pump_serial)
);

CREATE TABLE farm_owner (
  owner_id    VARCHAR2(6)  PRIMARY KEY,
  owner_name  VARCHAR2(40) NOT NULL,
  contact_no  CHAR(10)     NOT NULL UNIQUE CHECK (LENGTH(contact_no) = 10),
  village     VARCHAR2(30),
  email       VARCHAR2(50) UNIQUE
);

CREATE TABLE field_lease (
  lease_id     NUMBER(5)    PRIMARY KEY,
  field_code   VARCHAR2(10) NOT NULL,
  owner_id     VARCHAR2(6)  NOT NULL,
  start_date   DATE         NOT NULL,
  end_date     DATE         NOT NULL,
  annual_rent  NUMBER(10,2) CHECK (annual_rent > 0),
  CONSTRAINT fk_lease_field FOREIGN KEY (field_code) REFERENCES agricultural_field(field_code),
  CONSTRAINT fk_lease_owner FOREIGN KEY (owner_id)   REFERENCES farm_owner(owner_id),
  CONSTRAINT chk_lease_dates CHECK (end_date > start_date)
);

CREATE TABLE technician (
  tech_id         VARCHAR2(5)  PRIMARY KEY,
  tech_name       VARCHAR2(40) NOT NULL,
  specialization  VARCHAR2(20) CHECK (specialization IN ('Diesel Engine','Electric Motor','Hydraulics')),
  phone           CHAR(10)     UNIQUE,
  hire_date       DATE         NOT NULL,
  hourly_rate     NUMBER(7,2)  DEFAULT 400 CHECK (hourly_rate > 0)
);

CREATE TABLE maintenance_log (
  log_id        NUMBER(6)    PRIMARY KEY,
  pump_serial   VARCHAR2(10) NOT NULL,
  tech_id       VARCHAR2(5)  NOT NULL,
  service_date  DATE         NOT NULL,
  service_type  VARCHAR2(12) CHECK (service_type IN ('Preventive','Repair','Overhaul')),
  labour_hours  NUMBER(4,1)  CHECK (labour_hours > 0),
  parts_cost    NUMBER(10,2) DEFAULT 0 CHECK (parts_cost >= 0),
  CONSTRAINT fk_log_pump FOREIGN KEY (pump_serial) REFERENCES irrigation_pump(pump_serial),
  CONSTRAINT fk_log_tech FOREIGN KEY (tech_id)     REFERENCES technician(tech_id)
);

CREATE TABLE irrigation_schedule (
  schedule_id      NUMBER(6)    PRIMARY KEY,
  field_code       VARCHAR2(10) NOT NULL,
  irrigation_date  DATE         NOT NULL,
  shift            VARCHAR2(10) CHECK (shift IN ('Morning','Evening','Night')),
  duration_hrs     NUMBER(4,1)  CHECK (duration_hrs BETWEEN 0.5 AND 24),
  water_used_gal   NUMBER(10)   CHECK (water_used_gal >= 0),
  CONSTRAINT fk_sched_field FOREIGN KEY (field_code) REFERENCES agricultural_field(field_code)
);

-- Login table used only by the web application (not part of the E-R model)
CREATE TABLE app_user (
  username       VARCHAR2(30)  PRIMARY KEY,
  password_hash  VARCHAR2(255) NOT NULL,
  full_name      VARCHAR2(60)  NOT NULL,
  role           VARCHAR2(10)  DEFAULT 'viewer' NOT NULL CHECK (role IN ('admin','viewer')),
  created_at     DATE          DEFAULT SYSDATE
);

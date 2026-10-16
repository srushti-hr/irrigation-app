-- ============================================================
-- Run ONCE as SYSTEM (or SYS) to create the project schema user.
--
--   21c XE  : sqlplus system/<password>@localhost:1521/XEPDB1
--   23ai    : sqlplus system/<password>@localhost:1521/FREEPDB1
--   11g XE  : sqlplus system/<password>@localhost:1521/XE
--
-- Then:  @00_create_user.sql
-- Skip this file if your lab already gave you a schema/user.
-- ============================================================

CREATE USER irrigation IDENTIFIED BY irrigation123
  DEFAULT TABLESPACE users
  QUOTA UNLIMITED ON users;

GRANT CREATE SESSION, CREATE TABLE, CREATE VIEW, CREATE SEQUENCE,
      CREATE PROCEDURE, CREATE TRIGGER TO irrigation;

PROMPT User IRRIGATION created. Now connect as irrigation and run @setup.sql

# AquaField: Commercial Irrigation Asset Management System

A full-stack web application on **Oracle Database** for BACSE202 (Set 59: Commercial Irrigation Assets).
It manages irrigation pumps, the fields they serve, farm owners and their leases, technicians,
maintenance records and the daily irrigation schedule.

- **Frontend:** HTML, CSS, JavaScript (Jinja templates)
- **Backend:** Python + Flask
- **Database:** Oracle (SQL + PL/SQL) through `python-oracledb`

## Features

| Area | What it does |
| --- | --- |
| Login | Log in, register, log out. Passwords stored as salted PBKDF2 hashes. Sessions expire after 8 hours. Every form is CSRF-protected. |
| Roles | `admin` can insert, update and delete. `viewer` (and every newly registered user) is read-only, enforced on the server. |
| Dashboard | Totals, row counts for all 7 tables, maintenance cost per pump (PL/SQL function), acreage by crop, latest service jobs (3-table join). |
| 7 entity pages | **SELECT** with search (any column) and click-to-sort, **INSERT**, **UPDATE**, **DELETE**. Foreign keys are dropdowns of real parent rows. |
| Oracle errors | Constraint violations are shown in plain words **and** the raw `ORA-xxxxx` message, e.g. deleting a pump still used by a field shows `ORA-02292 … FK_FIELD_PUMP`. |
| SQL shown | After every insert/update/delete the exact SQL statement and bind values are shown. Each list page can reveal its SELECT. |
| SQL Reports | 22 live queries: aggregate and single-row functions, GROUP BY, HAVING, subqueries (incl. nested), inner / 3-table / left outer joins. |
| PL/SQL | Trigger `trg_maint_hire_date`, function `fn_pump_maintenance_cost`, procedure `sp_raise_rent` (with OUT parameter), all used by the app. |

## Project structure

```
irrigation-app/
├── app.py              Flask routes: auth, dashboard, CRUD, reports
├── db.py               Oracle connection pool, query helpers, ORA- error messages
├── entities.py         Definition of the 7 tables (columns, types, foreign keys)
├── reports.py          The report queries (same as the project report)
├── sql/
│   ├── 00_create_user.sql   create the IRRIGATION schema (run as SYSTEM, once)
│   ├── 01_drop.sql          drop old objects (makes setup re-runnable)
│   ├── 02_schema.sql        CREATE TABLE with all constraints
│   ├── 03_plsql.sql         trigger, function, procedure
│   ├── 04_seed.sql          sample data + demo logins
│   └── setup.sql            runs 01 → 04
├── templates/          HTML pages
├── static/style.css    styling
├── requirements.txt
└── .env.example        database settings template
```

## Setup on Windows (localhost)

### 1. Install the prerequisites

- **Oracle Database** 21c XE or 23ai Free (the one used in your lab is fine).
  Note the SYSTEM password you chose during installation.
- **Python 3.10+** from python.org. Tick **"Add python.exe to PATH"** during install.

### 2. Create the database user and tables

Open Command Prompt in the project's `sql` folder:

```bat
cd path\to\irrigation-app\sql

:: 21c XE uses XEPDB1, 23ai Free uses FREEPDB1
sqlplus system/YOUR_SYSTEM_PASSWORD@localhost:1521/XEPDB1
```

In SQL*Plus:

```sql
@00_create_user.sql
CONNECT irrigation/irrigation123@localhost:1521/XEPDB1
@setup.sql
EXIT
```

The last step prints a row count for each table (6 pumps, 5 rows in the others, 2 users).
You can re-run `@setup.sql` any time to reset the data.

> Already have a lab schema? Skip `00_create_user.sql`, connect as your own user and run `@setup.sql`,
> then put that username and password in `.env`.

### 3. Configure and run the app

Back in the project folder (`cd ..`):

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` in Notepad and check `DB_USER`, `DB_PASSWORD` and `DB_DSN`. Then:

```bat
python app.py
```

Open **http://localhost:5000** and log in:

| Username | Password | Access |
| --- | --- | --- |
| `admin` | `admin123` | full access |
| `viewer` | `viewer123` | read-only |

Next time you only need `venv\Scripts\activate` and `python app.py`.

### Troubleshooting

| Problem | Fix |
| --- | --- |
| `DPY-6005` / `ORA-12541` cannot connect | Oracle service not running, or wrong port. Start "OracleServiceXE" in Services. |
| `ORA-12514` service not known | Wrong service name in `DB_DSN`. Run `lsnrctl status` to see it (XEPDB1, FREEPDB1, XE). |
| `ORA-01017` invalid username/password | Check `DB_USER` / `DB_PASSWORD` in `.env`. |
| `ORA-00942` table or view does not exist | `setup.sql` was run as a different user. Connect as the `.env` user and run it again. |
| `DPY-3010` database version not supported | Oracle 11g: install Oracle Instant Client and set `ORACLE_CLIENT_LIB` in `.env`. |
| `'python' is not recognized` | Reinstall Python with "Add to PATH" ticked, or use `py` instead of `python`. |

## Demo video script (about 6–8 minutes)

1. **Login page.** Try a wrong password (error), then log in as `admin`.
2. **Dashboard.** Point out the totals, the 7 table counts and the maintenance cost chart
   (computed by the PL/SQL function `fn_pump_maintenance_cost`).
3. **SELECT.** Open *Agricultural Fields*, search "almond", sort by acreage, open
   "Show the SELECT query behind this page".
4. **INSERT.** Add pump `PMP-3370`, then field `FLD-06` that uses it (pump chosen from the
   foreign-key dropdown). Show the "SQL executed" box.
5. **UPDATE.** Edit pump `PMP-3340` and change horsepower 75.5 → 80. Note the primary key is locked.
6. **DELETE.** Delete maintenance log `1004` (works). Then try deleting pump `PMP-3310`:
   Oracle refuses with `ORA-02292` because field FLD-04 uses it (referential integrity).
7. **Constraints.** Add a lease with end date before start date → `CHK_LEASE_DATES`.
   Tick "Skip browser validation" and enter horsepower `-5` → CHECK constraint.
8. **Trigger.** Add a maintenance record for technician T05 (hired 2023) dated 2020 →
   blocked by `trg_maint_hire_date`.
9. **Reports.** Walk through one query from each group: function, GROUP BY, HAVING,
   subquery, join.
10. **Procedure.** Run `sp_raise_rent` for OWN-02 by 10% and show the rent change in the
    join report. Try 80% to show the procedure's own error.
11. **Roles.** Log out, register a new account, show it is read-only.

## Pushing to GitHub

```bat
git init
git add .
git commit -m "AquaField irrigation asset management system"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

`.env` is in `.gitignore`, so your database password is never uploaded.

## Database design

Seven entities: `IRRIGATION_PUMP`, `AGRICULTURAL_FIELD` (given) plus `FARM_OWNER`, `FIELD_LEASE`,
`TECHNICIAN`, `MAINTENANCE_LOG`, `IRRIGATION_SCHEDULE`, all in 3NF. `APP_USER` stores logins for
the website only and is not part of the E-R model.

| Relationship | Cardinality |
| --- | --- |
| IRRIGATION_PUMP serves AGRICULTURAL_FIELD | 1 : N |
| FARM_OWNER signs FIELD_LEASE | 1 : N |
| AGRICULTURAL_FIELD leased in FIELD_LEASE | 1 : N |
| AGRICULTURAL_FIELD has IRRIGATION_SCHEDULE | 1 : N |
| IRRIGATION_PUMP serviced in MAINTENANCE_LOG | 1 : N |
| TECHNICIAN does MAINTENANCE_LOG | 1 : N |

### Security notes

- All user input reaches Oracle as **bind variables**; table and column names come only from a
  fixed whitelist in `entities.py`, so SQL injection is not possible.
- Passwords are hashed (`werkzeug.security`, PBKDF2-SHA256 with salt).
- POST forms carry a per-session CSRF token; admin-only routes are checked on the server.

"""
Fixed report queries (the same ones as section 7 of the project report).
Users can only run these by key; they cannot type their own SQL.
"""

REPORTS = [
    # ---------------------------------------------------------- functions
    {
        "key": "agg-pumps", "group": "Aggregate functions",
        "title": "Pump fleet summary",
        "sql": """SELECT COUNT(*) AS pumps,
       SUM(flow_capacity_gpm) AS total_gpm,
       ROUND(AVG(flow_capacity_gpm), 2) AS avg_gpm,
       MAX(horsepower_rating) AS max_hp,
       MIN(horsepower_rating) AS min_hp
FROM irrigation_pump""",
    },
    {
        "key": "agg-maint", "group": "Aggregate functions",
        "title": "Maintenance spending on parts",
        "sql": """SELECT COUNT(*) AS jobs,
       SUM(parts_cost) AS total_parts,
       ROUND(AVG(parts_cost), 2) AS avg_parts
FROM maintenance_log""",
    },
    {
        "key": "fn-char", "group": "Single-row functions",
        "title": "Character functions on owners",
        "sql": """SELECT UPPER(owner_name) AS name_upper,
       LOWER(village) AS village_lower,
       LENGTH(owner_name) AS name_len,
       SUBSTR(contact_no, 1, 5) AS prefix
FROM farm_owner
ORDER BY owner_id""",
    },
    {
        "key": "fn-num", "group": "Single-row functions",
        "title": "Pump power in kW (1 HP = 0.746 kW)",
        "sql": """SELECT pump_serial || ' (' || fuel_type || ')' AS pump_label,
       ROUND(horsepower_rating * 0.746, 2) AS power_kw
FROM irrigation_pump
ORDER BY pump_serial""",
    },
    {
        "key": "fn-date", "group": "Single-row functions",
        "title": "Lease length and renewal date",
        "sql": """SELECT lease_id,
       ROUND(MONTHS_BETWEEN(end_date, start_date)) AS months,
       TO_CHAR(ADD_MONTHS(end_date, 12), 'DD-MM-YYYY') AS renewal_till
FROM field_lease
ORDER BY lease_id""",
    },
    {
        "key": "plsql-fn", "group": "Single-row functions",
        "title": "PL/SQL function: maintenance cost per pump",
        "sql": """SELECT pump_serial, fuel_type,
       fn_pump_maintenance_cost(pump_serial) AS total_maintenance_cost
FROM irrigation_pump
ORDER BY total_maintenance_cost DESC""",
    },
    # ---------------------------------------------------------- group by
    {
        "key": "gb-fuel", "group": "GROUP BY",
        "title": "Pumps per fuel type",
        "sql": """SELECT fuel_type, COUNT(*) AS pumps,
       ROUND(AVG(horsepower_rating), 2) AS avg_hp
FROM irrigation_pump
GROUP BY fuel_type
ORDER BY fuel_type""",
    },
    {
        "key": "gb-crop", "group": "GROUP BY",
        "title": "Land under each crop",
        "sql": """SELECT crop_cultivated, COUNT(*) AS fields,
       SUM(total_acreage) AS acres
FROM agricultural_field
GROUP BY crop_cultivated
ORDER BY acres DESC""",
    },
    {
        "key": "gb-spec", "group": "GROUP BY",
        "title": "Technicians by specialisation",
        "sql": """SELECT specialization, COUNT(*) AS techs,
       ROUND(AVG(hourly_rate), 2) AS avg_rate
FROM technician
GROUP BY specialization
ORDER BY specialization""",
    },
    # ---------------------------------------------------------- having
    {
        "key": "hv-pump", "group": "HAVING",
        "title": "Pumps serviced more than once",
        "sql": """SELECT pump_serial, COUNT(*) AS jobs,
       SUM(parts_cost) AS parts_total
FROM maintenance_log
GROUP BY pump_serial
HAVING COUNT(*) > 1""",
    },
    {
        "key": "hv-crop", "group": "HAVING",
        "title": "Crops covering more than 100 acres",
        "sql": """SELECT crop_cultivated, SUM(total_acreage) AS acres
FROM agricultural_field
GROUP BY crop_cultivated
HAVING SUM(total_acreage) > 100
ORDER BY acres DESC""",
    },
    {
        "key": "hv-rent", "group": "HAVING",
        "title": "Owners paying over ₹3,00,000 rent a year",
        "sql": """SELECT owner_id, COUNT(*) AS leases,
       SUM(annual_rent) AS total_rent
FROM field_lease
GROUP BY owner_id
HAVING SUM(annual_rent) > 300000
ORDER BY total_rent DESC""",
    },
    # ---------------------------------------------------------- subqueries
    {
        "key": "sq-flow", "group": "Subqueries",
        "title": "Pumps with above-average flow",
        "sql": """SELECT pump_serial, flow_capacity_gpm
FROM irrigation_pump
WHERE flow_capacity_gpm > (SELECT AVG(flow_capacity_gpm) FROM irrigation_pump)
ORDER BY flow_capacity_gpm DESC""",
    },
    {
        "key": "sq-largest", "group": "Subqueries",
        "title": "Largest field",
        "sql": """SELECT field_code, crop_cultivated, total_acreage
FROM agricultural_field
WHERE total_acreage = (SELECT MAX(total_acreage) FROM agricultural_field)""",
    },
    {
        "key": "sq-standby", "group": "Subqueries",
        "title": "Standby pumps (not assigned to any field)",
        "sql": """SELECT pump_serial, fuel_type, flow_capacity_gpm
FROM irrigation_pump
WHERE pump_serial NOT IN (SELECT pump_serial FROM agricultural_field
                          WHERE pump_serial IS NOT NULL)""",
    },
    {
        "key": "sq-nolease", "group": "Subqueries",
        "title": "Owners without a lease",
        "sql": """SELECT owner_id, owner_name
FROM farm_owner
WHERE owner_id NOT IN (SELECT owner_id FROM field_lease)""",
    },
    {
        "key": "sq-nested", "group": "Subqueries",
        "title": "Technicians who serviced a diesel pump (nested)",
        "sql": """SELECT tech_id, tech_name
FROM technician
WHERE tech_id IN (SELECT tech_id FROM maintenance_log
                  WHERE pump_serial IN (SELECT pump_serial FROM irrigation_pump
                                        WHERE fuel_type = 'Diesel'))
ORDER BY tech_id""",
    },
    # ---------------------------------------------------------- joins
    {
        "key": "jn-field-pump", "group": "Joins",
        "title": "Each field with its pump (inner join)",
        "sql": """SELECT f.field_code, f.crop_cultivated, p.pump_serial,
       p.fuel_type, p.flow_capacity_gpm
FROM agricultural_field f
JOIN irrigation_pump p ON f.pump_serial = p.pump_serial
ORDER BY f.field_code""",
    },
    {
        "key": "jn-owner", "group": "Joins",
        "title": "Owner, leased field and rent (3-table join)",
        "sql": """SELECT o.owner_name, f.field_code, f.crop_cultivated, l.annual_rent
FROM farm_owner o
JOIN field_lease l        ON o.owner_id = l.owner_id
JOIN agricultural_field f ON l.field_code = f.field_code
ORDER BY o.owner_name, f.field_code""",
    },
    {
        "key": "jn-left", "group": "Joins",
        "title": "Every owner, with or without a lease (left outer join)",
        "sql": """SELECT o.owner_name, l.lease_id
FROM farm_owner o
LEFT OUTER JOIN field_lease l ON o.owner_id = l.owner_id
ORDER BY o.owner_id, l.lease_id""",
    },
    {
        "key": "jn-cost", "group": "Joins",
        "title": "Total cost of each service job",
        "sql": """SELECT m.log_id, p.pump_serial, p.fuel_type, t.tech_name, m.service_type,
       m.labour_hours * t.hourly_rate + m.parts_cost AS total_cost
FROM maintenance_log m
JOIN irrigation_pump p ON m.pump_serial = p.pump_serial
JOIN technician t      ON m.tech_id = t.tech_id
ORDER BY m.log_id""",
    },
    {
        "key": "jn-water", "group": "Joins",
        "title": "Water used per acre on each run",
        "sql": """SELECT f.field_code, TO_CHAR(s.irrigation_date, 'DD-MM-YYYY') AS run_date,
       s.water_used_gal,
       ROUND(s.water_used_gal / f.total_acreage, 2) AS gal_per_acre
FROM irrigation_schedule s
JOIN agricultural_field f ON s.field_code = f.field_code
ORDER BY s.irrigation_date, f.field_code""",
    },
]

REPORTS_BY_KEY = {r["key"]: r for r in REPORTS}

"""
Describes the 7 entities so one set of routes and templates can
list / insert / update / delete / search any of them.

Table and column names used in SQL come ONLY from this file (a whitelist);
values typed by the user are always passed as bind variables.

Column keys:
  name      column name in Oracle
  label     text shown in the UI
  type      text | number | date | select | fk
  required  NOT NULL in the schema
  options   allowed values (type=select, mirrors the CHECK constraint)
  fk        (table, key_column, display_column) for a dropdown of parent rows
  step/min/max/maxlength   HTML input hints (Oracle constraints still decide)
"""

ENTITIES = {
    "pumps": {
        "table": "irrigation_pump",
        "title": "Irrigation Pumps",
        "singular": "Pump",
        "icon": "⚙",
        "pk": "pump_serial",
        "auto_pk": False,
        "pk_hint": "e.g. PMP-3370",
        "default_sort": "pump_serial",
        "columns": [
            {"name": "pump_serial", "label": "Pump serial", "type": "text", "required": True, "maxlength": 10},
            {"name": "horsepower_rating", "label": "Horsepower (HP)", "type": "number", "required": True, "step": "0.1", "min": "0.1"},
            {"name": "flow_capacity_gpm", "label": "Flow capacity (GPM)", "type": "number", "required": True, "step": "1", "min": "1"},
            {"name": "fuel_type", "label": "Fuel type", "type": "select", "required": True, "options": ["Diesel", "Electric"]},
        ],
        # extra read-only column computed by the PL/SQL function
        "computed": [
            {"name": "maint_cost", "label": "Maintenance cost (₹)",
             "sql": "fn_pump_maintenance_cost(pump_serial)", "money": True},
        ],
    },
    "fields": {
        "table": "agricultural_field",
        "title": "Agricultural Fields",
        "singular": "Field",
        "icon": "▦",
        "pk": "field_code",
        "auto_pk": False,
        "pk_hint": "e.g. FLD-06",
        "default_sort": "field_code",
        "columns": [
            {"name": "field_code", "label": "Field code", "type": "text", "required": True, "maxlength": 10},
            {"name": "crop_cultivated", "label": "Crop", "type": "text", "required": True, "maxlength": 30},
            {"name": "total_acreage", "label": "Acreage", "type": "number", "required": True, "step": "1", "min": "1"},
            {"name": "layout_type", "label": "Layout", "type": "select", "required": False,
             "options": ["Pivot-Line", "Drip-System", "Flood-Gate"]},
            {"name": "pump_serial", "label": "Pump", "type": "fk", "required": False,
             "fk": ("irrigation_pump", "pump_serial", "pump_serial || ' – ' || fuel_type || ', ' || flow_capacity_gpm || ' GPM'")},
        ],
    },
    "owners": {
        "table": "farm_owner",
        "title": "Farm Owners",
        "singular": "Owner",
        "icon": "☺",
        "pk": "owner_id",
        "auto_pk": False,
        "pk_hint": "e.g. OWN-06",
        "default_sort": "owner_id",
        "columns": [
            {"name": "owner_id", "label": "Owner ID", "type": "text", "required": True, "maxlength": 6},
            {"name": "owner_name", "label": "Name", "type": "text", "required": True, "maxlength": 40},
            {"name": "contact_no", "label": "Contact no.", "type": "text", "required": True, "maxlength": 10,
             "pattern": "[0-9]{10}", "title": "10-digit mobile number"},
            {"name": "village", "label": "Village", "type": "text", "required": False, "maxlength": 30},
            {"name": "email", "label": "Email", "type": "email", "required": False, "maxlength": 50},
        ],
    },
    "leases": {
        "table": "field_lease",
        "title": "Field Leases",
        "singular": "Lease",
        "icon": "✎",
        "pk": "lease_id",
        "auto_pk": True,
        "default_sort": "lease_id",
        "columns": [
            {"name": "lease_id", "label": "Lease ID", "type": "number", "required": True, "step": "1", "min": "1"},
            {"name": "field_code", "label": "Field", "type": "fk", "required": True,
             "fk": ("agricultural_field", "field_code", "field_code || ' – ' || crop_cultivated")},
            {"name": "owner_id", "label": "Owner", "type": "fk", "required": True,
             "fk": ("farm_owner", "owner_id", "owner_id || ' – ' || owner_name")},
            {"name": "start_date", "label": "Start date", "type": "date", "required": True},
            {"name": "end_date", "label": "End date", "type": "date", "required": True},
            {"name": "annual_rent", "label": "Annual rent (₹)", "type": "number", "required": False,
             "step": "0.01", "min": "0.01", "money": True},
        ],
    },
    "technicians": {
        "table": "technician",
        "title": "Technicians",
        "singular": "Technician",
        "icon": "✚",
        "pk": "tech_id",
        "auto_pk": False,
        "pk_hint": "e.g. T06",
        "default_sort": "tech_id",
        "columns": [
            {"name": "tech_id", "label": "Tech ID", "type": "text", "required": True, "maxlength": 5},
            {"name": "tech_name", "label": "Name", "type": "text", "required": True, "maxlength": 40},
            {"name": "specialization", "label": "Specialisation", "type": "select", "required": False,
             "options": ["Diesel Engine", "Electric Motor", "Hydraulics"]},
            {"name": "phone", "label": "Phone", "type": "text", "required": False, "maxlength": 10,
             "pattern": "[0-9]{10}", "title": "10-digit phone number"},
            {"name": "hire_date", "label": "Hire date", "type": "date", "required": True},
            {"name": "hourly_rate", "label": "Hourly rate (₹)", "type": "number", "required": False,
             "step": "0.01", "min": "0.01", "money": True},
        ],
    },
    "maintenance": {
        "table": "maintenance_log",
        "title": "Maintenance Log",
        "singular": "Service record",
        "icon": "⚒",
        "pk": "log_id",
        "auto_pk": True,
        "default_sort": "log_id",
        "columns": [
            {"name": "log_id", "label": "Log ID", "type": "number", "required": True, "step": "1", "min": "1"},
            {"name": "pump_serial", "label": "Pump", "type": "fk", "required": True,
             "fk": ("irrigation_pump", "pump_serial", "pump_serial || ' – ' || fuel_type")},
            {"name": "tech_id", "label": "Technician", "type": "fk", "required": True,
             "fk": ("technician", "tech_id", "tech_id || ' – ' || tech_name || ' (' || specialization || ')'")},
            {"name": "service_date", "label": "Service date", "type": "date", "required": True},
            {"name": "service_type", "label": "Service type", "type": "select", "required": False,
             "options": ["Preventive", "Repair", "Overhaul"]},
            {"name": "labour_hours", "label": "Labour hours", "type": "number", "required": False, "step": "0.1", "min": "0.1"},
            {"name": "parts_cost", "label": "Parts cost (₹)", "type": "number", "required": False,
             "step": "0.01", "min": "0", "money": True},
        ],
    },
    "schedule": {
        "table": "irrigation_schedule",
        "title": "Irrigation Schedule",
        "singular": "Irrigation run",
        "icon": "≈",
        "pk": "schedule_id",
        "auto_pk": True,
        "default_sort": "schedule_id",
        "columns": [
            {"name": "schedule_id", "label": "Schedule ID", "type": "number", "required": True, "step": "1", "min": "1"},
            {"name": "field_code", "label": "Field", "type": "fk", "required": True,
             "fk": ("agricultural_field", "field_code", "field_code || ' – ' || crop_cultivated")},
            {"name": "irrigation_date", "label": "Date", "type": "date", "required": True},
            {"name": "shift", "label": "Shift", "type": "select", "required": False, "options": ["Morning", "Evening", "Night"]},
            {"name": "duration_hrs", "label": "Duration (hrs)", "type": "number", "required": False,
             "step": "0.5", "min": "0.5", "max": "24"},
            {"name": "water_used_gal", "label": "Water used (gal)", "type": "number", "required": False, "step": "1", "min": "0"},
        ],
    },
}


def column(entity, name):
    for c in entity["columns"]:
        if c["name"] == name:
            return c
    return None

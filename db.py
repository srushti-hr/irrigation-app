"""
Oracle connection handling (python-oracledb) and small query helpers.
"""
import os
import re

import oracledb

_pool = None


def init_pool():
    """Create the connection pool once, using settings from .env."""
    global _pool
    # Oracle 11g needs "thick" mode (Oracle Instant Client). 12c and later
    # work in the default "thin" mode with nothing else installed.
    client_dir = os.getenv("ORACLE_CLIENT_LIB")
    if client_dir:
        oracledb.init_oracle_client(lib_dir=client_dir)

    _pool = oracledb.create_pool(
        user=os.getenv("DB_USER", "irrigation"),
        password=os.getenv("DB_PASSWORD", "irrigation123"),
        dsn=os.getenv("DB_DSN", "localhost:1521/XEPDB1"),
        min=1, max=4, increment=1,
    )
    return _pool


def get_conn():
    if _pool is None:
        init_pool()
    return _pool.acquire()


def _rows(cur):
    cols = [d[0].lower() for d in cur.description]
    return cols, [dict(zip(cols, r)) for r in cur.fetchall()]


def query(sql, params=None):
    """Run a SELECT and return a list of dicts (lower-case keys)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            return _rows(cur)[1]


def query_with_cols(sql, params=None):
    """Run a SELECT and return (column_names, rows)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            return _rows(cur)


def query_one(sql, params=None):
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=None):
    """Run INSERT / UPDATE / DELETE, commit, return rows affected."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            n = cur.rowcount
        conn.commit()
        return n


def call_function(name, return_type, args):
    with get_conn() as conn:
        with conn.cursor() as cur:
            return cur.callfunc(name, return_type, args)


def call_procedure_out(name, in_args):
    """Call a procedure whose last parameter is an OUT NUMBER; return it."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            out = cur.var(oracledb.DB_TYPE_NUMBER)
            cur.callproc(name, list(in_args) + [out])
            return out.getvalue()


# ---------------------------------------------------------------- errors

# Friendly messages for the Oracle errors a user can trigger from the UI.
ORA_MESSAGES = {
    1: "A record with this ID (or a unique value such as phone/email) already exists.",
    1400: "A required field was left empty.",
    1722: "A number field contains text.",
    1830: "A date is in the wrong format.",
    1840: "A date is in the wrong format.",
    1841: "A date is out of range.",
    1847: "A date is not valid for the month.",
    1861: "A date is in the wrong format.",
    2290: "A value breaks a CHECK rule of the table.",
    2291: "The selected parent record does not exist.",
    2292: "This record is still referenced by other records, so it cannot be deleted.",
    12899: "A value is too long for its column.",
    1438: "A number is too large for its column.",
}

# Extra explanations for named CHECK / FK constraints.
CONSTRAINT_HINTS = {
    "CHK_LEASE_DATES": "End date must be after the start date.",
    "FK_FIELD_PUMP": "A field still uses this pump.",
    "FK_LOG_PUMP": "This pump has maintenance records.",
    "FK_LOG_TECH": "This technician has maintenance records.",
    "FK_LEASE_FIELD": "This field has leases.",
    "FK_LEASE_OWNER": "This owner has leases.",
    "FK_SCHED_FIELD": "This field has irrigation runs scheduled.",
}


def friendly_error(exc):
    """Turn an oracledb error into (message, raw_oracle_text)."""
    err = exc.args[0] if exc.args else None
    code = getattr(err, "code", None)
    raw = (getattr(err, "message", None) or str(exc)).strip().splitlines()[0]

    # RAISE_APPLICATION_ERROR from our PL/SQL (-20000 .. -20999)
    if code and 20000 <= code <= 20999:
        msg = re.sub(r"^ORA-\d+:\s*", "", raw)
        return msg, raw

    msg = ORA_MESSAGES.get(code, "The database rejected this change.")
    m = re.search(r"\(([A-Z0-9_$#]+)\.([A-Z0-9_$#]+)\)", raw)
    if m and m.group(2) in CONSTRAINT_HINTS:
        msg += " " + CONSTRAINT_HINTS[m.group(2)]
    return msg, raw

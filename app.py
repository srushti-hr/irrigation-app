"""
Commercial Irrigation Asset Management System
Flask web application on Oracle Database.

Run:  python app.py      then open http://localhost:5000
"""
import datetime as dt
import os
import re
import secrets
from decimal import Decimal
from functools import wraps

from dotenv import load_dotenv
from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

import oracledb  # noqa: E402  (imported after .env so thick mode can be set)

import db  # noqa: E402
from entities import ENTITIES, column  # noqa: E402
from reports import REPORTS, REPORTS_BY_KEY  # noqa: E402

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)
app.config["PERMANENT_SESSION_LIFETIME"] = dt.timedelta(hours=8)


# ================================================================ helpers

def indian_number(n, decimals=0):
    """1234567.5 -> '12,34,567.50' (Indian digit grouping)."""
    neg = n < 0
    n = abs(n)
    whole, frac = f"{n:.{decimals}f}".split(".") if decimals else (f"{n:.0f}", "")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        whole = head + "," + tail
    out = whole + ("." + frac if frac else "")
    return ("-" if neg else "") + out


@app.template_filter("num")
def fmt_num(v, money=False):
    if v is None or v == "":
        return "—"
    if isinstance(v, (int, float, Decimal)):
        f = float(v)
        if money:
            return "₹" + indian_number(f, 0 if f == int(f) else 2)
        if f == int(f):
            return indian_number(int(f))
        return f"{f:,.2f}".rstrip("0").rstrip(".")
    return v


@app.template_filter("date")
def fmt_date(v):
    if v is None or v == "":
        return "—"
    if isinstance(v, (dt.date, dt.datetime)):
        return v.strftime("%d %b %Y")
    try:
        return dt.date.fromisoformat(str(v)[:10]).strftime("%d %b %Y")
    except ValueError:
        return v


def date_input_value(v):
    if v is None:
        return ""
    if isinstance(v, (dt.date, dt.datetime)):
        return v.strftime("%Y-%m-%d")
    return str(v)[:10]


def cell(value, col):
    """Format one table cell according to its column definition."""
    if col.get("type") == "date":
        return fmt_date(value)
    if col["name"].endswith("_id") and isinstance(value, (int, float, Decimal)):
        return str(int(value))
    if isinstance(value, (int, float, Decimal)):
        return fmt_num(value, money=col.get("money", False))
    return "—" if value in (None, "") else value


def auto(value, name=""):
    """Format a value of unknown type (used by the reports page)."""
    if isinstance(value, (dt.date, dt.datetime)):
        return fmt_date(value)
    if name.endswith("_id") and isinstance(value, (int, float, Decimal)):
        return str(int(value))
    return fmt_num(value)


app.jinja_env.globals.update(cell=cell, auto=auto, ENTITIES=ENTITIES)


# ================================================================ security

@app.before_request
def csrf_protect():
    """Every POST must carry the token stored in the user's session."""
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    if request.method == "POST":
        if request.form.get("csrf") != session["csrf"]:
            abort(400, "Form expired. Go back, reload the page and try again.")
    g.user = session.get("user")


@app.context_processor
def inject_csrf():
    return {"csrf_token": session.get("csrf", ""), "user": g.get("user")}


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not g.user:
            flash("Please log in to continue.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if g.user["role"] != "admin":
            flash("Your account is read-only. Log in as an admin to make changes.", "error")
            return redirect(request.referrer or url_for("dashboard"))
        return view(*args, **kwargs)
    return wrapper


# ================================================================ auth

@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        try:
            row = db.query_one(
                "SELECT username, password_hash, full_name, role "
                "FROM app_user WHERE username = :u", {"u": username})
        except oracledb.Error as e:
            flash("Cannot reach the database: " + db.friendly_error(e)[1], "error")
            return render_template("login.html", username=username)

        if row and check_password_hash(row["password_hash"], password):
            session.clear()
            session.permanent = True
            session["user"] = {"username": row["username"],
                               "full_name": row["full_name"], "role": row["role"]}
            flash(f"Welcome back, {row['full_name']}.", "success")
            nxt = request.args.get("next", "")
            return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//")
                            else url_for("dashboard"))
        flash("Incorrect username or password.", "error")
        return render_template("login.html", username=username)
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("dashboard"))
    form = {"username": "", "full_name": ""}
    if request.method == "POST":
        form["username"] = request.form.get("username", "").strip().lower()
        form["full_name"] = request.form.get("full_name", "").strip()
        pw = request.form.get("password", "")
        pw2 = request.form.get("confirm", "")

        errors = []
        if not re.fullmatch(r"[a-z0-9_]{3,30}", form["username"]):
            errors.append("Username must be 3–30 characters: letters, digits or _.")
        if not form["full_name"]:
            errors.append("Full name is required.")
        if len(pw) < 6:
            errors.append("Password must be at least 6 characters.")
        if pw != pw2:
            errors.append("Passwords do not match.")

        if not errors:
            try:
                db.execute(
                    "INSERT INTO app_user (username, password_hash, full_name, role) "
                    "VALUES (:u, :h, :n, 'viewer')",
                    {"u": form["username"],
                     "h": generate_password_hash(pw, method="pbkdf2:sha256"),
                     "n": form["full_name"][:60]})
                flash("Account created. You can log in now (read-only access).", "success")
                return redirect(url_for("login"))
            except oracledb.IntegrityError:
                errors.append("That username is already taken.")
            except oracledb.Error as e:
                errors.append(db.friendly_error(e)[0])
        for e in errors:
            flash(e, "error")
    return render_template("register.html", form=form)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ================================================================ dashboard

@app.route("/")
@login_required
def dashboard():
    counts = db.query("""
        SELECT 'pumps' AS k, COUNT(*) AS n FROM irrigation_pump
        UNION ALL SELECT 'fields', COUNT(*) FROM agricultural_field
        UNION ALL SELECT 'owners', COUNT(*) FROM farm_owner
        UNION ALL SELECT 'leases', COUNT(*) FROM field_lease
        UNION ALL SELECT 'technicians', COUNT(*) FROM technician
        UNION ALL SELECT 'maintenance', COUNT(*) FROM maintenance_log
        UNION ALL SELECT 'schedule', COUNT(*) FROM irrigation_schedule""")
    counts = {r["k"].strip(): r["n"] for r in counts}

    totals = db.query_one("""
        SELECT (SELECT NVL(SUM(total_acreage), 0) FROM agricultural_field) AS acres,
               (SELECT NVL(SUM(flow_capacity_gpm), 0) FROM irrigation_pump) AS gpm,
               (SELECT NVL(SUM(water_used_gal), 0) FROM irrigation_schedule) AS water,
               (SELECT NVL(SUM(annual_rent), 0) FROM field_lease) AS rent
        FROM dual""")

    pump_costs = db.query("""
        SELECT pump_serial, fuel_type,
               fn_pump_maintenance_cost(pump_serial) AS cost
        FROM irrigation_pump
        ORDER BY cost DESC, pump_serial""")
    total_maint = sum(float(r["cost"] or 0) for r in pump_costs)

    crops = db.query("""
        SELECT crop_cultivated AS crop, SUM(total_acreage) AS acres
        FROM agricultural_field
        GROUP BY crop_cultivated
        ORDER BY acres DESC""")

    recent = db.query("""
        SELECT * FROM (
            SELECT m.log_id, m.service_date, m.service_type, p.pump_serial,
                   t.tech_name,
                   m.labour_hours * t.hourly_rate + m.parts_cost AS total_cost
            FROM maintenance_log m
            JOIN irrigation_pump p ON p.pump_serial = m.pump_serial
            JOIN technician t      ON t.tech_id = m.tech_id
            ORDER BY m.service_date DESC, m.log_id DESC
        ) WHERE ROWNUM <= 5""")

    return render_template("dashboard.html", counts=counts, totals=totals,
                           pump_costs=pump_costs, total_maint=total_maint,
                           crops=crops, recent=recent)


# ================================================================ CRUD

def get_entity(key):
    ent = ENTITIES.get(key)
    if not ent:
        abort(404)
    return ent


def pk_value(ent, raw):
    """Convert the primary key from the URL to the right Python type."""
    if column(ent, ent["pk"])["type"] == "number":
        try:
            return int(raw)
        except ValueError:
            abort(404)
    return raw


def fk_options(ent):
    """Dropdown choices for every foreign-key column: {col: [(value, label)]}."""
    opts = {}
    for c in ent["columns"]:
        if c["type"] == "fk":
            table, keycol, display = c["fk"]
            rows = db.query(f"SELECT {keycol} AS v, {display} AS l FROM {table} ORDER BY {keycol}")
            opts[c["name"]] = [(r["v"], r["l"]) for r in rows]
    return opts


def select_list(ent):
    parts = []
    for c in ent["columns"]:
        parts.append(c["name"])
    for c in ent.get("computed", []):
        parts.append(f"{c['sql']} AS {c['name']}")
    return ", ".join(parts)


def parse_form(ent, form, editing):
    """Validate the submitted form. Returns (values, errors)."""
    values, errors = {}, []
    for c in ent["columns"]:
        name = c["name"]
        if editing and name == ent["pk"]:
            continue
        raw = form.get(name, "").strip()
        if raw == "":
            if c["required"]:
                errors.append(f"{c['label']} is required.")
            values[name] = None
            continue
        t = c["type"]
        if t == "number":
            try:
                num = float(raw)
            except ValueError:
                errors.append(f"{c['label']} must be a number.")
                continue
            values[name] = int(num) if "." not in c.get("step", "1") and num == int(num) else num
        elif t == "date":
            try:
                dt.date.fromisoformat(raw)
            except ValueError:
                errors.append(f"{c['label']} must be a valid date.")
                continue
            values[name] = raw
        elif t == "select" and raw not in c["options"]:
            errors.append(f"{c['label']} must be one of: {', '.join(c['options'])}.")
        else:
            if c.get("pattern") and not re.fullmatch(c["pattern"], raw):
                errors.append(f"{c['label']}: {c.get('title', 'invalid format')}.")
            values[name] = raw
    return values, errors


def show_sql(sql, params):
    """Flash the statement that was run, with bind values, for the demo."""
    binds = ", ".join(f":{k} = {v!r}" for k, v in params.items())
    flash(sql + (f"\n-- binds: {binds}" if binds else ""), "sql")


def bind_expr(ent, name):
    return f"TO_DATE(:{name}, 'YYYY-MM-DD')" if column(ent, name)["type"] == "date" else f":{name}"


@app.route("/e/<key>")
@login_required
def entity_list(key):
    ent = get_entity(key)
    colnames = [c["name"] for c in ent["columns"]] + [c["name"] for c in ent.get("computed", [])]

    q = request.args.get("q", "").strip()
    search_col = request.args.get("col", "")
    sort = request.args.get("sort", ent["default_sort"])
    direction = "DESC" if request.args.get("dir") == "desc" else "ASC"
    if sort not in colnames:
        sort = ent["default_sort"]

    where, params = "", {}
    if q:
        def as_text(c):
            return (f"TO_CHAR({c['name']}, 'YYYY-MM-DD')" if c["type"] == "date"
                    else f"TO_CHAR({c['name']})")
        targets = [c for c in ent["columns"] if c["name"] == search_col] or ent["columns"]
        where = "WHERE " + " OR ".join(f"UPPER({as_text(c)}) LIKE :q" for c in targets)
        params["q"] = f"%{q.upper()}%"

    sql = f"SELECT {select_list(ent)} FROM {ent['table']} {where} ORDER BY {sort} {direction}"
    try:
        rows = db.query(sql, params)
    except oracledb.Error as e:
        msg, raw = db.friendly_error(e)
        flash(f"{msg} ({raw})", "error")
        rows = []

    all_cols = ent["columns"] + ent.get("computed", [])
    return render_template("list.html", key=key, ent=ent, rows=rows, cols=all_cols,
                           q=q, search_col=search_col, sort=sort,
                           dir=direction.lower(), sql=sql.replace(":q", f"'%{q.upper()}%'") if q else sql)


def next_id(ent):
    row = db.query_one(f"SELECT NVL(MAX({ent['pk']}), 0) + 1 AS n FROM {ent['table']}")
    return row["n"]


@app.route("/e/<key>/new", methods=["GET", "POST"])
@admin_required
def entity_new(key):
    ent = get_entity(key)
    record, sql = {}, None
    if request.method == "POST":
        values, errors = parse_form(ent, request.form, editing=False)
        record = dict(request.form)
        if not errors:
            # leave out empty columns so Oracle DEFAULT values apply
            cols = [n for n, v in values.items() if v is not None]
            sql = (f"INSERT INTO {ent['table']} ({', '.join(cols)}) VALUES "
                   f"({', '.join(bind_expr(ent, n) for n in cols)})")
            try:
                params = {n: values[n] for n in cols}
                db.execute(sql, params)
                pk = values[ent["pk"]]
                flash(f"{ent['singular']} {pk} added.", "success")
                show_sql(sql, params)
                return redirect(url_for("entity_list", key=key))
            except oracledb.Error as e:
                msg, raw = db.friendly_error(e)
                errors.append(msg)
                flash(raw, "oracle")
        for e in errors:
            flash(e, "error")
    elif ent.get("auto_pk"):
        record[ent["pk"]] = next_id(ent)

    return render_template("form.html", key=key, ent=ent, record=record, editing=False,
                           fk=fk_options(ent), date_value=date_input_value)


@app.route("/e/<key>/<pk>/edit", methods=["GET", "POST"])
@admin_required
def entity_edit(key, pk):
    ent = get_entity(key)
    pkv = pk_value(ent, pk)
    current = db.query_one(
        f"SELECT {select_list(ent)} FROM {ent['table']} WHERE {ent['pk']} = :pk", {"pk": pkv})
    if not current:
        abort(404)

    record = current
    if request.method == "POST":
        values, errors = parse_form(ent, request.form, editing=True)
        record = dict(request.form, **{ent["pk"]: pkv})
        if not errors:
            sets = ", ".join(f"{n} = {bind_expr(ent, n)}" for n in values)
            sql = f"UPDATE {ent['table']} SET {sets} WHERE {ent['pk']} = :pk__"
            try:
                params = dict(values, pk__=pkv)
                db.execute(sql, params)
                flash(f"{ent['singular']} {pkv} updated.", "success")
                show_sql(sql, params)
                return redirect(url_for("entity_list", key=key))
            except oracledb.Error as e:
                msg, raw = db.friendly_error(e)
                errors.append(msg)
                flash(raw, "oracle")
        for e in errors:
            flash(e, "error")

    return render_template("form.html", key=key, ent=ent, record=record, editing=True,
                           fk=fk_options(ent), date_value=date_input_value)


@app.route("/e/<key>/<pk>/delete", methods=["POST"])
@admin_required
def entity_delete(key, pk):
    ent = get_entity(key)
    pkv = pk_value(ent, pk)
    try:
        sql = f"DELETE FROM {ent['table']} WHERE {ent['pk']} = :pk"
        n = db.execute(sql, {"pk": pkv})
        if n:
            flash(f"{ent['singular']} {pkv} deleted.", "success")
            show_sql(sql, {"pk": pkv})
        else:
            flash(f"{ent['singular']} {pkv} was not found.", "error")
    except oracledb.Error as e:
        msg, raw = db.friendly_error(e)
        flash(f"Could not delete {ent['singular'].lower()} {pkv}. {msg}", "error")
        flash(raw, "oracle")
    return redirect(url_for("entity_list", key=key))


# ================================================================ reports

@app.route("/reports")
@login_required
def reports():
    key = request.args.get("run") or REPORTS[0]["key"]
    rep = REPORTS_BY_KEY.get(key)
    if not rep:
        abort(404)
    cols, rows, error = [], [], None
    try:
        cols, rows = db.query_with_cols(rep["sql"])
    except oracledb.Error as e:
        error = db.friendly_error(e)[1]

    groups = {}
    for r in REPORTS:
        groups.setdefault(r["group"], []).append(r)

    owners = db.query("SELECT owner_id, owner_name FROM farm_owner ORDER BY owner_id")
    return render_template("reports.html", groups=groups, rep=rep, cols=cols,
                           rows=rows, error=error, owners=owners)


@app.route("/reports/raise-rent", methods=["POST"])
@admin_required
def raise_rent():
    owner = request.form.get("owner_id", "")
    try:
        pct = float(request.form.get("percent", ""))
    except ValueError:
        flash("Enter a percentage.", "error")
        return redirect(url_for("reports", run="hv-rent"))
    try:
        n = db.call_procedure_out("sp_raise_rent", [owner, pct])
        flash(f"sp_raise_rent: {int(n or 0)} lease(s) of {owner} raised by {pct:g}%.", "success")
    except oracledb.Error as e:
        msg, raw = db.friendly_error(e)
        flash(msg, "error")
        flash(raw, "oracle")
    return redirect(url_for("reports", run="jn-owner"))


# ================================================================ errors

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="That page does not exist."), 404


@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", code=400, message=e.description), 400


@app.errorhandler(oracledb.Error)
def db_error(e):
    return render_template("error.html", code=500,
                           message="Database error: " + db.friendly_error(e)[1]), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    print(f"\n  Irrigation app running at http://localhost:{port}\n")
    app.run(host="127.0.0.1", port=port, debug=os.getenv("FLASK_DEBUG") == "1")

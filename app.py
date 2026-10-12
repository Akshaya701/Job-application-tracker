import csv
import io
import os
import secrets
import sqlite3
from datetime import date
from functools import wraps

from flask import (
    Flask, abort, flash, make_response, redirect, render_template,
    request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "jobs.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE", "0") == "1"

# Set TRACKER_PASSWORD before running if you want login protection.
# Local default is intentionally documented for convenience; change it before public deployment.
TRACKER_USERNAME = os.environ.get("TRACKER_USERNAME", "admin")
TRACKER_PASSWORD = os.environ.get("TRACKER_PASSWORD", "change-me-now")
TRACKER_PASSWORD_HASH = generate_password_hash(TRACKER_PASSWORD)

STATUSES = [
    "Wishlist", "Applied", "Online Assessment", "Interview",
    "Offer", "Rejected", "Withdrawn"
]
PRIORITIES = ["Low", "Medium", "High"]


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                job_url TEXT DEFAULT '',
                location TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Wishlist',
                priority TEXT NOT NULL DEFAULT 'Medium',
                application_date TEXT DEFAULT '',
                deadline TEXT DEFAULT '',
                contact TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def protect_post_requests():
    if request.method == "POST":
        submitted = request.form.get("_csrf_token", "")
        expected = session.get("_csrf_token", "")
        if not expected or not secrets.compare_digest(submitted, expected):
            abort(400, description="Invalid or expired form token. Refresh and try again.")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def clean_text(value, max_length):
    return (value or "").strip()[:max_length]


def validate_application(form):
    data = {
        "company": clean_text(form.get("company"), 120),
        "role": clean_text(form.get("role"), 120),
        "job_url": clean_text(form.get("job_url"), 500),
        "location": clean_text(form.get("location"), 120),
        "status": clean_text(form.get("status"), 40),
        "priority": clean_text(form.get("priority"), 20),
        "application_date": clean_text(form.get("application_date"), 10),
        "deadline": clean_text(form.get("deadline"), 10),
        "contact": clean_text(form.get("contact"), 160),
        "notes": clean_text(form.get("notes"), 3000),
    }
    errors = []
    if not data["company"]:
        errors.append("Company is required.")
    if not data["role"]:
        errors.append("Job role is required.")
    if data["status"] not in STATUSES:
        errors.append("Choose a valid application status.")
    if data["priority"] not in PRIORITIES:
        errors.append("Choose a valid priority.")
    for field in ("application_date", "deadline"):
        if data[field]:
            try:
                date.fromisoformat(data[field])
            except ValueError:
                errors.append(f"{field.replace('_', ' ').title()} must be a valid date.")
    if data["job_url"] and not data["job_url"].startswith(("https://", "http://")):
        errors.append("Job link must start with http:// or https://.")
    return data, errors


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if secrets.compare_digest(username, TRACKER_USERNAME) and check_password_hash(TRACKER_PASSWORD_HASH, password):
            session.clear()
            session["authenticated"] = True
            session["_csrf_token"] = secrets.token_urlsafe(32)
            flash("Welcome back. Your tracker is ready.", "success")
            target = request.args.get("next", "")
            if not target.startswith("/") or target.startswith("//"):
                target = url_for("dashboard")
            return redirect(target)
        flash("Incorrect username or password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    search = clean_text(request.args.get("q"), 100)
    status = clean_text(request.args.get("status"), 40)
    if status and status not in STATUSES:
        status = ""

    where = []
    params = []
    if search:
        pattern = f"%{search}%"
        where.append("(company LIKE ? OR role LIKE ? OR location LIKE ? OR notes LIKE ?)")
        params.extend([pattern, pattern, pattern, pattern])
    if status:
        where.append("status = ?")
        params.append(status)
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM applications" + where_sql +
            " ORDER BY CASE WHEN deadline = '' THEN 1 ELSE 0 END, deadline ASC, updated_at DESC",
            params
        ).fetchall()
        stats = {
            "total": db.execute("SELECT COUNT(*) FROM applications").fetchone()[0],
            "interviews": db.execute("SELECT COUNT(*) FROM applications WHERE status = 'Interview'").fetchone()[0],
            "offers": db.execute("SELECT COUNT(*) FROM applications WHERE status = 'Offer'").fetchone()[0],
            "rejected": db.execute("SELECT COUNT(*) FROM applications WHERE status = 'Rejected'").fetchone()[0],
            "active": db.execute("SELECT COUNT(*) FROM applications WHERE status IN ('Applied', 'Online Assessment', 'Interview')").fetchone()[0],
        }
    return render_template(
        "dashboard.html", applications=rows, stats=stats, statuses=STATUSES,
        selected_status=status, search=search
    )


@app.route("/applications/new", methods=["GET", "POST"])
@login_required
def create_application():
    data = {
        "company": "", "role": "", "job_url": "", "location": "",
        "status": "Wishlist", "priority": "Medium", "application_date": "",
        "deadline": "", "contact": "", "notes": ""
    }
    if request.method == "POST":
        data, errors = validate_application(request.form)
        if errors:
            for error in errors:
                flash(error, "error")
        else:
            with get_db() as db:
                db.execute("""
                    INSERT INTO applications
                    (company, role, job_url, location, status, priority,
                     application_date, deadline, contact, notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, tuple(data[key] for key in (
                    "company", "role", "job_url", "location", "status", "priority",
                    "application_date", "deadline", "contact", "notes"
                )))
            flash("Application added successfully.", "success")
            return redirect(url_for("dashboard"))
    return render_template("application_form.html", item=data, statuses=STATUSES,
                           priorities=PRIORITIES, page_title="Add application", submit_label="Save application")


@app.route("/applications/<int:application_id>")
@login_required
def application_detail(application_id):
    with get_db() as db:
        item = db.execute("SELECT * FROM applications WHERE id = ?", (application_id,)).fetchone()
    if item is None:
        abort(404)
    return render_template("application_detail.html", item=item)


@app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
@login_required
def edit_application(application_id):
    with get_db() as db:
        existing = db.execute("SELECT * FROM applications WHERE id = ?", (application_id,)).fetchone()
    if existing is None:
        abort(404)
    item = dict(existing)
    if request.method == "POST":
        item, errors = validate_application(request.form)
        if errors:
            for error in errors:
                flash(error, "error")
        else:
            with get_db() as db:
                db.execute("""
                    UPDATE applications SET company=?, role=?, job_url=?, location=?,
                    status=?, priority=?, application_date=?, deadline=?, contact=?,
                    notes=?, updated_at=CURRENT_TIMESTAMP WHERE id=?
                """, tuple(item[key] for key in (
                    "company", "role", "job_url", "location", "status", "priority",
                    "application_date", "deadline", "contact", "notes"
                )) + (application_id,))
            flash("Application updated.", "success")
            return redirect(url_for("application_detail", application_id=application_id))
    return render_template("application_form.html", item=item, statuses=STATUSES,
                           priorities=PRIORITIES, page_title="Edit application", submit_label="Save changes")


@app.route("/applications/<int:application_id>/delete", methods=["POST"])
@login_required
def delete_application(application_id):
    with get_db() as db:
        result = db.execute("DELETE FROM applications WHERE id = ?", (application_id,))
    if result.rowcount == 0:
        abort(404)
    flash("Application deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/export.csv")
@login_required
def export_csv():
    with get_db() as db:
        rows = db.execute("""
            SELECT company, role, job_url, location, status, priority,
                   application_date, deadline, contact, notes, created_at, updated_at
            FROM applications ORDER BY updated_at DESC
        """).fetchall()
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["Company", "Role", "Job URL", "Location", "Status", "Priority",
                     "Application Date", "Deadline", "Contact", "Notes", "Created At", "Updated At"])
    writer.writerows([tuple(row) for row in rows])
    response = make_response("\ufeff" + output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=job_applications.csv"
    return response


@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, message=getattr(error, "description", "Bad request.")), 400


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", code=404, message="The page or application you requested was not found."), 404


init_db()

if __name__ == "__main__":
    # Debug mode is intentionally disabled by default.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)

# Job Application Tracker

A personal job-search tracker built with Python, Flask, SQLite, Jinja templates, and CSS. It is designed to run locally without any AWS services.

## Features

- Dashboard counts for total applications, active applications, interviews, and offers
- Create, view, edit, and delete job records
- Track company, role, job posting URL, location, status, priority, application date, deadline, contact, and notes
- Search by company, role, location, and notes; filter by status
- Export all records to CSV
- SQLite persistence
- Basic single-user login, session cookies, CSRF tokens for POST forms, parameterized SQL queries, and server-side input validation
- Responsive layout

## Requirements

- Python 3.10 or newer recommended
- pip
- A browser

## Run locally (Windows PowerShell)

1. Extract the project ZIP.
2. Open the extracted `job_application_tracker` folder in VS Code.
3. Open Terminal > New Terminal and run:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:TRACKER_USERNAME = "admin"
$env:TRACKER_PASSWORD = "replace-with-a-strong-local-password"
$env:SECRET_KEY = "replace-with-a-long-random-secret"
python app.py
```

4. Open <http://127.0.0.1:5000>.
5. Sign in using the username and password set in the terminal.

If PowerShell prevents activation, use Command Prompt:

```bat
py -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
set TRACKER_USERNAME=admin
set TRACKER_PASSWORD=replace-with-a-strong-local-password
set SECRET_KEY=replace-with-a-long-random-secret
python app.py
```

Then run `python app.py` and visit `http://127.0.0.1:5000`.

### Default login warning

If no environment variables are set, the local development default is `admin` / `change-me-now`. Change it before use and **never expose the application publicly with the default password or development secret**.

The database file `jobs.db` is created automatically in the project directory. Back it up before deleting or moving the project. The database is intentionally excluded from Git.


## Project structure

job_application_tracker/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── application_form.html
│   ├── application_detail.html
│   └── error.html
└── static/
    └── style.css


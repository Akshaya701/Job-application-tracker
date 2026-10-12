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

## Quick test checklist

- Sign in and confirm the dashboard opens.
- Add a sample application and confirm it appears.
- Open the detail page and edit the record.
- Search for the company name and filter by status.
- Export CSV and open the file.
- Delete the sample record and confirm it disappears.
- Stop and restart the app; confirm the remaining records persist.

## Deploying to AWS without surprise charges

**Local use costs $0 in AWS charges because it uses no AWS resources.** Deploying a Flask app to AWS is not automatically free just because an AWS account already exists.

Before creating any AWS resources:
1. Sign in to the AWS Console and check **Billing and Cost Management** for current credits, Free Tier eligibility, and current usage.
2. Check the specific service's pricing page and whether the account's offer covers that service and region.
3. Create a small AWS Budget alert, if available to your account. A budget alert is a notification, not a hard spending cap.
4. Do not create EC2, Lightsail, App Runner, RDS, load balancers, NAT gateways, or other billable resources unless you have verified the expected cost.

### Optional EC2 deployment (only if the console confirms suitable free eligibility/credits)

These are general steps; the actual cost depends on your account offer, region, instance type, disk, public IPv4 address, data transfer, and how long resources run.

1. In the AWS Console, confirm EC2 is covered by your current offer in your selected region.
2. Launch an eligible Linux instance only after reviewing the cost estimate. Restrict SSH (port 22) to your own IP address.
3. Connect using SSH and install Python, pip, and a virtual environment using the distribution's package manager.
4. Copy the project to the instance (for example, using `scp`) or clone your repository.
5. Create a virtual environment, install `requirements.txt`, and set strong `TRACKER_USERNAME`, `TRACKER_PASSWORD`, and `SECRET_KEY` values in the server environment.
6. Run behind a production WSGI server such as Gunicorn and configure a reverse proxy and HTTPS before public use. Do not use Flask's built-in development server for production.
7. Restrict inbound traffic. Never open SSH to the entire internet. Do not store real personal or recruiter data until authentication, HTTPS, backups, and deployment hardening have been reviewed.
8. When finished, stop and terminate resources you no longer need, delete unattached volumes and unused public IPs, and check the billing dashboard again. Stopping an instance may not stop storage or public IPv4 charges.

### Important deployment limitation

This project is a small local prototype. It uses SQLite on the same machine and a simple single-user password configured through environment variables. For a public or multi-user production deployment, add proper user management, secure secret management, HTTPS, database backups, rate limiting, stronger session controls, and deployment monitoring. The code has not been deployed to AWS as part of this package.

## Project structure

```text
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
```

## Resume bullet (use only after you run and verify it)

**Job Application Tracker | Python, Flask, SQLite, HTML/CSS**
- Built a web application to organize job applications, interview stages, priorities, and deadlines.
- Implemented CRUD operations, status-based filtering, search, CSV export, and persistent SQLite storage.
- Added single-user login, CSRF form tokens, and server-side input validation.

Do not claim AWS deployment until you have actually deployed and tested the application on AWS.

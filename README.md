# CivicShield — DCC Police Complaint & Location Assistance Prototype

A student project demonstrating a complaint-management workflow with citizen accounts, role-restricted officer actions, optional browser location sharing, case-status tracking, and a clearly labelled *demonstration* FIR record.

> **Important:** This is an academic prototype, not an official police service. Do not enter real personal, criminal, medical, or emergency information. The generated `DEMO-FIR-*` values are not official FIR numbers. The app does not secretly track people and is not connected to police systems.

## Included features

- Citizen registration and sign-in with password hashing.
- Role-based access: citizen versus officer/admin.
- Citizen can see only their own complaints.
- Complaint reference generation and status tracking.
- Optional browser geolocation with permission; user can select a point on the map.
- Location is stored only when the complaint form is submitted.
- Officer dashboard and status updates.
- Officer-only demonstration FIR record workflow.
- CSRF protection on form submissions.
- SQLite for easy local setup; optional MySQL configuration.
- Docker Compose file for a containerized app + MySQL development environment.

## Requirements

- Windows 10/11
- Python 3.13 (already installed for this project)
- VS Code recommended
- Internet connection for Google Fonts and Leaflet/OpenStreetMap tiles
- MySQL is **not required** for local first run; SQLite is the default.

## Local Windows setup (recommended first)

Open Command Prompt in this project folder.

1. Create and activate a virtual environment if you have not already:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```
2. Install packages:
   ```cmd
   python -m pip install -r requirements.txt
   ```
3. Copy environment example:
   ```cmd
   copy .env.example .env
   ```
   For local demo only, the default secret works but should be changed before any shared deployment.
4. Initialize database:
   ```cmd
   python -m flask --app app init-db
   ```
5. Start the app:
   ```cmd
   python app.py
   ```
6. Open `http://127.0.0.1:5000`.

Location permission works on localhost in supported browsers. Users must grant permission; there is no covert background tracking.

## Create an officer account

In a second Command Prompt window, navigate to the project folder and activate the same virtual environment. Then run:

```cmd
python -m flask --app app create-officer
```

Enter a display name, email, and a strong password when prompted. Do not create an officer account by changing a public registration form; public registration creates citizen accounts only.

## MySQL option (after the SQLite demo works)

1. Create a database and a least-privilege database user in MySQL.
2. Copy `.env.example` to `.env`.
3. Set `DATABASE_URL` in `.env`:
   ```text
   DATABASE_URL=mysql+pymysql://dcc_user:YOUR_URL_ENCODED_PASSWORD@127.0.0.1:3306/dcc_police
   ```
4. Set a long random `SECRET_KEY`.
5. Re-run `python -m flask --app app init-db`.

Use URL-encoding for special characters in database passwords. Never share `.env` or commit it to GitHub.

## Docker Compose (optional)

Install Docker Desktop first. Set non-default passwords and a secret in your environment or `.env`, then run:

```cmd
docker compose up --build
```

Open `http://127.0.0.1:5000`. The compose file is a local learning setup, not a production deployment. For a real distributed cloud demonstration, deploy multiple stateless app instances behind a load balancer, use managed database services, secure secrets, TLS, monitoring, backups, and a documented recovery plan.

## Folder structure

```text
DCC_Police_System/
├── app.py
├── extensions.py
├── models.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── run_windows.bat
├── models/
├── services/
├── instance/
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   ├── auth/
│   ├── complaints/
│   └── errors/
└── static/
    ├── css/style.css
    └── js/location.js
```

The `models.py` module at the project root contains the current database models; the `models/` folder is reserved for later modularization.

## DCC expansion roadmap

This initial version is a working web-app foundation, not a complete distributed production system. Recommended next stages:

1. Add audit-event records for officer actions.
2. Add complaint assignment and status history.
3. Add notifications with a queue worker.
4. Separate notifications and report processing into independent services.
5. Containerize services and deploy multiple app instances behind a load balancer.
6. Add cloud monitoring, backups, automated tests, rate limiting, security review, and data-retention rules.

## Known limitations

- The FIR feature creates a sample record only. It does not create a legally valid or official FIR.
- File evidence uploads are not implemented in this starter version.
- Map tiles and fonts require internet access.
- This starter app is for local learning; it has not undergone a security audit and must not be used for real police operations.

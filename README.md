# LoanHub - Professional Digital Lending & Fintech Platform

LoanHub (formerly LoanSphere) is a full-stack digital lending and loan portfolio management platform designed with modern user interface aesthetics, security hardening controls, and a robust backend state machine.

---

## 🚀 Key Features

- **Standardized Flask Blueprint Architecture**: Code is split cleanly across controllers (`app/routes`), models (`app/models`), services (`app/services`), and utilities (`app/utils`).
- **State Machine Loan Lifecycle**: Applications transition securely through `SUBMITTED` ➔ `UNDER_REVIEW` ➔ `DOCUMENT_VERIFICATION` ➔ `ELIGIBILITY_CHECK` ➔ `APPROVED`/`REJECTED` ➔ `SANCTIONED` ➔ `DISBURSED` ➔ `ACTIVE` ➔ `REPAYMENT` ➔ `CLOSED` with transition restrictions.
- **Credit Eligibility Assessment Engine**: Evaluates applicant FOIR (Fixed Obligation to Income Ratio), age thresholds, income boundaries, and debt capacities.
- **Decimal-Safe EMI & Amortization Engine**: Authoritative Python `Decimal` financial calculator that generates schedules and monthly breakdowns. Supports promotional zero-interest programs.
- **Secure File upload controls**: Validates file MIME types, enforces size limits (max 10MB), sanitizes filenames, and restricts access to owners and admins.
- **Automated Schema Migrations**: DB schema management utilizing `Flask-Migrate` (Alembic) and separate standalone database seeding.
- **CI/CD Integration**: GitHub Actions workflow verifying styling (Ruff), security vulnerabilities (Bandit), and test coverage (Pytest).

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, Flask
- **ORM & DB**: SQLAlchemy, Flask-Migrate (Alembic), support for SQLite, MySQL, and PostgreSQL
- **Frontend**: HTML5, Vanilla CSS3, Javascript (ES6), Jinja2 Templates, Bootstrap 5.3
- **PDF Generation**: ReportLab
- **Security**: Flask-WTF CSRF Protection, Werkzeug Password Hashing, RBAC (Role-Based Access Control)
- **Deployment**: Gunicorn, WhiteNoise, Render Blueprint (`render.yaml`)

---

## 📁 Project Structure

```
LoanHub/
├── app/
│   ├── models/            # SQLAlchemy database models
│   │   ├── user.py        # Credentials and password verification
│   │   ├── loan.py        # LoanType, LoanApplication, LoanStatusHistory
│   │   ├── emi.py         # EMI history
│   │   ├── interest_rate.py # Scheme rate matrix
│   │   ├── repayment.py   # Repayment transactions
│   │   ├── document.py    # Document upload registry
│   │   └── ...
│   ├── routes/            # Request routers
│   │   ├── auth.py        # Registration and profile
│   │   ├── main.py        # Customer views, calculator, document retrieval
│   │   └── admin.py       # Admin verification panel
│   ├── services/          # Pure business logic layers
│   │   ├── loan_service.py # State machine rules
│   │   ├── emi_service.py  # Decimal financial engine
│   │   ├── eligibility_service.py # FOIR and age limits assessor
│   │   ├── notification_service.py # Alert dispatcher
│   │   └── pdf_service.py  # Receipt generator
│   └── utils/             # Helpers
│       ├── decorators.py  # RBAC role checks
│       ├── validators.py  # File security and PAN/Aadhar regex
│       └── extensions.py  # Flask extensions init
│
├── migrations/            # Alembic schema version tracking
├── scripts/
│   └── seed.py            # Development database seeder
├── tests/                 # Automated test suite
├── config.py              # Environment configuration loader
├── run.py                 # Root WSGI entry point
├── Procfile               # Gunicorn startup configuration
├── render.yaml            # Render Blueprint spec
└── README.md              # Documentation
```

---

## 🔒 Security Hardening

- **Data Isolation**: Multi-tenant isolation verifies that customer queries filter strictly by `current_user.id` on document downloads and receipts.
- **RBAC**: Access to the admin dashboard and operations is locked with `@admin_required`, aborting with a `403 Forbidden` for unauthorized requests.
- **XSS & SQLi Protection**: Enforced by SQLAlchemy parameter binding and Jinja2 automatic escaping.
- **CSRF Protection**: Universal CSRF checks enabled, with AJAX fetch headers validated using `X-CSRFToken` tokens.
- **Session Security**: Cookies are flagged `HttpOnly`, `SameSite=Lax`, and `Secure=True` in production.

---

## ⚙️ Local Development Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Configurations
Copy the example environment file:
```bash
cp .env.example .env
```
Provide your secrets (`DATABASE_URL`, `SECRET_KEY`, and SMTP details). If no `DATABASE_URL` is configured, it falls back to creating `database/loansphere.db` SQLite locally in development.

### 3. Run Database Migrations & Seeding
Initialize the database tables and populate mock interest rates, faqs, and logins:
```bash
python -m flask db upgrade
python scripts/seed.py
```
This registers two default logins for testing:
- **System Admin**: `admin1@loansphere.bank` (Password: `adminPass1!`)
- **Customer User**: `user1@gmail.com` (Password: `userpass123`)

### 4. Start the Application
Launch the server:
```bash
python run.py
```
The app runs at **[http://localhost:5000](http://localhost:5000)**.

---

## 🧪 Testing Suite

Run the full pytest suite:
```bash
python -m pytest
```

Execute Ruff lint checking:
```bash
python -m ruff check app/
```

Run Bandit security scanner:
```bash
python -m bandit -r app/
```

---

## 🚀 Render Production Deployment

1. Push your repository to GitHub.
2. Go to **Render Dashboard** -> **New +** -> **Blueprint**.
3. Link this repository. Render automatically reads `render.yaml` to deploy your Gunicorn web app, execute `flask db upgrade` migrations on startup, and secure env credentials.

---

## ⚠️ Demo Disclaimer
This application is a demo lending and fintech portfolio project. It is **NOT** a real banking platform. All credit scoring, eligibility checks, and transaction executions are simulated.

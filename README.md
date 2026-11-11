# NutriTrack — Integrated Full-Stack Project

[![Python Tests](https://img.shields.io/badge/pytest-20%20passed-brightgreen.svg)](tests/)
[![Architecture](https://img.shields.io/badge/Architecture-Modular%20Monolith-blue.svg)](docs/system_design.md)
[![Database](https://img.shields.io/badge/RDBMS-3NF%20Compliant-orange.svg)](database/schema.sql)
[![Cloud](https://img.shields.io/badge/Cloud-Microsoft%20Azure-0078D4.svg)](docs/dp900_data_classification_and_azure.md)
[![Security](https://img.shields.io/badge/Security-RBAC%20%7C%20STRIDE%20%7C%20Audit-red.svg)](docs/threat_model_and_security_checklist.md)

NutriTrack is an enterprise-grade wellness and nutrition tracking web application built to fulfill the **Integrated Full-Stack Project** curriculum combining **System Design**, **RDBMS**, **DP-900 (Azure Data Fundamentals)**, and **Cloud Security**.

---

## 4-Subject Syllabus Mapping

| Subject (20 Marks Each) | Core Deliverables in Repository | Documentation & Code Reference |
|---|---|---|
| **System Design** | • Functional & Non-Functional Requirements<br>• High-level Component & Data Flow Architecture<br>• Complete API Endpoint Catalog<br>• Written Trade-Off Analysis (Monolith vs. Microservices, SSR vs. SPA) | [`docs/system_design.md`](docs/system_design.md)<br>Architecture Diagram |
| **RDBMS** | • Schema in Third Normal Form (3NF) with 12 related tables<br>• Primary, Foreign Keys with `ON DELETE CASCADE / RESTRICT`<br>• `CHECK` constraints on all numeric fields<br>• Multi-table JOINs, 2 Views, 1 Trigger, 1 Stored Procedure<br>• Explicit ACID Transactions with Rollback handling<br>• B-Tree Indexes on searched columns | [`database/schema.sql`](database/schema.sql)<br>[`database/queries.sql`](database/queries.sql)<br>[`docs/rdbms_design.md`](docs/rdbms_design.md)<br>ER Diagram (`Nutri Tracker ER Diagram.jpg`) |
| **DP-900 (Azure Data)** | • Data Classification: Structured, Semi-Structured, Unstructured<br>• Relational database hosted on Azure Database for PostgreSQL<br>• Cloud Non-Relational Store: Azure Blob Storage (`nutrition-reports`)<br>• Semi-structured JSON document export for Cosmos DB ingestion<br>• Power BI Star Schema model & 7/30-day analytics view | [`docs/dp900_data_classification_and_azure.md`](docs/dp900_data_classification_and_azure.md)<br>[`app/core/azure_blob.py`](app/core/azure_blob.py)<br>Reports View (`/reports`) |
| **Cloud Security** | • Role-Based Access Control (RBAC): `user` and `admin` roles<br>• PBKDF2-HMAC-SHA256 password hashing with salt<br>• HTTPS & Secure Session Cookies (`HttpOnly`, `SameSite=Lax`, `Secure`)<br>• Secrets kept out of repo via `.env` and Azure Key Vault<br>• OWASP Top 10 defense: SQLi (SQLAlchemy ORM) & XSS prevention<br>• Database firewall & VNet rule configuration<br>• Tamper-evident `activity_log` with IP tracking | [`docs/threat_model_and_security_checklist.md`](docs/threat_model_and_security_checklist.md)<br>Threat Model (`threat model nutri.png`) |

---

## Evaluation Test Logins (Role-Based Access)

The application automatically seeds pre-configured test accounts for each role upon first launch:

| Role | Email Address | Password | Permissions & Available Features |
|---|---|---|---|
| **Regular User** | `user@nutritrack.com` | `User123!` | Dashboard, Meal Logging, Hydration, Goals, 7/30-Day Analytics, CSV/JSON Reports, Cloud Archival |
| **Administrator** | `admin@nutritrack.com` | `Admin123!` | Full user features **+** Administrative Console (`/admin`), Food Catalog Management, Security Activity & Audit Logs |

---

## Quickstart: Local Setup & Launch

### Prerequisites
- Python 3.10+ (tested on Python 3.10, 3.12, 3.14)
- Git

### 1. Clone & Navigate to Repository
```powershell
git clone https://github.com/Sha-mbhavi/Nutri-tracker.git
cd Nutri-tracker
```

### 2. Create and Activate Virtual Environment
```powershell
# Windows
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### 4. Configure Environment
```powershell
Copy-Item .env.example .env
```

### 5. Launch the Web Application
```powershell
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.  
The SQLite development database is created automatically in the `instance/` folder with seeded food catalog items, test users, sample meals, goals, and activity logs.

---

## Running the Automated Test Suite

Run pytest to execute the full test suite (functional, security, RBAC, DP-900 exports, data calculation):

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Expected output:
```text
tests/test_app.py::test_registration_hashes_password PASSED
tests/test_app.py::test_protected_dashboard_requires_login PASSED
tests/test_app.py::test_registration_and_meal_calculation PASSED
...
tests/test_architecture_and_security.py::test_rbac_admin_access_control PASSED
tests/test_architecture_and_security.py::test_failed_login_activity_logging PASSED
tests/test_architecture_and_security.py::test_dp900_semi_structured_json_export PASSED
tests/test_architecture_and_security.py::test_dp900_blob_storage_archival PASSED

============================== 20 passed in 1.48s ==============================
```

---

## Running Database SQL Scripts

Execute and verify the 3NF schema and SQL queries:

```powershell
# Execute the DDL schema
sqlite3 instance/nutritrack.db < database/schema.sql

# Execute multi-table joins, transactions, views, and index verification
sqlite3 instance/nutritrack.db < database/queries.sql
```

---

## Cloud Deployment (Microsoft Azure)

To deploy NutriTrack to Microsoft Azure:

1. **Azure Database for PostgreSQL Flexible Server:**
   - Create Flexible Server in your resource group.
   - Configure Firewall: allow Azure Services and your client IP.
   - Run `database/schema.sql` to initialize the 3NF schema.

2. **Azure Blob Storage:**
   - Create Storage Account `nutritrackstorage`.
   - Create private container `nutrition-reports`.
   - Obtain Connection String and add to Azure Key Vault.

3. **Azure App Service (Linux Web App):**
   - Runtime: Python 3.10.
   - Application Settings:
     - `SECRET_KEY`: `<secure-random-key>`
     - `DATABASE_URL`: `postgresql://<user>:<password>@<host>:5432/nutritrack?sslmode=require`
     - `SESSION_COOKIE_SECURE`: `true`
     - `AZURE_STORAGE_CONNECTION_STRING`: `<connection-string>`
   - Deploy using GitHub Actions or Azure CLI:
     ```bash
     az webapp up --name nutritrack-app --resource-group nutritrack-rg --runtime "PYTHON:3.10"
     ```

---

## Project Documentation Index

- **Master Project Report:** [`docs/PROJECT_REPORT.md`](docs/PROJECT_REPORT.md)
- **System Design Document:** [`docs/system_design.md`](docs/system_design.md)
- **RDBMS Normalization & Schema Document:** [`docs/rdbms_design.md`](docs/rdbms_design.md)
- **DP-900 Data Classification & Azure Cloud Architecture:** [`docs/dp900_data_classification_and_azure.md`](docs/dp900_data_classification_and_azure.md)
- **Cloud Security Threat Model (STRIDE) & Checklist:** [`docs/threat_model_and_security_checklist.md`](docs/threat_model_and_security_checklist.md)
- **Schema Script:** [`database/schema.sql`](database/schema.sql)
- **Query File:** [`database/queries.sql`](database/queries.sql)
- **ER Diagram:** `Nutri Tracker ER Diagram.jpg`
- **Threat Model Diagram:** `threat model nutri.png`

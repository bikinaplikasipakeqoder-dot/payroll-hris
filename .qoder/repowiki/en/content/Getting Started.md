# Getting Started

<cite>
**Referenced Files in This Document**
- [requirements.txt](file://requirements.txt)
- [alembic.ini](file://alembic.ini)
- [env.py](file://alembic/env.py)
- [database.py](file://app/database.py)
- [base.py](file://app/models/base.py)
- [auth.py](file://app/models/auth.py)
- [employee.py](file://app/models/employee.py)
- [salary.py](file://app/models/salary.py)
- [payroll.py](file://app/models/payroll.py)
- [seed_data.py](file://app/seed/seed_data.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Environment Setup](#environment-setup)
5. [Initial Database Configuration](#initial-database-configuration)
6. [First Run](#first-run)
7. [Accessing API Endpoints](#accessing-api-endpoints)
8. [Initial System Configuration](#initial-system-configuration)
9. [Common Setup Issues and Solutions](#common-setup-issues-and-solutions)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [Conclusion](#conclusion)

## Introduction
This guide helps you quickly set up and run the Payroll system locally. It covers prerequisites, installation, environment configuration, database initialization with Alembic, and first-time usage. The system is built with FastAPI and SQLAlchemy, and uses SQLite by default for simplicity.

## Prerequisites
- Python 3.x: The project uses modern Python features and dependencies aligned with recent Python releases.
- SQL Fundamentals: Understanding of relational databases, tables, relationships, and migrations is helpful.
- Indonesian Payroll Regulations: The system includes built-in defaults aligned with Indonesian tax (PPh Pasal 17), BPJS contributions, and PTKP categories for 2024. Familiarity with these concepts will help you configure the system effectively.

## Installation
Follow these steps to install the project locally:

1. Clone or download the repository to your local machine.
2. Navigate to the project root directory.
3. Install dependencies using the provided requirements file:
   - Command: pip install -r requirements.txt
   - This installs FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic, python-dotenv, and other libraries.

**Section sources**
- [requirements.txt:1-14](file://requirements.txt#L1-L14)

## Environment Setup
Set up a Python virtual environment to isolate dependencies:

1. Create a virtual environment:
   - Command: python -m venv venv
2. Activate the environment:
   - On macOS/Linux: source venv/bin/activate
   - On Windows: venv\Scripts\activate
3. Install dependencies:
   - Command: pip install -r requirements.txt

Optional: Set environment variables for advanced configuration (see First Run section).

## Initial Database Configuration
By default, the system uses SQLite with a local file named payroll.db. The database URL is configurable via an environment variable.

Key configuration points:
- Default URL: sqlite:///./payroll.db
- Environment variable override: DATABASE_URL
- SQLite foreign key enforcement is enabled automatically.

Important note: Alembic migrations are configured to run offline and online modes with batch rendering for SQLite compatibility.

**Section sources**
- [database.py:17](file://app/database.py#L17)
- [database.py:27-32](file://app/database.py#L27-L32)
- [alembic.ini:30](file://alembic.ini#L30)
- [env.py:46](file://alembic/env.py#L46)

## First Run
Complete these steps to initialize the database and seed default data:

1. Apply Alembic migrations:
   - Command: alembic upgrade head
   - This creates all tables defined in the models and applies schema updates.
2. Seed the database with Indonesian payroll defaults:
   - Command: python -m app.seed.seed_data
   - This seeds roles, permissions, PTKP values, tax brackets, BPJS settings, overtime rules, languages, leave types, and tax settings for 2024.

After seeding, your database will contain:
- A default company record
- System roles and permissions
- Indonesian tax and social security settings for 2024
- Default configurations for attendance, leaves, and payroll processing

**Section sources**
- [env.py:76-80](file://alembic/env.py#L76-L80)
- [seed_data.py:27-63](file://app/seed/seed_data.py#L27-L63)
- [seed_data.py:432-448](file://app/seed/seed_data.py#L432-L448)

## Accessing API Endpoints
Once the database is initialized, you can start the development server and explore the API:

1. Start the development server:
   - Command: uvicorn main:app --reload
   - Replace main:app with the actual module path if your FastAPI app is defined elsewhere.
2. Open your browser or API client:
   - Swagger UI: http://127.0.0.1:8000/docs
   - Redoc: http://127.0.0.1:8000/redoc

Note: The server listens on localhost by default. If you need to change host/port, configure Uvicorn accordingly.

## Initial System Configuration
Configure the system for your organization:

1. Log in to the system using seeded roles (Administrator, Payroll Master, Operator, etc.) and update company settings:
   - Update company details (legal name, tax number, address, contact info)
   - Configure work week days and default payroll method
2. Define organizational structure:
   - Create departments and positions
   - Assign employees to departments and positions
3. Set up compensation:
   - Define employee grades and salary matrices
   - Create allowance and deduction types
4. Configure payroll settings:
   - Set tax settings (PPh Pasal 17)
   - Adjust BPJS contribution rates and limits
   - Define overtime multipliers and policies
5. Manage leaves and attendance:
   - Configure leave types and entitlements
   - Set up shifts and attendance tracking

## Common Setup Issues and Solutions
- Alembic upgrade fails with SQLite ALTER TABLE errors:
  - Ensure migrations are applied with batch rendering. Alembic is configured to use render_as_batch=True for SQLite compatibility.
  - Verify the target metadata includes all models.
- Database URL not taking effect:
  - Confirm DATABASE_URL environment variable is set before starting the server.
  - Check that the path is writable and accessible.
- Foreign keys not enforced:
  - SQLite foreign key enforcement is enabled via PRAGMA. If you switch to another database, ensure foreign key constraints are enabled at the database level.
- Missing default data after seeding:
  - Re-run the seed script to populate missing defaults (it is idempotent).
- Port already in use:
  - Change the port when starting Uvicorn (e.g., --port 8001).

## Troubleshooting Guide
- Database connectivity:
  - Verify DATABASE_URL points to a valid SQLite file or external database.
  - For external databases, ensure credentials and connection parameters are correct.
- Migration issues:
  - Check Alembic logs for errors during upgrade.
  - Confirm that all model classes are imported so Alembic’s target metadata includes them.
- Seeding failures:
  - Review the seed script output for any constraint violations or missing dependencies.
  - Ensure the database is migrated before seeding.

## Conclusion
You now have a fully functional local Payroll system with Indonesian payroll defaults pre-configured. Use the seeded data as a foundation and customize company settings, organizational structure, compensation plans, and policies to match your needs. Explore the API endpoints to integrate with clients or build administrative tools.
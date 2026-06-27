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
- [main.py](file://app/main.py)
- [config.py](file://app/config.py)
- [package.json](file://frontend/package.json)
- [next.config.ts](file://frontend/next.config.ts)
- [api.ts](file://frontend/src/lib/api.ts)
- [README.md](file://frontend/README.md)
- [vercel.json](file://vercel.json)
</cite>

## Update Summary
**Changes Made**
- Added comprehensive frontend setup instructions for Next.js application
- Updated development workflow to include both backend and frontend components
- Enhanced deployment configuration with Vercel integration
- Added environment variable configuration guidance
- Updated API endpoint access instructions with new routing structure

## Table of Contents
1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Environment Setup](#environment-setup)
5. [Backend Development Setup](#backend-development-setup)
6. [Frontend Development Setup](#frontend-development-setup)
7. [Initial Database Configuration](#initial-database-configuration)
8. [First Run](#first-run)
9. [Accessing API Endpoints](#accessing-api-endpoints)
10. [Initial System Configuration](#initial-system-configuration)
11. [Development Workflow](#development-workflow)
12. [Common Setup Issues and Solutions](#common-setup-issues-and-solutions)
13. [Troubleshooting Guide](#troubleshooting-guide)
14. [Conclusion](#conclusion)

## Introduction
This guide helps you quickly set up and run the Payroll system locally with both backend and frontend components. The system consists of a FastAPI backend serving an Indonesian payroll and HRIS platform, integrated with a Next.js frontend. It covers prerequisites, installation, environment configuration, database initialization with Alembic, and first-time usage with comprehensive development workflow instructions.

## Prerequisites
- Python 3.x: The project uses modern Python features and dependencies aligned with recent Python releases.
- Node.js 18+: Required for frontend development with Next.js framework.
- SQL Fundamentals: Understanding of relational databases, tables, relationships, and migrations is helpful.
- Indonesian Payroll Regulations: The system includes built-in defaults aligned with Indonesian tax (PPh Pasal 17), BPJS contributions, and PTKP categories for 2024. Familiarity with these concepts will help you configure the system effectively.

## Installation
Follow these steps to install the project locally:

1. Clone or download the repository to your local machine.
2. Navigate to the project root directory.
3. Install backend dependencies using the provided requirements file:
   - Command: pip install -r requirements.txt
   - This installs FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic, python-dotenv, and other libraries.
4. Navigate to the frontend directory:
   - Command: cd frontend
5. Install frontend dependencies:
   - Command: npm install
   - Alternative: yarn install or pnpm install

**Section sources**
- [requirements.txt:1-23](file://requirements.txt#L1-L23)
- [package.json:10-18](file://frontend/package.json#L10-L18)

## Environment Setup
Set up Python virtual environment for backend isolation:

1. Create a virtual environment:
   - Command: python -m venv venv
2. Activate the environment:
   - On macOS/Linux: source venv/bin/activate
   - On Windows: venv\Scripts\activate
3. Install backend dependencies:
   - Command: pip install -r requirements.txt

Set up Node.js environment for frontend:

1. Navigate to frontend directory:
   - Command: cd frontend
2. Install frontend dependencies:
   - Command: npm install

Optional: Create environment files for both backend and frontend:
- Backend: Create `.env` file with database configuration
- Frontend: Create `.env.local` file with API base URL

## Backend Development Setup
Configure the backend development environment:

1. Database configuration:
   - Default: SQLite with `payroll.db` file
   - Override: Set `DATABASE_URL` environment variable
   - Example: `DATABASE_URL=sqlite:///./payroll.db` or `DATABASE_URL=postgresql://user:password@localhost/dbname`

2. JWT configuration:
   - Set `JWT_SECRET_KEY` for authentication
   - Configure `JWT_ALGORITHM` and `JWT_EXPIRATION_MINUTES`

3. Debug configuration:
   - Set `DEBUG=True` for development
   - Configure `LOG_LEVEL` for logging verbosity

**Section sources**
- [config.py:4-18](file://app/config.py#L4-L18)
- [database.py:16-39](file://app/database.py#L16-L39)

## Frontend Development Setup
Configure the frontend development environment:

1. Application configuration:
   - Next.js version: 16.2.9
   - React version: 19.2.4
   - TypeScript support included

2. Development server:
   - Start command: `npm run dev`
   - Alternative commands: `yarn dev` or `pnpm dev`
   - Default port: 3000

3. API configuration:
   - Default API base URL: `http://localhost:8000`
   - Override via `NEXT_PUBLIC_API_URL` environment variable
   - Frontend automatically handles API errors and responses

4. Styling and UI:
   - Tailwind CSS configured
   - TypeScript types included
   - React Hook Form with Zod validation

**Section sources**
- [package.json:5-9](file://frontend/package.json#L5-L9)
- [next.config.ts:1-15](file://frontend/next.config.ts#L1-L15)
- [api.ts:1-2](file://frontend/src/lib/api.ts#L1-L2)

## Initial Database Configuration
The system supports multiple database backends with SQLite as default:

Key configuration points:
- Default URL: sqlite:///./payroll.db
- Environment variable override: DATABASE_URL
- SQLite foreign key enforcement is enabled automatically
- Support for Turso/libSQL with authentication token

Important note: Alembic migrations are configured to run offline and online modes with batch rendering for SQLite compatibility.

**Section sources**
- [database.py:16-51](file://app/database.py#L16-L51)
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

3. Start development servers:
   - Backend: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
   - Frontend: `npm run dev` (in frontend directory)

After seeding, your database will contain:
- A default company record
- System roles and permissions
- Indonesian tax and social security settings for 2024
- Default configurations for attendance, leaves, and payroll processing

**Section sources**
- [env.py:76-80](file://alembic/env.py#L76-L80)
- [seed_data.py:28-74](file://app/seed/seed_data.py#L28-L74)
- [main.py:67-76](file://app/main.py#L67-L76)

## Accessing API Endpoints
Once the database is initialized, you can start the development servers and explore the API:

1. Start the backend development server:
   - Command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   - The API is accessible at http://localhost:8000
2. Start the frontend development server:
   - Command: npm run dev (in frontend directory)
   - The frontend is accessible at http://localhost:3000
3. Open your browser or API client:
   - Swagger UI: http://localhost:8000/docs
   - Redoc: http://localhost:8000/redoc
   - Frontend dashboard: http://localhost:3000

Note: The backend server listens on all interfaces by default for development. The frontend server listens on localhost:3000.

**Section sources**
- [main.py:30-34](file://app/main.py#L30-L34)
- [README.md:5-15](file://frontend/README.md#L5-L15)

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

## Development Workflow
The system follows a Git-based development workflow with separate backend and frontend components:

### Backend Development
- FastAPI application with modular router structure
- Comprehensive API endpoints under `/api/v1` prefix
- Real-time database initialization and seeding on startup
- Support for multiple database backends (SQLite, PostgreSQL, Turso/libSQL)

### Frontend Development
- Next.js 16.2.9 with App Router
- TypeScript with strict typing
- Tailwind CSS for styling
- React Hook Form with Zod validation
- Responsive design with mobile-first approach

### Deployment Workflow
- Separate builds for backend (Python) and frontend (Next.js)
- Vercel deployment configuration with route mapping
- Environment variable management for production

**Section sources**
- [main.py:49-64](file://app/main.py#L49-L64)
- [vercel.json:3-22](file://vercel.json#L3-L22)

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
  - Change the port when starting Uvicorn (e.g., --port 8001) or frontend (e.g., --port 3001).
- Frontend dependencies not installing:
  - Clear npm cache: `npm cache clean --force`
  - Delete node_modules and reinstall: `rm -rf node_modules && npm install`
- API not connecting to frontend:
  - Ensure backend is running on port 8000
  - Set NEXT_PUBLIC_API_URL=http://localhost:8000 in frontend environment
- CORS issues in development:
  - Frontend allows all origins for development. Restrict in production.

## Troubleshooting Guide
- Database connectivity:
  - Verify DATABASE_URL points to a valid SQLite file or external database.
  - For external databases, ensure credentials and connection parameters are correct.
- Migration issues:
  - Check Alembic logs for errors during upgrade.
  - Confirm that all model classes are imported so Alembic's target metadata includes them.
- Seeding failures:
  - Review the seed script output for any constraint violations or missing dependencies.
  - Ensure the database is migrated before seeding.
- Frontend build issues:
  - Clear Next.js cache: `rm -rf .next`
  - Check TypeScript compilation errors
  - Verify all required environment variables are set
- API route conflicts:
  - All routes are prefixed with `/api/v1`
  - Check for conflicting route definitions in routers

## Conclusion
You now have a fully functional local Payroll system with both backend and frontend components, featuring Indonesian payroll defaults pre-configured. The system supports multiple database backends, includes comprehensive development workflow with Git-based migration, and provides separate backend and frontend development environments. Use the seeded data as a foundation and customize company settings, organizational structure, compensation plans, and policies to match your needs. Explore the API endpoints and frontend interface to integrate with clients or build administrative tools.
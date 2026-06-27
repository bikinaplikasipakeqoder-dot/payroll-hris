The repository employs a minimalist, script-free build and deployment approach typical of early-stage or lightweight Python applications. There are no dedicated build automation tools (such as `Makefile`, `pyproject.toml`, or `setup.py`), containerization definitions (`Dockerfile`), or CI/CD pipeline configurations (`.github/workflows`, `.gitlab-ci.yml`).

### Core Build & Dependency Management
- **Dependency Resolution**: Relies exclusively on a flat `requirements.txt` file listing direct dependencies (FastAPI, SQLAlchemy, Alembic, etc.). There is no lock file (e.g., `requirements-lock.txt` or `poetry.lock`), implying that builds are not strictly reproducible across environments without manual pinning.
- **Execution Model**: The application is designed to be run directly via the Python interpreter (e.g., `uvicorn app.main:app` or similar entry points not explicitly defined in a build script). Database initialization is handled programmatically via `app.database.init_db()` rather than through a build-step migration command.

### Schema Migration Strategy
- **Alembic Integration**: Database schema evolution is managed by **Alembic**, configured via `alembic.ini` and the `alembic/` directory.
- **Configuration**: The migration environment is set to use SQLite (`sqlite:///./payroll.db`) by default. Foreign key enforcement is enabled via SQLAlchemy event listeners in `app/database.py` (`PRAGMA foreign_keys=ON`), which is a critical runtime configuration for data integrity in SQLite.
- **Workflow**: Developers are expected to use standard Alembic CLI commands (`alembic revision --autogenerate`, `alembic upgrade head`) manually, as there are no wrapper scripts to automate this process.

### Deployment & CI/CD Absence
- **No Containerization**: The absence of `Dockerfile` or `docker-compose.yml` suggests that deployment is either manual (e.g., copying files to a server) or handled by an external platform that abstracts away the build process (e.g., Heroku, Render, or a custom internal platform not represented in the code).
- **No Automated Testing/CI**: There are no test runners (like `pytest.ini`) or CI configuration files visible. Quality assurance and integration testing are likely performed locally or are not yet formalized in the repository structure.

### Developer Conventions
1. **Manual Environment Setup**: Developers must manually create a virtual environment and install dependencies using `pip install -r requirements.txt`.
2. **Direct CLI Usage**: All operational tasks (migrations, server startup) are executed via direct CLI calls to `alembic` and `uvicorn`/`python`.
3. **SQLite-Centric Development**: The default configuration targets SQLite, simplifying local development but requiring careful attention to concurrency limitations if deployed in a multi-user environment without switching the `DATABASE_URL`.
This repository uses a standard Python dependency management approach centered around `pip` and a flat `requirements.txt` file. There is no evidence of advanced dependency management tools like Poetry, Pipenv, or Conda, nor are there any lockfiles (`requirements-lock.txt`, `Pipfile.lock`, `poetry.lock`) or vendoring strategies.

### System and Approach
- **Package Manager**: `pip` is the implied package manager, relying on the standard `requirements.txt` format.
- **Versioning Strategy**: Dependencies use minimum version constraints (e.g., `fastapi>=0.104.0`, `sqlalchemy>=2.0.0`). This allows for automatic minor/patch updates but may introduce instability if major breaking changes are released in dependent libraries.
- **Locking**: No lockfile is present. This means builds are not fully reproducible by default, as different installations may resolve to different compatible versions of sub-dependencies.

### Key Files
- **`requirements.txt`**: The single source of truth for third-party library declarations. It includes core web framework dependencies (`fastapi`, `uvicorn`), database ORM tools (`sqlalchemy`, `alembic`), authentication utilities (`python-jose`, `passlib`), and AI integration libraries (`langchain`, `openai`).
- **`alembic.ini`**: Configures the Alembic migration tool, specifying the script location and database URL. It does not manage Python package dependencies but relies on `sqlalchemy` being installed via `requirements.txt`.

### Architecture and Conventions
- **Flat Dependency List**: All dependencies, both direct and potentially indirect, are listed in a single flat file. There is no separation between production, development, and testing dependencies (e.g., no `requirements-dev.txt`).
- **Environment Configuration**: Database connectivity is managed via environment variables (`DATABASE_URL`) with a fallback to a local SQLite file (`payroll.db`), as seen in `app/database.py`. This suggests a simple deployment model, likely for development or small-scale production.
- **No Private Registry Configuration**: There are no files indicating the use of private PyPI registries (e.g., `.pip/pip.conf`, `ARTIFACTORY_URL` environment variables).

### Rules for Developers
1. **Adding Dependencies**: New libraries must be added manually to `requirements.txt` with an appropriate version constraint (preferably `>=` for minor/patch flexibility or `==` for strict pinning if stability is critical).
2. **Installation**: Run `pip install -r requirements.txt` to install all required packages.
3. **Reproducibility Warning**: Due to the lack of a lockfile, developers should be aware that dependency versions may drift between environments. For production, consider generating a lockfile using `pip freeze > requirements-lock.txt` after testing.
4. **Database Schema Changes**: Use Alembic for schema migrations. Ensure `alembic` is installed via `requirements.txt` and configure migrations in the `alembic/` directory.
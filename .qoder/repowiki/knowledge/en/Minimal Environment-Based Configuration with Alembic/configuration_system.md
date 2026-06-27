## Configuration System Overview

This repository uses a **minimal, environment-variable-driven configuration approach** typical of small-to-medium Python applications. There is no dedicated configuration management framework or centralized config module.

### What System/Approach Is Used

- **Environment variables**: The sole mechanism for runtime configuration, accessed via `os.environ.get()` with hardcoded defaults.
- **Alembic INI file**: Standard `alembic.ini` for database migration tooling configuration.
- **No dedicated config package**: No `config/` directory, no YAML/TOML/JSON config files, no Pydantic Settings usage despite `pydantic-settings` being listed in `requirements.txt`.

### Key Files and Packages

| File | Role |
|------|------|
| `app/database.py` | Defines `DATABASE_URL` via `os.environ.get("DATABASE_URL", "sqlite:///./payroll.db")`. This is the only application-level configuration point. |
| `alembic.ini` | Alembic migration tool configuration: sets `script_location`, `sqlalchemy.url` (hardcoded to `sqlite:///./payroll.db`), and logging levels. |
| `alembic/env.py` | Alembic runtime environment; reads from `alembic.ini` via `context.config` for migration execution. |
| `requirements.txt` | Lists `pydantic-settings>=2.0.0` and `python-dotenv>=1.0.0` as dependencies, but neither is actively used in the codebase. |

### Architecture and Conventions

1. **Single configuration variable**: Only `DATABASE_URL` is configurable at runtime. All other settings (SQLite PRAGMA behavior, connection pooling, echo mode) are hardcoded in `app/database.py`.
2. **Hardcoded defaults**: The fallback `sqlite:///./payroll.db` is embedded directly in source code, not externalized.
3. **Alembic URL duplication**: The database URL appears in two places — `alembic.ini` (line 30) and `app/database.py` (line 17) — creating a potential consistency risk. Changes must be made in both locations.
4. **No environment layering**: No `.env` file loading, no profile-based configs (dev/staging/prod), no secret management integration.
5. **Unused dependencies**: `pydantic-settings` and `python-dotenv` are declared but never imported or instantiated, suggesting planned but unimplemented configuration infrastructure.

### Rules Developers Should Follow

- **To change the database location**: Update `DATABASE_URL` in `app/database.py` AND `sqlalchemy.url` in `alembic.ini` to keep them synchronized.
- **To add new configuration**: Follow the existing pattern — use `os.environ.get("KEY", "default_value")` in the module where the setting is consumed. Do not create a centralized config module unless the project scales.
- **For secrets**: Currently there is no secret management. Sensitive values (if any are added later) should be passed via environment variables, never committed to source.
- **Avoid relying on `pydantic-settings` or `python-dotenv`**: These are listed in requirements but unused. If adopted, a migration plan would be needed to consolidate the scattered `os.environ` calls.

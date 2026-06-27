"""
FastAPI dependency injection utilities.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db


def get_database():
    """
    Alias for database session dependency.

    Usage:
        @router.get("/items")
        def read_items(db: Session = Depends(get_database)):
            ...
    """
    return Depends(get_db)


def get_current_user():
    """
    Placeholder for JWT authentication.

    TODO: Implement JWT token validation with python-jose.
    For now, returns a mock user context.
    """
    return {"user_id": 1, "company_id": 1, "role": "Administrator"}

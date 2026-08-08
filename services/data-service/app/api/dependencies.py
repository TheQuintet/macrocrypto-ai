from typing import Optional

from fastapi import Header


async def jwt_auth(
    authorization: Optional[str] = Header(default=None)
):
    """
    JWT integration point for future validation.
    """

    # JWT validation will be added in a future sprint.
    return authorization

from app.database.session import SessionLocal


def get_db():
    """
    Provide a database session for API requests.

    The session is automatically closed after
    the request completes.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
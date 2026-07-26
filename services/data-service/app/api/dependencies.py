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
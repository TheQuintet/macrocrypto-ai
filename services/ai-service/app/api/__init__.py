"""AI Service — HTTP API package.

This package contains the FastAPI routers and shared dependencies
used by the HTTP layer.

Structure:
    - dependencies: shared dependency-injection helpers
    - v1: version 1 API routers

Routers are registered in app/main.py via include_router().
"""
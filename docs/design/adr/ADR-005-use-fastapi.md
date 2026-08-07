# ADR-005: Use FastAPI for API Gateway

## Status

**Accepted**

---

## Context

We need a Python framework for the API Gateway. We considered FastAPI, Flask, and Django.

---

## Decision

**Use FastAPI** for the API Gateway.

---

## Rationale

| Reason | Explanation |
|--------|-------------|
| **Performance** | Async, fast (Starlette + Pydantic) |
| **Auto-Docs** | OpenAPI/Swagger generated automatically |
| **Validation** | Pydantic for request/response validation |
| **Async Support** | Native async/await for performance |
| **Type Hints** | Built-in Python type hints for better IDE support |

---

## Alternatives Considered

| Alternative | Why Rejected |
|-------------|--------------|
| **Flask** | Synchronous only, slower, no auto-docs |
| **Django** | Heavy, overkill for API-only |
| **Starlite** | Newer, less community support |

---

## Consequences

### Positive

- ✅ Automatic OpenAPI documentation
- ✅ Fast performance
- ✅ Great async support
- ✅ Built-in validation

### Negative

- ❌ Less mature than Flask
- ❌ Smaller ecosystem (but growing)

---

## Implementation Details

| Component | Technology |
|-----------|------------|
| Framework | FastAPI 0.110+ |
| Web Server | Uvicorn + Gunicorn |
| Serialization | Pydantic |
| Validation | Pydantic |
| Authentication | python-jose (JWT) |

---

## Related ADRs

- None

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-07 | Sid | Initial version |
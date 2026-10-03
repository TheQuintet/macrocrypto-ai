# Software Testing Report

## 1. Local & Development-Time Testing

*   **Service-Level Unit Tests:** During active development, developers run localized unit test suites using `pytest` for each individual service (`api-gateway`, `alert-service`, and `data-service`) in isolation.
*   **Early Defect Detection:** These tests allow for rapid verification of business logic, validation of helper functions, and mocking of external dependencies before code is committed or pushed to remote branches.

---

## 2. Automated Testing Frameworks & CI/CD Scope

*   **Comprehensive pytest Suites:** Automated test suites verify core functionalities, API contracts, and integration flows across all targeted microservices.
*   **Code Coverage Threshold (> 80%):** Enforced via `pytest-cov` to track and guarantee that code coverage across the `api-gateway`, `alert-service`, and `data-service` consistently surpasses 80%, maintaining high reliability and surfacing untested code paths.
*   **Dependency & State Verification:** For the `data-service`, tests successfully spin up and validate integrations with **RabbitMQ** and **Redis** during pipeline execution.
*   **Excluded Tests:** Explicitly bypassed resource-heavy data-preparation tests during standard CI runs to optimize pipeline speed and avoid external bottlenecks.

---

## 3. Infrastructure & Environment Management

*   **Isolated CI Service Containers:** Leveraged native **GitHub Actions** parallel service containers for **TimescaleDB**, **Redis**, and **RabbitMQ** to ensure clean, isolated states for every test run and prevent cross-test interference.
*   **Health-Check Gatekeeping:** Integrated database and broker diagnostic commands (`pg_isready`, `redis-cli ping`, and `rabbitmq-diagnostics`) to block `pytest` execution until all dependent infrastructure components are fully initialized and responsive.
*   **Uvicorn Background Server Integration:** Programmatically boots up a live **FastAPI** server instance on `127.0.0.1:8001` (with background logging suppressed) specifically for socket-dependent integration tests. The test runner pings the `/docs` endpoint to confirm server readiness before test execution, complete with automated process cleanup upon completion.
*   **Mocked Environment Configuration:** Explicitly mapped test environment variables—including `DATABASE_URL`, active connection ports, and mock third-party credentials like `FRED_API_KEY`—to prevent startup validation errors and guarantee deterministic test behavior.

---

## 4. Security Auditing & Vulnerability Management

*   **Static Dependency Scanning (pip-audit & Safety):** Integrated `pip-audit` into the GitHub Actions CI pipeline to systematically scan individual `requirements.txt` files across all microservices (`api-gateway`, `alert-service`, and `data-service`).
*   **Vulnerability Exception Handling:** Identified and managed `PYSEC-2026-1325`, a transitive `ecdsa` package vulnerability introduced via `python-jose`.
*   **Risk Justification & Bypass Control:** Documented that because full JWT authentication and token verification are not yet active within the API gateway, this signature-related side-channel vector remains unexposed. Applied an explicit `ignore-vulns` exception configuration with team documentation to keep CI passing while tracking a future migration path to `PyJWT`.
*   **CI/CD Pipeline Gatekeeping Flow:** Configured the `security-audit` job in GitHub Actions with dependency constraints (`needs`), ensuring that security audits execute automatically only after all microservice unit and integration test suites pass successfully.

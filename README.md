# Flock Energy — Urja Meter Ops API Wrapper

A read-only REST API adapter intended to expose smart-meter information from the legacy Urja Meter Ops portal as structured JSON.

> **Important implementation status:** This repository is a runnable API foundation. The assignment requires you to inspect the live portal and confirm its real login flow, internal API paths, parameters, and response structures. Values in `.env.example` for portal paths and form field names are placeholders, not verified facts. Complete `PROTOCOL.md` from your own DevTools observations before treating the integration as finished.

## Features

- FastAPI service with OpenAPI schema at `/openapi.json` and interactive docs at `/docs`.
- Adapter layer separated from API routes.
- HTTP client cookie persistence and session reuse.
- Basic re-login attempt when an HTML response appears to be a login page.
- JSON response parsing and HTML table extraction.
- Simple whitespace, boolean, and numeric normalization.
- Consistent upstream error responses.
- Small normalization test suite.

## Architecture

```text
Client
  |
  v
FastAPI routes (app/main.py)
  |
  v
Portal adapter (app/portal_client.py)
  |-- login/session cookies
  |-- requests to discovered portal paths
  v
Urja Meter Ops portal
  |
  v
JSON or HTML response
  |
  v
Normalization (app/normalization.py)
  |
  v
Clean JSON response
```

## Requirements

- Python 3.10+
- Internet access to the provided portal
- Git

## Setup on Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` locally. Put the supplied login credentials in `.env`; do not commit the file. Verify all portal paths, form field names, CSRF requirements and success/failure indicators in browser DevTools.

## Run

```powershell
uvicorn app.main:app --reload
```

Open:
- Health check: http://127.0.0.1:8000/health
- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Local service health |
| POST | `/api/v1/auth/login` | Create/refresh the portal session |
| GET | `/api/v1/meters` | List meters |
| GET | `/api/v1/meters/{meter_id}` | Meter details |
| GET | `/api/v1/meters/{meter_id}/consumption` | Consumption history |
| GET | `/api/v1/hierarchy` | Optional network hierarchy |

These are the wrapper's intended public routes. The upstream paths are configured separately and must be verified.

## Example requests

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/api/v1/auth/login
curl http://127.0.0.1:8000/api/v1/meters
curl http://127.0.0.1:8000/api/v1/meters/METER_ID
curl http://127.0.0.1:8000/api/v1/meters/METER_ID/consumption
curl http://127.0.0.1:8000/api/v1/hierarchy
```

A successful response is wrapped in a stable `data` property, for example:

```json
{
  "data": [
    {
      "meter_id": "example-id",
      "consumption": 124.5
    }
  ]
}
```

The example above illustrates the response shape only; it is not a claim about actual portal fields.

## Discover the real portal protocol

1. Open the portal in a browser and sign in using the provided credentials.
2. Open DevTools → Network; enable Preserve log.
3. Observe the login request method, URL, form/JSON fields, CSRF tokens and response cookies.
4. Navigate to meter list, meter detail and consumption pages.
5. Identify the data requests and their response formats. Prefer an existing JSON endpoint when available; otherwise parse HTML.
6. Update `.env` with confirmed paths and field names. If the login uses CSRF or a multi-step flow, update `PortalClient.login()` accordingly.
7. Record the observed facts, sample structures and anomalies in `PROTOCOL.md`.
8. Test all routes against the live portal and update the OpenAPI schema if the public contract changes.

Do not probe for vulnerabilities, bypass access controls, or change upstream data. Treat the portal as read-only.

## Tests

```powershell
pytest -q
```

The included tests cover normalization and HTML table parsing. They do not prove that the live portal integration works.

## Assumptions and trade-offs

- FastAPI was selected because it provides OpenAPI documentation automatically and supports a small, modular service.
- A single HTTP client is used to retain cookies for the process lifetime.
- HTML table parsing is generic. Real portal pages may require portal-specific selectors and mapping logic.
- The sample login implementation assumes a simple form POST. Add CSRF handling or other steps only if DevTools confirms they are required.
- This initial implementation does not persist a cache or local copy of meter data.
- The service is read-only and does not expose portal write operations.
- For production, use a managed secret store, add structured logging and metrics, and define safe concurrency/session behavior.

## Intentional omissions

- No frontend dashboard; the assessment makes it an optional extension.
- No invented meter data or unverified upstream paths.
- No caching, bulk export or advanced hierarchy reconstruction until the portal protocol is understood.
- No production deployment configuration until local integration tests pass.

## Reflection

Complete these honestly after you investigate and test the portal. Do not submit invented discoveries.

1. **What assumptions did you make?** Explain which assumptions were confirmed and which remain.
2. **Which part was most difficult, and how did you get unstuck?** Describe your actual DevTools/code investigation.
3. **If you had another day, what would you improve?** Prioritize improvements based on what you observed.
4. **What mistake did you make?** Give a real example and how you corrected it.
5. **If reviewing your own submission, what would you criticise?** Discuss concrete limitations and their impact.

## Submission checklist

- [ ] Verify login and session behavior against the live portal.
- [ ] Replace all placeholder upstream paths and field names.
- [ ] Verify list, detail and consumption endpoints.
- [ ] Complete `PROTOCOL.md` with observed facts.
- [ ] Run tests and manually test all API routes.
- [ ] Check `/openapi.json` and `/docs`.
- [ ] Complete the reflection with genuine experiences.
- [ ] Remove secrets and `.env` from Git.
- [ ] Push to a public GitHub repository and email the repository URL as instructed.

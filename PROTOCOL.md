# PROTOCOL.md — Urja Meter Ops discovery notes

## Status

**Discovery not yet recorded.** This file is a structured worksheet, not a report of verified portal behavior. Fill it in from browser DevTools and actual responses. Do not guess values.

## Portal

- Base URL: `https://urja-ops.flockenergy.tech`
- Access mode: normal authenticated user; read-only.
- Date inspected: TODO
- Browser / environment: TODO

## Authentication workflow

- Login HTTP method: TODO
- Login URL/path: TODO
- Form fields or JSON keys: TODO (never record the password)
- CSRF token required? TODO
- Cookies or bearer token returned: TODO (record names, not secret values)
- Successful-login indicator: TODO
- Failed-login indicator: TODO
- Session-expiry behavior: TODO
- Re-authentication behavior verified: TODO

## Discovered data requests

| Purpose | Method | Path | Parameters | Response format | Verified? |
|---|---|---|---|---|---|
| Meter list | TODO | TODO | TODO | TODO | No |
| Meter details | TODO | TODO | TODO | TODO | No |
| Consumption history | TODO | TODO | TODO | TODO | No |
| Network hierarchy | TODO | TODO | TODO | TODO | No |

## Data shapes and anomalies

### Meter list
- Observed field names: TODO
- Sample response with sensitive/session data removed: TODO
- Pagination/filter parameters: TODO
- Missing or inconsistent fields: TODO

### Meter details
- Observed field names: TODO
- Identifier format: TODO
- Relationships/hierarchy fields: TODO

### Consumption
- Date/time format and timezone: TODO
- Units: TODO
- Numeric representation: TODO
- Gaps, duplicates, unusual values: TODO

## Adapter decisions

Document confirmed choices and why:
- JSON API vs HTML parsing: TODO
- HTML selectors/table mapping: TODO
- Normalization rules: TODO
- Session refresh strategy: TODO
- Timeout and error handling: TODO

## Evidence and reproduction

For each observation, note the browser Network request name, method, path, status code and response type. Do not include passwords, cookie values, access tokens or other secrets.

## Remaining unknowns

- TODO

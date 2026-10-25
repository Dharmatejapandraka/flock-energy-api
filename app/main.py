
from contextlib import asynccontextmanager
from math import ceil

from fastapi import FastAPI, Path
from fastapi.responses import JSONResponse

from app.portal_client import PortalClient
from app.errors import (
    PortalAuthenticationError,
    PortalNotFoundError,
    PortalResponseError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.portal = PortalClient()
    yield
    app.state.portal.close()


app = FastAPI(
    title="Flock Energy — Urja Meter Ops API",
    description=(
        "A normalized REST API adapter for the read-only Urja Meter Ops portal. "
        "Portal paths and login behavior must be verified in PROTOCOL.md "
        "before production use."
    ),
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


@app.exception_handler(PortalAuthenticationError)
async def auth_error_handler(_, exc):
    return JSONResponse(
        status_code=502,
        content={
            "error": "portal_authentication_failed",
            "detail": str(exc),
        },
    )


@app.exception_handler(PortalNotFoundError)
async def not_found_handler(_, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "portal_resource_not_found",
            "detail": str(exc),
        },
    )


@app.exception_handler(PortalResponseError)
async def portal_error_handler(_, exc):
    return JSONResponse(
        status_code=502,
        content={
            "error": "portal_upstream_error",
            "detail": str(exc),
        },
    )


@app.get("/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "service": "flock-energy-api",
    }


@app.post("/api/v1/auth/login", tags=["Authentication"])
def login():
    """Create or refresh the upstream portal session."""
    return app.state.portal.login(force=True)


@app.get("/api/v1/meters", tags=["Meters"])
def list_meters():
    """Return the meter listing exposed by the upstream portal."""
    return {"data": app.state.portal.meters()}


@app.get("/api/v1/meters/{meter_id}", tags=["Meters"])
def get_meter(
    meter_id: str = Path(min_length=1, max_length=128)
):
    """Return normalized details for one meter."""
    return {"data": app.state.portal.meter(meter_id)}


@app.get(
    "/api/v1/meters/{meter_id}/consumption",
    tags=["Consumption"],
)
def get_consumption(
    meter_id: str = Path(min_length=1, max_length=128)
):
    """Return consumption history for one meter."""
    return {"data": app.state.portal.consumption(meter_id)}


@app.get("/api/v1/hierarchy", tags=["Hierarchy"])
def get_hierarchy():
    """Return unique hierarchy paths from all meter-list pages."""
    portal = app.state.portal

    first_page_response = portal.meters(page=1)

    if isinstance(first_page_response, dict):
        first_page_meters = first_page_response.get("data", [])
        total = first_page_response.get("total")
        page_size = first_page_response.get("pageSize")
    elif isinstance(first_page_response, list):
        first_page_meters = first_page_response
        total = None
        page_size = None
    else:
        first_page_meters = []
        total = None
        page_size = None

    if not isinstance(first_page_meters, list):
        first_page_meters = []

    if page_size is None or not isinstance(page_size, int) or page_size < 1:
        page_size = len(first_page_meters) or 20

    if isinstance(total, int) and total >= 0:
        total_pages = max(1, ceil(total / page_size))
    else:
        total_pages = 1

    hierarchy_paths = []
    seen_paths = set()
    meters_processed = 0

    for page_number in range(1, total_pages + 1):
        if page_number == 1:
            page_meters = first_page_meters
        else:
            page_response = portal.meters(page=page_number)

            if isinstance(page_response, dict):
                page_meters = page_response.get("data", [])
            elif isinstance(page_response, list):
                page_meters = page_response
            else:
                page_meters = []

            if not isinstance(page_meters, list):
                page_meters = []

        if not page_meters:
            break

        for meter in page_meters:
            if not isinstance(meter, dict):
                continue

            meter_id = meter.get("meterId") or meter.get("meter_id")
            if meter_id is None:
                continue

            details = portal.meter(str(meter_id))
            hierarchy = details.get("hierarchy", {})

            if not isinstance(hierarchy, dict) or not hierarchy:
                continue

            path = (
                hierarchy.get("zone"),
                hierarchy.get("circle"),
                hierarchy.get("division"),
                hierarchy.get("subdivision"),
                hierarchy.get("substation"),
                hierarchy.get("feeder"),
                hierarchy.get("dt"),
            )

            if path in seen_paths:
                continue

            seen_paths.add(path)
            hierarchy_paths.append(
                {
                    "zone": path[0],
                    "circle": path[1],
                    "division": path[2],
                    "subdivision": path[3],
                    "substation": path[4],
                    "feeder": path[5],
                    "dt": path[6],
                }
            )

            meters_processed += 1

    return {
        "data": hierarchy_paths,
        "count": len(hierarchy_paths),
        "pages_checked": total_pages,
    }

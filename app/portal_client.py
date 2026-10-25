
import re
from urllib.parse import urljoin

import httpx

from app.config import settings
from app.errors import (
    PortalAuthenticationError,
    PortalNotFoundError,
    PortalResponseError,
)
from app.normalization import parse_response, normalize_meter_detail


class PortalClient:
    """Read-only adapter around the legacy Urja Meter Ops portal."""

    def __init__(self):
        self.client = httpx.Client(
            base_url=settings.portal_base_url.rstrip("/") + "/",
            timeout=settings.request_timeout_seconds,
            follow_redirects=True,
            verify=settings.verify_tls,
            headers={"User-Agent": "flock-energy-api-wrapper/1.0"},
        )
        self._authenticated = False

    def close(self):
        self.client.close()

    def _url(self, path: str) -> str:
        return urljoin(self.client.base_url, path.lstrip("/"))

    def login(self, force: bool = False) -> dict:
        if self._authenticated and not force:
            return {
                "authenticated": True,
                "message": "Existing session reused",
            }

        if not settings.portal_username or not settings.portal_password:
            raise PortalAuthenticationError(
                "Set PORTAL_USERNAME and PORTAL_PASSWORD in .env."
            )

        payload = {
            settings.portal_username_field: settings.portal_username,
            settings.portal_password_field: settings.portal_password,
        }

        try:
            response = self.client.post(
                settings.portal_login_path,
                data=payload,
                headers={
                    "Accept": "application/json",
                    "Origin": settings.portal_base_url,
                    "Referer": f"{settings.portal_base_url}/login",
                    "x-sveltekit-action": "true",
                },
            )
        except httpx.HTTPError as exc:
            raise PortalAuthenticationError(
                f"Could not reach portal login: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise PortalAuthenticationError(
                f"Portal login returned HTTP {response.status_code}"
            )

        session_cookie = any(
            "session_token" in cookie.name
            for cookie in self.client.cookies.jar
        )

        try:
            result = response.json()
        except ValueError:
            result = {}

        is_redirect = (
            isinstance(result, dict)
            and result.get("type") == "redirect"
            and result.get("status") == 303
            and result.get("location") == "/meters"
        )

        if not session_cookie or not is_redirect:
            raise PortalAuthenticationError(
                "Portal login could not be verified. Check credentials, "
                "response format, and session cookie."
            )

        self._authenticated = True

        return {
            "authenticated": True,
            "message": "Portal login successful",
        }

    def request_data(self, path: str):
        if not self._authenticated:
            self.login()

        try:
            response = self.client.get(path)
            content_type = response.headers.get("content-type", "")

            try:
                data = parse_response(response.text, content_type)
            except ValueError:
                self.login(force=True)
                response = self.client.get(path)
                content_type = response.headers.get("content-type", "")
                data = parse_response(response.text, content_type)

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise PortalNotFoundError(
                    "The requested resource was not found in the portal."
                ) from exc

            raise PortalResponseError(
                f"Portal returned HTTP {exc.response.status_code}"
            ) from exc

        except httpx.HTTPError as exc:
            raise PortalResponseError(
                f"Portal request failed: {exc}"
            ) from exc

        if response.status_code == 404:
            raise PortalNotFoundError(
                "The requested resource was not found in the portal."
            )

        if response.status_code >= 400:
            raise PortalResponseError(
                f"Portal returned HTTP {response.status_code}"
            )

        return data

    def meters(self, page: int = 1):
        """Fetch one page of meters from the portal."""
        if page < 1:
            raise ValueError("page must be at least 1")

        path = settings.portal_meters_path

        if re.search(r"([?&]page=)\d+", path):
            path = re.sub(
                r"([?&]page=)\d+",
                lambda match: f"{match.group(1)}{page}",
                path,
            )
        else:
            separator = "&" if "?" in path else "?"
            path = f"{path}{separator}page={page}"

        return self.request_data(path)

    def meter(self, meter_id: str):
        """Fetch and normalize details for one meter."""
        data = self.request_data(
            settings.portal_meter_detail_path.format(
                meter_id=meter_id
            )
        )
        return normalize_meter_detail(data)

    def consumption(self, meter_id: str):
        """Fetch consumption readings for one meter."""
        return self.request_data(
            settings.portal_consumption_path.format(
                meter_id=meter_id
            )
        )

    def hierarchy(self):
        """Fetch the configured hierarchy endpoint, if available."""
        return self.request_data(settings.portal_hierarchy_path)

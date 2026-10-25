
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Upstream portal
    portal_base_url: str = "https://urja-ops.flockenergy.tech"

    # Read credentials from .env; never hardcode them here
    portal_username: str = ""
    portal_password: str = ""

    # Confirmed login form
    portal_login_path: str = "/login"
    portal_username_field: str = "email"
    portal_password_field: str = "password"

    # Confirmed meter search API
    portal_meters_path: str = "/portal/meters/search?q=&page=1"

    # Detail path still needs verification as a JSON endpoint
    portal_meter_detail_path: str = "/portal/meters/{meter_id}"

    # Confirmed energy API
    portal_consumption_path: str = "/portal/meters/{meter_id}/energy"

    # Not yet verified in DevTools
    portal_hierarchy_path: str = "/portal/hierarchy"

    request_timeout_seconds: float = 20.0
    verify_tls: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

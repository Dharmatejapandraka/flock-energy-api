class PortalError(Exception):
    """Base exception for upstream portal failures."""

class PortalAuthenticationError(PortalError):
    """Login failed or the portal rejected the session."""

class PortalNotFoundError(PortalError):
    """The requested upstream resource does not exist."""

class PortalResponseError(PortalError):
    """The upstream response could not be interpreted safely."""

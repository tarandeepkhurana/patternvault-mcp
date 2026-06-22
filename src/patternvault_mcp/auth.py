"""Authentication setup for PatternVault MCP."""

from fastmcp.server.auth import AuthProvider, StaticTokenVerifier

from patternvault_mcp.settings import Settings


def build_auth_provider(settings: Settings) -> AuthProvider | None:
    """Build the configured FastMCP auth provider.

    Static token auth is useful for local/manual testing. For hosted production,
    keep this module as the switch point for a real OAuth/OIDC/JWT provider.
    """

    if settings.auth_mode == "none":
        return None

    if settings.auth_mode == "static":
        if not settings.static_token:
            msg = "PATTERNVAULT_STATIC_TOKEN is required when PATTERNVAULT_AUTH_MODE=static"
            raise ValueError(msg)

        return StaticTokenVerifier(
            tokens={
                settings.static_token: {
                    "client_id": "patternvault-local",
                    "scopes": settings.required_scopes,
                }
            },
            required_scopes=settings.required_scopes,
        )

    msg = f"Unsupported auth mode: {settings.auth_mode}"
    raise ValueError(msg)

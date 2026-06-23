"""PatternVault FastMCP server definition."""

from fastmcp import FastMCP

from patternvault_mcp.auth import build_auth_provider
from patternvault_mcp.resources import register_resources
from patternvault_mcp.settings import get_settings
from patternvault_mcp.tools import register_tools


settings = get_settings()

mcp = FastMCP(
    name=settings.server_name,
    version=settings.server_version,
    instructions=(
        "PatternVault exposes reusable engineering pattern documentation as MCP "
        "resources for coding agents."
    ),
    auth=build_auth_provider(settings),
)

register_resources(mcp, settings)
register_tools(mcp, settings)

app = mcp.http_app(path=settings.mcp_path, stateless_http=settings.stateless_http)

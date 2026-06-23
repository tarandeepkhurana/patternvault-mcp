"""MCP resources backed by PatternVault Markdown files."""

from __future__ import annotations

import json
import re

from fastmcp import FastMCP

from patternvault_mcp.pattern_docs import list_docs, read_doc
from patternvault_mcp.settings import Settings


def register_resources(mcp: FastMCP, settings: Settings) -> None:
    """Register all PatternVault README resources on the server."""

    readmes_dir = settings.readmes_dir.resolve()

    @mcp.resource(
        "patternvault://readmes/index",
        name="patternvault_readmes_index",
        title="PatternVault README Index",
        description="Index of Markdown pattern resources available in PatternVault.",
        mime_type="application/json",
        tags={"patternvault", "readmes"},
    )
    def readmes_index() -> str:
        resources = [
            {
                "slug": doc.slug,
                "title": doc.title,
                "uri": doc.uri,
                "filename": doc.filename,
            }
            for doc in list_docs(readmes_dir)
        ]
        return json.dumps({"resources": resources}, indent=2)

    for doc in list_docs(readmes_dir):
        _register_readme_resource(mcp, doc)


def _register_readme_resource(mcp: FastMCP, doc) -> None:
    def read_readme() -> str:
        return read_doc(doc)

    read_readme.__name__ = f"readme_{_python_identifier(doc.slug)}"

    mcp.resource(
        doc.uri,
        name=read_readme.__name__,
        title=doc.title,
        description=f"PatternVault Markdown resource from {doc.filename}.",
        mime_type="text/markdown",
        tags={"patternvault", "readmes"},
    )(read_readme)


def _python_identifier(value: str) -> str:
    return re.sub(r"\W+", "_", value).strip("_")

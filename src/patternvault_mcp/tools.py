"""MCP tools for discovering and applying PatternVault docs."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastmcp import FastMCP

from patternvault_mcp.pattern_docs import (
    build_context_pack,
    get_doc,
    list_docs,
    read_doc,
    search_docs,
    search_pattern_cards,
)
from patternvault_mcp.settings import Settings


def register_tools(mcp: FastMCP, settings: Settings) -> None:
    """Register PatternVault document and pattern-card tools."""

    readmes_dir = settings.readmes_dir.resolve()

    @mcp.tool(
        name="list_pattern_docs",
        title="List Pattern Docs",
        description="List all PatternVault Markdown pattern documents.",
        tags={"patternvault", "docs"},
    )
    def list_pattern_docs() -> list[dict[str, str]]:
        return [
            {
                "slug": doc.slug,
                "title": doc.title,
                "uri": doc.uri,
                "filename": doc.filename,
            }
            for doc in list_docs(readmes_dir)
        ]

    @mcp.tool(
        name="read_pattern_doc",
        title="Read Pattern Doc",
        description="Read one PatternVault Markdown document by slug, filename, or resource URI.",
        tags={"patternvault", "docs"},
    )
    def read_pattern_doc(slug: str) -> dict[str, str]:
        doc = get_doc(readmes_dir, slug)
        return {
            "slug": doc.slug,
            "title": doc.title,
            "uri": doc.uri,
            "filename": doc.filename,
            "content": read_doc(doc),
        }

    @mcp.tool(
        name="search_patterns",
        title="Search Patterns",
        description="Search PatternVault Markdown docs with deterministic keyword matching.",
        tags={"patternvault", "search"},
    )
    def search_patterns(query: str, max_results: int = 5) -> list[dict[str, object]]:
        return search_docs(readmes_dir, query=query, max_results=max_results)

    @mcp.tool(
        name="recommend_patterns_for_task",
        title="Recommend Patterns For Task",
        description="Recommend relevant PatternVault docs and pattern cards for an engineering task.",
        tags={"patternvault", "recommendations"},
    )
    def recommend_patterns_for_task(task: str, max_results: int = 5) -> dict[str, object]:
        docs = search_docs(readmes_dir, query=task, max_results=max_results)
        cards = search_pattern_cards(readmes_dir, query=task, max_results=max_results)
        return {
            "task": task,
            "recommended_docs": docs,
            "recommended_pattern_cards": cards,
            "suggested_read_order": [doc["uri"] for doc in docs],
        }

    @mcp.tool(
        name="get_pattern_cards",
        title="Get Pattern Cards",
        description="List or search individual pattern cards parsed from 10-pattern-cards.md.",
        tags={"patternvault", "pattern-cards"},
    )
    def get_pattern_cards(
        query: str = "",
        max_results: int = 10,
        include_content: bool = False,
    ) -> list[dict[str, object]]:
        return search_pattern_cards(
            readmes_dir,
            query=query,
            max_results=max_results,
            include_content=include_content,
        )

    @mcp.tool(
        name="build_context_pack",
        title="Build Context Pack",
        description="Build a compact task-focused bundle of relevant PatternVault docs and pattern cards.",
        tags={"patternvault", "context"},
    )
    def build_context_pack_tool(task: str, max_chars: int = 12000) -> dict[str, object]:
        return build_context_pack(readmes_dir, task=task, max_chars=max_chars)


async def _smoke_test_tools() -> None:
    """Run a small local smoke test for the registered MCP tools."""

    test_mcp = FastMCP(name="PatternVault Tools Smoke Test")
    register_tools(test_mcp, Settings())

    tools = await test_mcp.list_tools()
    print("Registered tools:")
    for tool in tools:
        print(f"- {tool.name}")

    sample_calls: list[tuple[str, dict[str, object]]] = [
        ("list_pattern_docs", {}),
        ("search_patterns", {"query": "supabase auth dependency", "max_results": 3}),
        ("get_pattern_cards", {"query": "supabase auth", "max_results": 3}),
        (
            "build_context_pack",
            {
                "task": "add a Supabase auth protected backend route",
                "max_chars": 2000,
            },
        ),
    ]

    for tool_name, arguments in sample_calls:
        result = await test_mcp.call_tool(tool_name, arguments)
        print(f"\n{tool_name}:")
        print(json.dumps(_tool_result_payload(result), indent=2, default=str))


def _tool_result_payload(result: Any) -> Any:
    structured_content = getattr(result, "structured_content", None)
    if structured_content is not None:
        return structured_content

    content = getattr(result, "content", None)
    if content is not None:
        return content

    return result


if __name__ == "__main__":
    asyncio.run(_smoke_test_tools())

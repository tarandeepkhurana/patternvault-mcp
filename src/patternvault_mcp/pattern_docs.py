"""Markdown-backed PatternVault document helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


README_PATTERN = "*.md"
README_URI_PREFIX = "patternvault://readmes/"
PATTERN_CARD_HEADING = re.compile(r"^## Pattern:\s*(?P<name>.+?)\s*$", re.MULTILINE)
TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]*", re.IGNORECASE)


@dataclass(frozen=True)
class PatternDoc:
    path: Path
    slug: str
    title: str
    uri: str
    filename: str


@dataclass(frozen=True)
class PatternCard:
    name: str
    slug: str
    source_slug: str
    source_uri: str
    content: str


def list_docs(readmes_dir: Path) -> list[PatternDoc]:
    """Return all Markdown pattern docs in stable order."""

    root = readmes_dir.resolve()
    if not root.exists():
        return []

    return [
        PatternDoc(
            path=path,
            slug=slug_for_file(path),
            title=title_for_file(path),
            uri=uri_for_slug(slug_for_file(path)),
            filename=path.name,
        )
        for path in sorted(root.glob(README_PATTERN))
        if path.is_file() and not path.name.startswith(".")
    ]


def get_doc(readmes_dir: Path, slug_or_uri: str) -> PatternDoc:
    """Resolve a document by slug, filename, or PatternVault resource URI."""

    wanted_slug = normalize_doc_slug(slug_or_uri)

    for doc in list_docs(readmes_dir):
        if doc.slug == wanted_slug:
            return doc

    available = ", ".join(doc.slug for doc in list_docs(readmes_dir))
    msg = f"Unknown PatternVault doc '{slug_or_uri}'. Available docs: {available}"
    raise ValueError(msg)


def read_doc(doc: PatternDoc) -> str:
    """Read a PatternVault document as UTF-8 Markdown."""

    return doc.path.read_text(encoding="utf-8")


def search_docs(readmes_dir: Path, query: str, max_results: int = 5) -> list[dict[str, object]]:
    """Search Markdown docs with deterministic keyword scoring."""

    query_terms = tokenize(query)
    if not query_terms:
        return []

    max_results = clamp(max_results, 1, 50)
    results: list[dict[str, object]] = []
    for doc in list_docs(readmes_dir):
        text = read_doc(doc)
        score = score_text(query_terms, f"{doc.title} {doc.filename}", text)
        if score <= 0:
            continue

        results.append(
            {
                "slug": doc.slug,
                "title": doc.title,
                "uri": doc.uri,
                "filename": doc.filename,
                "score": score,
                "matches": build_excerpts(text, query_terms),
            }
        )

    return sorted(results, key=lambda item: (-int(item["score"]), str(item["slug"])))[:max_results]


def list_pattern_cards(readmes_dir: Path) -> list[PatternCard]:
    """Parse individual pattern cards from 10-pattern-cards.md."""

    try:
        source_doc = get_doc(readmes_dir, "10-pattern-cards")
    except ValueError:
        return []

    text = read_doc(source_doc)
    matches = list(PATTERN_CARD_HEADING.finditer(text))
    cards: list[PatternCard] = []

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        name = match.group("name").strip()
        cards.append(
            PatternCard(
                name=name,
                slug=slugify(name),
                source_slug=source_doc.slug,
                source_uri=source_doc.uri,
                content=text[start:end].strip(),
            )
        )

    return cards


def search_pattern_cards(
    readmes_dir: Path,
    query: str = "",
    max_results: int = 10,
    include_content: bool = False,
) -> list[dict[str, object]]:
    """Return parsed pattern cards, optionally filtered by query."""

    query_terms = tokenize(query)
    max_results = clamp(max_results, 1, 100)
    results: list[dict[str, object]] = []

    for card in list_pattern_cards(readmes_dir):
        score = score_text(query_terms, card.name, card.content) if query_terms else 1
        if score <= 0:
            continue

        result: dict[str, object] = {
            "name": card.name,
            "slug": card.slug,
            "source_slug": card.source_slug,
            "source_uri": card.source_uri,
            "score": score,
            "matches": build_excerpts(card.content, query_terms) if query_terms else [],
        }
        if include_content:
            result["content"] = card.content
        results.append(result)

    return sorted(results, key=lambda item: (-int(item["score"]), str(item["slug"])))[:max_results]


def build_context_pack(readmes_dir: Path, task: str, max_chars: int = 12000) -> dict[str, object]:
    """Build a compact task-focused context bundle from docs and pattern cards."""

    max_chars = clamp(max_chars, 2_000, 50_000)
    docs = search_docs(readmes_dir, task, max_results=6)
    cards = search_pattern_cards(readmes_dir, task, max_results=8, include_content=True)

    sections: list[str] = []
    included_docs: list[dict[str, object]] = []
    included_cards: list[dict[str, object]] = []

    for doc_result in docs:
        doc = get_doc(readmes_dir, str(doc_result["slug"]))
        text = read_doc(doc)
        section = text.strip() if text.lstrip().startswith("# ") else f"# {doc.title}\n\n{text.strip()}"
        remaining = _remaining_chars(sections, max_chars)
        if remaining < 300:
            break
        sections.append(trim_to_chars(section, remaining))
        included_docs.append(doc_result)

    for card in cards:
        content = str(card.get("content", ""))
        remaining = _remaining_chars(sections, max_chars)
        if not content or remaining < 300:
            break
        sections.append(trim_to_chars(content, remaining))
        included_cards.append({key: value for key, value in card.items() if key != "content"})

    return {
        "task": task,
        "max_chars": max_chars,
        "included_docs": included_docs,
        "included_pattern_cards": included_cards,
        "context": "\n\n---\n\n".join(section for section in sections if section),
    }


def normalize_doc_slug(value: str) -> str:
    """Normalize a slug, filename, or PatternVault URI to a doc slug."""

    normalized = value.strip()
    if normalized.startswith(README_URI_PREFIX):
        normalized = normalized.removeprefix(README_URI_PREFIX)
    if normalized.endswith(".md"):
        normalized = normalized[:-3]
    return normalized.lower().replace("_", "-")


def slug_for_file(path: Path) -> str:
    return path.stem.lower().replace("_", "-")


def uri_for_slug(slug: str) -> str:
    return f"{README_URI_PREFIX}{slug}"


def title_for_file(path: Path) -> str:
    title = re.sub(r"^\d+[-_ ]*", "", path.stem)
    return title.replace("-", " ").replace("_", " ").title()


def slugify(value: str) -> str:
    slug = "-".join(tokenize(value))
    return slug or "pattern"


def tokenize(value: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_PATTERN.finditer(value)]


def score_text(query_terms: list[str], title: str, body: str) -> int:
    title_lower = title.lower()
    body_lower = body.lower()
    score = 0

    for term in query_terms:
        if term in title_lower:
            score += 12
        score += min(body_lower.count(term), 10)

    return score


def build_excerpts(text: str, query_terms: list[str], max_excerpts: int = 3, radius: int = 120) -> list[str]:
    excerpts: list[str] = []
    text_lower = text.lower()

    for term in query_terms:
        index = text_lower.find(term)
        if index < 0:
            continue

        start = max(0, index - radius)
        end = min(len(text), index + len(term) + radius)
        excerpt = " ".join(text[start:end].split())
        if start > 0:
            excerpt = f"...{excerpt}"
        if end < len(text):
            excerpt = f"{excerpt}..."
        excerpts.append(excerpt)

        if len(excerpts) >= max_excerpts:
            break

    return excerpts


def trim_to_chars(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    if max_chars <= 15:
        return ""
    return value[: max(0, max_chars - 15)].rstrip() + "\n\n[truncated]"


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def _remaining_chars(sections: list[str], max_chars: int) -> int:
    used = sum(len(section) for section in sections) + max(0, len(sections) - 1) * len("\n\n---\n\n")
    return max(0, max_chars - used)

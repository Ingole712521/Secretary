"""Tool for searching a query on a named website."""

from __future__ import annotations

import asyncio
import platform
import subprocess
import sys
from typing import Any
from urllib.parse import quote, quote_plus

from app.tools.interfaces.base_tool import BaseTool
from app.tools.results.models import ToolResult
from app.tools.schemas.enums import ToolCategory, ToolPermissionLevel
from app.tools.schemas.parameters import ToolParameter

# Native search-URL templates for popular sites. ``{q}`` is the encoded query.
# Aliases the user is likely to say all map onto these canonical templates.
_SEARCH_TEMPLATES: dict[str, str] = {
    "google": "https://www.google.com/search?q={q}",
    "bing": "https://www.bing.com/search?q={q}",
    "duckduckgo": "https://duckduckgo.com/?q={q}",
    "ddg": "https://duckduckgo.com/?q={q}",
    "youtube": "https://www.youtube.com/results?search_query={q}",
    "yt": "https://www.youtube.com/results?search_query={q}",
    "wikipedia": "https://en.wikipedia.org/w/index.php?search={q}",
    "wiki": "https://en.wikipedia.org/w/index.php?search={q}",
    "amazon": "https://www.amazon.in/s?k={q}",
    "flipkart": "https://www.flipkart.com/search?q={q}",
    "github": "https://github.com/search?q={q}&type=repositories",
    "stackoverflow": "https://stackoverflow.com/search?q={q}",
    "stack overflow": "https://stackoverflow.com/search?q={q}",
    "reddit": "https://www.reddit.com/search/?q={q}",
    "twitter": "https://twitter.com/search?q={q}",
    "x": "https://twitter.com/search?q={q}",
    "linkedin": "https://www.linkedin.com/search/results/all/?keywords={q}",
    "spotify": "https://open.spotify.com/search/{q_path}",
    "maps": "https://www.google.com/maps/search/{q_path}",
    "google maps": "https://www.google.com/maps/search/{q_path}",
    "netflix": "https://www.netflix.com/search?q={q}",
    "imdb": "https://www.imdb.com/find/?q={q}",
    "gmail": "https://mail.google.com/mail/u/0/#search/{q}",
    "drive": "https://drive.google.com/drive/search?q={q}",
    "google drive": "https://drive.google.com/drive/search?q={q}",
    "play store": "https://play.google.com/store/search?q={q}",
    "playstore": "https://play.google.com/store/search?q={q}",
    "ebay": "https://www.ebay.com/sch/i.html?_nkw={q}",
    "quora": "https://www.quora.com/search?q={q}",
    "pinterest": "https://www.pinterest.com/search/pins/?q={q}",
    "medium": "https://medium.com/search?q={q}",
    "npm": "https://www.npmjs.com/search?q={q}",
    "pypi": "https://pypi.org/search/?q={q}",
    "news": "https://news.google.com/search?q={q}",
    "google news": "https://news.google.com/search?q={q}",
    "scholar": "https://scholar.google.com/scholar?q={q}",
    "google scholar": "https://scholar.google.com/scholar?q={q}",
}

# Common site name -> domain, for the site-scoped fallback search.
_KNOWN_DOMAINS: dict[str, str] = {
    "facebook": "facebook.com",
    "instagram": "instagram.com",
    "whatsapp": "web.whatsapp.com",
    "telegram": "web.telegram.org",
    "geeksforgeeks": "geeksforgeeks.org",
    "w3schools": "w3schools.com",
    "mdn": "developer.mozilla.org",
    "leetcode": "leetcode.com",
}


class WebSearchTool(BaseTool):
    """Search a query on a named website and open the results in the browser.

    Handles requests like "search cats on YouTube", "search laptops on
    Amazon", or "search python decorators on Stack Overflow". For any site
    that is not directly supported, it falls back to a Google search scoped
    to that site's domain so the search still happens "on that website".
    """

    def __init__(self, *, timeout_seconds: float = 15.0) -> None:
        """Initialize the tool.

        Args:
            timeout_seconds: Timeout for launching the browser.
        """
        self._timeout_seconds = timeout_seconds

    @property
    def id(self) -> str:
        """Tool identifier."""
        return "web.search"

    @property
    def name(self) -> str:
        """Tool name."""
        return "Web Search"

    @property
    def description(self) -> str:
        """Tool description."""
        return (
            "Search for something on a website and open the results in the "
            "browser. Use for any 'search X on Y' / 'look up X on Y' / "
            "'find X on Y' request, e.g. 'search lofi music on YouTube', "
            "'search running shoes on Amazon', 'search FastAPI on Google'. "
            "Provide 'query' (what to search for) and optionally 'website' "
            "(the site to search on; defaults to Google). 'website' may be a "
            "known site name (youtube, amazon, google, wikipedia, github, "
            "reddit, ...) or any domain like 'example.com'."
        )

    @property
    def category(self) -> ToolCategory:
        """Tool category."""
        return ToolCategory.SYSTEM

    @property
    def parameters(self) -> list[ToolParameter]:
        """Tool parameters."""
        return [
            ToolParameter(
                name="query",
                type="string",
                description="What to search for (the search terms).",
                required=True,
            ),
            ToolParameter(
                name="website",
                type="string",
                description=(
                    "Site to search on: a known name (youtube, amazon, "
                    "google, wikipedia, github, reddit, ...) or a domain "
                    "like 'example.com'. Defaults to Google."
                ),
                required=False,
                default="google",
            ),
        ]

    @property
    def permissions(self) -> list[ToolPermissionLevel]:
        """Required permissions."""
        return [ToolPermissionLevel.EXECUTE]

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        """Build the search URL and open it in the default browser.

        Args:
            params: Must include ``query``; ``website`` is optional.

        Returns:
            Result describing the search that was opened.
        """
        query = str(params.get("query", "")).strip()
        if not query:
            return ToolResult.failure(
                error="No query provided",
                message="Tell me what to search for.",
            )

        website = str(params.get("website") or "google").strip()
        url, site_label = _build_search_url(query, website)

        try:
            exit_code, stderr = await asyncio.to_thread(self._open, url)
        except subprocess.TimeoutExpired:
            return ToolResult.success(
                output={"query": query, "website": site_label, "url": url},
                message=f"Searching '{query}' on {site_label}.",
            )
        except OSError as exc:
            return ToolResult.failure(
                error=str(exc),
                message=f"Failed to open the browser for '{site_label}'.",
            )

        if exit_code != 0:
            return ToolResult.failure(
                error=stderr.strip() or f"Exit code {exit_code}",
                message=f"Could not open the search on {site_label}.",
            )

        return ToolResult.success(
            output={"query": query, "website": site_label, "url": url},
            message=f"Searching '{query}' on {site_label}.",
        )

    def _open(self, url: str) -> tuple[int, str]:
        """Open a URL in the default browser and return (exit_code, stderr)."""
        argv = _open_url_argv(url)
        completed = subprocess.run(  # noqa: S603
            argv,
            capture_output=True,
            timeout=self._timeout_seconds,
            check=False,
        )
        stderr = completed.stderr.decode(sys.getdefaultencoding(), errors="replace")
        return completed.returncode, stderr


def _build_search_url(query: str, website: str) -> tuple[str, str]:
    """Return the (url, human-label) for searching ``query`` on ``website``.

    Args:
        query: Raw search terms.
        website: Site name or domain to search on.

    Returns:
        A tuple of the search URL and a human-friendly site label.
    """
    key = website.lower().strip()
    encoded = quote_plus(query)
    encoded_path = quote(query)

    template = _SEARCH_TEMPLATES.get(key)
    if template is not None:
        url = template.format(q=encoded, q_path=encoded_path)
        return url, key

    domain = _as_domain(key)
    if domain is not None:
        # Scope a Google search to the requested site so it still searches
        # "on that website" even without a native search endpoint.
        scoped = quote_plus(f"{query} site:{domain}")
        return f"https://www.google.com/search?q={scoped}", domain

    # Unknown, non-domain site name: run a plain Google search including it.
    combined = quote_plus(f"{query} {website}")
    return f"https://www.google.com/search?q={combined}", "google"


def _as_domain(website: str) -> str | None:
    """Resolve a site name to a domain, or None when it is not a site.

    Args:
        website: Site name or domain string (lowercased).

    Returns:
        A domain like ``example.com``, or None when it is a bare word.
    """
    if website in _KNOWN_DOMAINS:
        return _KNOWN_DOMAINS[website]
    cleaned = website.removeprefix("http://").removeprefix("https://")
    cleaned = cleaned.split("/")[0].strip()
    if "." in cleaned and " " not in cleaned:
        return cleaned
    return None


def _open_url_argv(url: str) -> list[str]:
    """Build the OS-specific command to open a URL in the default browser."""
    if platform.system() == "Windows":
        command = f"Start-Process -FilePath {_ps_quote(url)}"
        return [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ]
    if platform.system() == "Darwin":
        return ["open", url]
    return ["xdg-open", url]


def _ps_quote(value: str) -> str:
    """Single-quote a value for safe use in a PowerShell command."""
    escaped = value.replace("'", "''")
    return f"'{escaped}'"

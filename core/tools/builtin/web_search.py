from __future__ import annotations

from typing import Any

import httpx

from core.tools.base import BaseTool


class WebSearchTool(BaseTool):
    """Web search via DuckDuckGo with Instant Answer API + HTML lite fallback."""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search the web for current information on any topic. "
            "Returns summarised results from DuckDuckGo."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Max number of result snippets to return (default 5, max 10).",
                },
            },
            "required": ["query"],
        }

    async def run(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "")
        num_results = min(kwargs.get("num_results", 5), 10)
        if not query:
            return "Error: empty search query."

        result = await self._instant_answer(query)
        if result:
            return result

        return await self._html_lite_search(query, num_results)

    async def _instant_answer(self, query: str) -> str | None:
        """Try the DuckDuckGo Instant Answer JSON API first."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
                )
                data = resp.json()

            abstract = data.get("AbstractText", "")
            source = data.get("AbstractSource", "")
            url = data.get("AbstractURL", "")
            if abstract:
                cite = f"\n\nSource: {source} ({url})" if source else ""
                return abstract + cite

            answer = data.get("Answer", "")
            if answer:
                return answer

            related: list[dict] = data.get("RelatedTopics", [])
            snippets = []
            for topic in related[:5]:
                text = topic.get("Text", "")
                if text:
                    href = topic.get("FirstURL", "")
                    snippets.append(f"- {text}" + (f" ({href})" if href else ""))
            if snippets:
                return "\n".join(snippets)

        except Exception:
            pass
        return None

    async def _html_lite_search(self, query: str, num_results: int) -> str:
        """Fallback: scrape DuckDuckGo HTML lite for search result snippets."""
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(
                    "https://lite.duckduckgo.com/lite/",
                    params={"q": query},
                    headers={"User-Agent": "Mozilla/5.0 (compatible; AgentPlatform/1.0)"},
                )
                html = resp.text

            snippets = self._parse_lite_html(html, num_results)
            if snippets:
                return f"Search results for '{query}':\n\n" + "\n\n".join(snippets)
            return f"No results found for '{query}'."
        except Exception as exc:
            return f"Search error: {exc}"

    @staticmethod
    def _parse_lite_html(html: str, max_results: int) -> list[str]:
        """Extract result snippets from DuckDuckGo lite HTML without an HTML parser."""
        results: list[str] = []
        marker = 'class="result-snippet"'
        pos = 0
        while len(results) < max_results:
            idx = html.find(marker, pos)
            if idx == -1:
                break
            tag_end = html.find(">", idx)
            close = html.find("</td>", tag_end)
            if tag_end == -1 or close == -1:
                break
            snippet = html[tag_end + 1: close].strip()
            snippet = snippet.replace("<b>", "").replace("</b>", "")
            snippet = snippet.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            snippet = snippet.replace("&#x27;", "'").replace("&quot;", '"')
            if snippet:
                link_start = html.rfind('class="result-link"', pos, idx)
                url = ""
                if link_start != -1:
                    href_start = html.find('href="', link_start)
                    if href_start != -1 and href_start < idx:
                        href_end = html.find('"', href_start + 6)
                        url = html[href_start + 6: href_end]
                entry = f"- {snippet}"
                if url:
                    entry += f"\n  Source: {url}"
                results.append(entry)
            pos = close
        return results

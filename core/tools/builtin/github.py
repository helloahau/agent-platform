from __future__ import annotations

import base64
import json
from typing import Any

import httpx

from core.tools.base import BaseTool

_GITHUB_API = "https://api.github.com"


class GitHubTool(BaseTool):
    """Full GitHub integration: repos, files, issues, and pull requests (read + write)."""

    @property
    def name(self) -> str:
        return "github"

    @property
    def description(self) -> str:
        return (
            "Interact with GitHub repositories, issues, and pull requests. "
            "Read actions (no token needed for public repos): "
            "'search_repos', 'get_repo', 'list_files', 'read_file', "
            "'list_issues', 'get_issue', 'list_prs', 'get_pr', 'get_pr_diff'. "
            "Write actions (require GITHUB_TOKEN): "
            "'comment_on_issue', 'comment_on_pr', 'update_pr', "
            "'create_issue', 'merge_pr'."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "search_repos", "get_repo", "list_files", "read_file",
                        "list_issues", "get_issue", "create_issue",
                        "comment_on_issue",
                        "list_prs", "get_pr", "get_pr_diff",
                        "comment_on_pr", "update_pr", "merge_pr",
                    ],
                    "description": "The GitHub action to perform.",
                },
                "owner": {
                    "type": "string",
                    "description": "Repository owner (user or org).",
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name.",
                },
                "query": {
                    "type": "string",
                    "description": "Search query (for search_repos).",
                },
                "path": {
                    "type": "string",
                    "description": "File/directory path in the repo.",
                },
                "ref": {
                    "type": "string",
                    "description": "Branch or commit SHA.",
                },
                "number": {
                    "type": "integer",
                    "description": "Issue or PR number.",
                },
                "state": {
                    "type": "string",
                    "enum": ["open", "closed", "all"],
                    "description": "Filter by state. Default: open.",
                },
                "title": {
                    "type": "string",
                    "description": "Title (for create_issue or update_pr).",
                },
                "body": {
                    "type": "string",
                    "description": "Body text (for create_issue, comment_on_issue, comment_on_pr, update_pr).",
                },
            },
            "required": ["action"],
        }

    def _get_token(self) -> str:
        try:
            from config.settings import get_settings
            token = get_settings().github_token
            if token:
                return token
        except Exception:
            pass
        import os
        return os.environ.get("GITHUB_TOKEN", "")

    def _headers(self, require_auth: bool = False) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github.v3+json"}
        token = self._get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        elif require_auth:
            raise PermissionError(
                "This action requires a GITHUB_TOKEN. "
                "Set it in your .env file or as an environment variable."
            )
        return headers

    async def _api_get(self, url: str, params: dict | None = None, require_auth: bool = False) -> Any:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, headers=self._headers(require_auth), params=params)
            resp.raise_for_status()
            return resp.json()

    async def _api_post(self, url: str, payload: dict) -> Any:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(url, headers=self._headers(require_auth=True), json=payload)
            resp.raise_for_status()
            return resp.json()

    async def _api_patch(self, url: str, payload: dict) -> Any:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.patch(url, headers=self._headers(require_auth=True), json=payload)
            resp.raise_for_status()
            return resp.json()

    async def _api_put(self, url: str, payload: dict | None = None) -> Any:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.put(url, headers=self._headers(require_auth=True), json=payload or {})
            resp.raise_for_status()
            return resp.json()

    async def _api_get_text(self, url: str) -> str:
        headers = self._headers()
        headers["Accept"] = "application/vnd.github.v3.diff"
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.text

    async def run(self, **kwargs: Any) -> str:
        action = kwargs.get("action", "")
        dispatch = {
            "search_repos": self._search_repos,
            "get_repo": self._get_repo,
            "list_files": self._list_files,
            "read_file": self._read_file,
            "list_issues": self._list_issues,
            "get_issue": self._get_issue,
            "create_issue": self._create_issue,
            "comment_on_issue": self._comment_on_issue,
            "list_prs": self._list_prs,
            "get_pr": self._get_pr,
            "get_pr_diff": self._get_pr_diff,
            "comment_on_pr": self._comment_on_pr,
            "update_pr": self._update_pr,
            "merge_pr": self._merge_pr,
        }
        handler = dispatch.get(action)
        if not handler:
            return f"Error: unknown action '{action}'. Available: {list(dispatch.keys())}"
        try:
            return await handler(**kwargs)
        except PermissionError as exc:
            return f"Auth error: {exc}"
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500]
            return f"GitHub API error ({exc.response.status_code}): {body}"
        except Exception as exc:
            return f"GitHub error: {exc}"

    # ── Read actions ─────────────────────────────────────────────────────

    async def _search_repos(self, **kw: Any) -> str:
        query = kw.get("query", "")
        if not query:
            return "Error: 'query' is required."
        data = await self._api_get(f"{_GITHUB_API}/search/repositories", {"q": query, "per_page": 5})
        items = data.get("items", [])
        if not items:
            return f"No repositories found for '{query}'."
        lines = [f"Found {data['total_count']} repos (top 5):\n"]
        for r in items:
            lines.append(
                f"- **{r['full_name']}** ({r['stargazers_count']} stars) — "
                f"{r.get('description') or 'No description'}\n"
                f"  {r['html_url']}  |  {r.get('language', 'N/A')}"
            )
        return "\n".join(lines)

    async def _get_repo(self, **kw: Any) -> str:
        owner, repo = kw.get("owner", ""), kw.get("repo", "")
        if not owner or not repo:
            return "Error: 'owner' and 'repo' are required."
        d = await self._api_get(f"{_GITHUB_API}/repos/{owner}/{repo}")
        return (
            f"**{d['full_name']}**\n"
            f"Description: {d.get('description', 'N/A')}\n"
            f"Stars: {d['stargazers_count']}  |  Forks: {d['forks_count']}  |  Open Issues: {d['open_issues_count']}\n"
            f"Language: {d.get('language', 'N/A')}  |  License: {(d.get('license') or {}).get('name', 'N/A')}\n"
            f"Default branch: {d['default_branch']}\n"
            f"URL: {d['html_url']}"
        )

    async def _list_files(self, **kw: Any) -> str:
        owner, repo = kw.get("owner", ""), kw.get("repo", "")
        path = kw.get("path", "")
        if not owner or not repo:
            return "Error: 'owner' and 'repo' are required."
        params = {}
        if kw.get("ref"):
            params["ref"] = kw["ref"]
        data = await self._api_get(f"{_GITHUB_API}/repos/{owner}/{repo}/contents/{path}", params)
        if not isinstance(data, list):
            return f"'{path}' is a file. Use 'read_file' instead."
        lines = [f"Contents of {owner}/{repo}/{path or '(root)'}:\n"]
        for item in data:
            icon = "dir" if item["type"] == "dir" else "file"
            size = f" ({item.get('size', 0)} B)" if item["type"] == "file" else ""
            lines.append(f"  [{icon}] {item['name']}{size}")
        return "\n".join(lines)

    async def _read_file(self, **kw: Any) -> str:
        owner, repo = kw.get("owner", ""), kw.get("repo", "")
        path = kw.get("path", "README.md")
        if not owner or not repo:
            return "Error: 'owner' and 'repo' are required."
        params = {}
        if kw.get("ref"):
            params["ref"] = kw["ref"]
        data = await self._api_get(f"{_GITHUB_API}/repos/{owner}/{repo}/contents/{path}", params)
        if isinstance(data, list):
            return f"'{path}' is a directory. Use 'list_files' instead."
        if data.get("encoding") == "base64":
            content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            if len(content) > 5000:
                content = content[:5000] + "\n\n... (truncated at 5000 chars)"
            return f"**{path}** ({data.get('size', '?')} bytes):\n\n{content}"
        return f"Cannot decode file at '{path}'."

    async def _list_issues(self, **kw: Any) -> str:
        owner, repo = kw.get("owner", ""), kw.get("repo", "")
        if not owner or not repo:
            return "Error: 'owner' and 'repo' are required."
        state = kw.get("state", "open")
        data = await self._api_get(
            f"{_GITHUB_API}/repos/{owner}/{repo}/issues",
            {"state": state, "per_page": 10},
        )
        if not data:
            return f"No {state} issues in {owner}/{repo}."
        lines = [f"{state.capitalize()} issues in {owner}/{repo}:\n"]
        for i in data:
            kind = "PR" if "pull_request" in i else "Issue"
            labels = ", ".join(l["name"] for l in i.get("labels", []))
            lines.append(f"- #{i['number']} [{kind}] {i['title']}" + (f"  ({labels})" if labels else ""))
        return "\n".join(lines)

    async def _get_issue(self, **kw: Any) -> str:
        owner, repo = kw.get("owner", ""), kw.get("repo", "")
        number = kw.get("number")
        if not owner or not repo or not number:
            return "Error: 'owner', 'repo', and 'number' are required."
        issue = await self._api_get(f"{_GITHUB_API}/repos/{owner}/{repo}/issues/{number}")
        body = (issue.get("body") or "No description.")[:1500]
        kind = "Pull Request" if "pull_request" in issue else "Issue"
        comments = await self._api_get(
            f"{_GITHUB_API}/repos/{owner}/{repo}/issues/{number}/comments", {"per_page": 5}
        )
        comment_lines = [f"  @{c['user']['login']}: {(c.get('body') or '')[:300]}" for c in comments[:5]]
        result = (
            f"**{kind} #{issue['number']}**: {issue['title']}\n"
            f"State: {issue['state']}  |  Author: @{issue['user']['login']}\n"
            f"Labels: {', '.join(l['name'] for l in issue.get('labels', [])) or 'none'}\n\n{body}"
        )
        if comment_lines:
            result += "\n\nRecent comments:\n" + "\n".join(comment_lines)
        return result

    # ── PR-specific read actions ─────────────────────────────────────────

    async def _list_prs(self, **kw: Any) -> str:
        owner, repo = kw.get("owner", ""), kw.get("repo", "")
        if not owner or not repo:
            return "Error: 'owner' and 'repo' are required."
        state = kw.get("state", "open")
        data = await self._api_get(
            f"{_GITHUB_API}/repos/{owner}/{repo}/pulls",
            {"state": state, "per_page": 10},
        )
        if not data:
            return f"No {state} pull requests in {owner}/{repo}."
        lines = [f"{state.capitalize()} PRs in {owner}/{repo}:\n"]
        for pr in data:
            lines.append(
                f"- #{pr['number']} {pr['title']}\n"
                f"  {pr['head']['ref']} -> {pr['base']['ref']}  |  "
                f"Author: @{pr['user']['login']}  |  State: {pr['state']}"
            )
        return "\n".join(lines)

    async def _get_pr(self, **kw: Any) -> str:
        owner, repo = kw.get("owner", ""), kw.get("repo", "")
        number = kw.get("number")
        if not owner or not repo or not number:
            return "Error: 'owner', 'repo', and 'number' are required."
        pr = await self._api_get(f"{_GITHUB_API}/repos/{owner}/{repo}/pulls/{number}")
        body = (pr.get("body") or "No description.")[:1500]
        reviews = await self._api_get(
            f"{_GITHUB_API}/repos/{owner}/{repo}/pulls/{number}/reviews", {"per_page": 5}
        )
        review_lines = [
            f"  @{r['user']['login']} — {r['state']}" + (f": {r['body'][:200]}" if r.get("body") else "")
            for r in reviews[:5]
        ]
        files = await self._api_get(
            f"{_GITHUB_API}/repos/{owner}/{repo}/pulls/{number}/files", {"per_page": 20}
        )
        file_lines = [f"  {f['status']}: {f['filename']} (+{f['additions']} -{f['deletions']})" for f in files[:20]]

        result = (
            f"**PR #{pr['number']}**: {pr['title']}\n"
            f"State: {pr['state']}  |  Mergeable: {pr.get('mergeable', 'unknown')}\n"
            f"Author: @{pr['user']['login']}\n"
            f"Branch: {pr['head']['ref']} -> {pr['base']['ref']}\n"
            f"Commits: {pr['commits']}  |  Changed files: {pr['changed_files']}  |  "
            f"+{pr['additions']} -{pr['deletions']}\n\n{body}"
        )
        if file_lines:
            result += "\n\nChanged files:\n" + "\n".join(file_lines)
        if review_lines:
            result += "\n\nReviews:\n" + "\n".join(review_lines)
        return result

    async def _get_pr_diff(self, **kw: Any) -> str:
        owner, repo = kw.get("owner", ""), kw.get("repo", "")
        number = kw.get("number")
        if not owner or not repo or not number:
            return "Error: 'owner', 'repo', and 'number' are required."
        diff = await self._api_get_text(f"{_GITHUB_API}/repos/{owner}/{repo}/pulls/{number}")
        if len(diff) > 8000:
            diff = diff[:8000] + "\n\n... (diff truncated at 8000 chars)"
        return f"Diff for PR #{number}:\n\n```diff\n{diff}\n```"

    # ── Write actions (require GITHUB_TOKEN) ─────────────────────────────

    async def _create_issue(self, **kw: Any) -> str:
        owner, repo = kw.get("owner", ""), kw.get("repo", "")
        title, body = kw.get("title", ""), kw.get("body", "")
        if not owner or not repo or not title:
            return "Error: 'owner', 'repo', and 'title' are required."
        data = await self._api_post(
            f"{_GITHUB_API}/repos/{owner}/{repo}/issues",
            {"title": title, "body": body},
        )
        return f"Created issue #{data['number']}: {data['title']}\nURL: {data['html_url']}"

    async def _comment_on_issue(self, **kw: Any) -> str:
        owner, repo = kw.get("owner", ""), kw.get("repo", "")
        number, body = kw.get("number"), kw.get("body", "")
        if not owner or not repo or not number or not body:
            return "Error: 'owner', 'repo', 'number', and 'body' are required."
        data = await self._api_post(
            f"{_GITHUB_API}/repos/{owner}/{repo}/issues/{number}/comments",
            {"body": body},
        )
        return f"Comment posted on issue #{number}.\nURL: {data['html_url']}"

    async def _comment_on_pr(self, **kw: Any) -> str:
        owner, repo = kw.get("owner", ""), kw.get("repo", "")
        number, body = kw.get("number"), kw.get("body", "")
        if not owner or not repo or not number or not body:
            return "Error: 'owner', 'repo', 'number', and 'body' are required."
        data = await self._api_post(
            f"{_GITHUB_API}/repos/{owner}/{repo}/issues/{number}/comments",
            {"body": body},
        )
        return f"Comment posted on PR #{number}.\nURL: {data['html_url']}"

    async def _update_pr(self, **kw: Any) -> str:
        owner, repo = kw.get("owner", ""), kw.get("repo", "")
        number = kw.get("number")
        if not owner or not repo or not number:
            return "Error: 'owner', 'repo', and 'number' are required."
        payload: dict[str, Any] = {}
        if kw.get("title"):
            payload["title"] = kw["title"]
        if kw.get("body"):
            payload["body"] = kw["body"]
        if kw.get("state"):
            payload["state"] = kw["state"]
        if not payload:
            return "Error: provide at least one of 'title', 'body', or 'state' to update."
        data = await self._api_patch(
            f"{_GITHUB_API}/repos/{owner}/{repo}/pulls/{number}", payload
        )
        return (
            f"PR #{data['number']} updated.\n"
            f"Title: {data['title']}\n"
            f"State: {data['state']}\n"
            f"URL: {data['html_url']}"
        )

    async def _merge_pr(self, **kw: Any) -> str:
        owner, repo = kw.get("owner", ""), kw.get("repo", "")
        number = kw.get("number")
        if not owner or not repo or not number:
            return "Error: 'owner', 'repo', and 'number' are required."
        data = await self._api_put(
            f"{_GITHUB_API}/repos/{owner}/{repo}/pulls/{number}/merge",
            {"merge_method": "merge"},
        )
        if data.get("merged"):
            return f"PR #{number} merged successfully. SHA: {data.get('sha', 'N/A')}"
        return f"PR #{number} could not be merged: {data.get('message', 'unknown reason')}"

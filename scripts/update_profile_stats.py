#!/usr/bin/env python3
"""Generate stable, repository-local GitHub activity cards."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
USERNAME = "Rhongomiant1227"
INK = "#1f2328"
MUTED = "#57606a"
BLUE = "#315f9c"
LINE = "#d0d7de"
COLORS = ["#315f9c", "#58b6a8", "#e97868", "#9784e5", "#ed9868"]


def api(path: str):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def esc(value: object) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def svg_card(title: str, body: str, height: int = 184) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="620" height="{height}" viewBox="0 0 620 {height}" role="img" aria-label="{esc(title)}">
  <rect width="619" height="{height-1}" x=".5" y=".5" rx="10" fill="#fff" stroke="{LINE}"/>
  <text x="22" y="34" fill="{BLUE}" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif" font-size="14" font-weight="600">{esc(title)}</text>
  {body}
</svg>\n'''


def make_stats(user: dict, repos: list[dict]) -> str:
    stars = sum(int(repo.get("stargazers_count", 0)) for repo in repos)
    forks = sum(int(repo.get("forks_count", 0)) for repo in repos)
    rows = [("Public repositories", user.get("public_repos", 0), COLORS[0]), ("Stars earned", stars, COLORS[2]), ("Followers", user.get("followers", 0), COLORS[1]), ("Forks received", forks, COLORS[3])]
    body = [f'<text x="22" y="72" fill="{INK}" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif" font-size="34" font-weight="700">{esc(user.get("public_repos", 0))}</text>', f'<text x="126" y="70" fill="{MUTED}" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif" font-size="13">public repositories</text>']
    for index, (label, value, color) in enumerate(rows):
        y = 101 + index * 18
        body.append(f'<circle cx="27" cy="{y-4}" r="4" fill="{color}"/><text x="40" y="{y}" fill="{MUTED}" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif" font-size="12">{esc(label)}</text><text x="348" y="{y}" fill="{INK}" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif" font-size="12" font-weight="600">{esc(value)}</text>')
    return svg_card(f"{USERNAME}'s GitHub activity", "".join(body))


def make_languages(repos: list[dict]) -> str:
    counts: dict[str, int] = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        for language, size in api(f"/repos/{repo['full_name']}/languages").items():
            counts[language] = counts.get(language, 0) + int(size)
    top = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:5]
    total = sum(counts.values()) or 1
    x = 22
    bar = []
    for index, (language, count) in enumerate(top):
        width = max(12, round(420 * count / total))
        bar.append(f'<rect x="{x}" y="55" width="{width}" height="12" fill="{COLORS[index % len(COLORS)]}"/>')
        x += width
    body = ["".join(bar)]
    for index, (language, count) in enumerate(top):
        col = index % 2
        row = index // 2
        x = 22 + col * 220
        y = 98 + row * 30
        pct = round(count * 100 / total, 1)
        body.append(f'<circle cx="{x+5}" cy="{y-4}" r="5" fill="{COLORS[index % len(COLORS)]}"/><text x="{x+18}" y="{y}" fill="{MUTED}" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif" font-size="12">{esc(language)} {pct}%</text>')
    if not top:
        body.append(f'<text x="22" y="90" fill="{MUTED}" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif" font-size="13">No public language data yet</text>')
    return svg_card("Most used languages", "".join(body))


def main() -> None:
    user = api(f"/users/{USERNAME}")
    repos = []
    page = 1
    while True:
        batch = api(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner&sort=updated")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "github-stats.svg").write_text(make_stats(user, repos), encoding="utf-8")
    (ASSETS / "github-languages.svg").write_text(make_languages(repos), encoding="utf-8")


if __name__ == "__main__":
    main()

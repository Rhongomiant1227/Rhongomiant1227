#!/usr/bin/env python3
"""Generate stable, repository-local GitHub activity cards."""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from profile_images import build_activity_images


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


def svg_card(title: str, body: str, height: int = 220) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="{height}" viewBox="0 0 400 {height}" role="img" aria-label="{esc(title)}">
  <rect width="399" height="{height-1}" x=".5" y=".5" rx="8" fill="#fff" stroke="{LINE}"/>
  <text x="20" y="34" fill="{BLUE}" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif" font-size="17" font-weight="600">{esc(title)}</text>
  {body}
</svg>\n'''


def make_stats(user: dict, repos: list[dict]) -> str:
    stars = sum(int(repo.get("stargazers_count", 0)) for repo in repos)
    forks = sum(int(repo.get("forks_count", 0)) for repo in repos)
    rows = [("Public repositories", user.get("public_repos", 0), COLORS[0]), ("Stars earned", stars, COLORS[2]), ("Followers", user.get("followers", 0), COLORS[1]), ("Forks received", forks, COLORS[3])]
    body = [f'<text x="20" y="78" fill="{INK}" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif" font-size="34" font-weight="700">{esc(user.get("public_repos", 0))}</text>', f'<text x="84" y="76" fill="{MUTED}" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif" font-size="15">public repositories</text>']
    for index, (label, value, color) in enumerate(rows):
        y = 112 + index * 27
        body.append(f'<circle cx="25" cy="{y-5}" r="4" fill="{color}"/><text x="39" y="{y}" fill="{MUTED}" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif" font-size="16">{esc(label)}</text><text x="378" y="{y}" text-anchor="end" fill="{INK}" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif" font-size="16" font-weight="600">{esc(value)}</text>')
    return svg_card("Public activity", "".join(body))


def make_languages(repos: list[dict]) -> str:
    counts: dict[str, int] = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        for language, size in api(f"/repos/{repo['full_name']}/languages").items():
            counts[language] = counts.get(language, 0) + int(size)
    top = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:5]
    total = sum(counts.values()) or 1
    remaining = sum(counts.values()) - sum(count for _, count in top)
    if remaining:
        top.append(("Other", remaining))
    x = 20
    bar = []
    for index, (language, count) in enumerate(top):
        width = 360 * count / total
        color = COLORS[index] if index < len(COLORS) else "#8c959f"
        bar.append(f'<rect x="{x:.2f}" y="57" width="{width:.2f}" height="12" fill="{color}"/>')
        x += width
    body = ["".join(bar)]
    for index, (language, count) in enumerate(top):
        col = index % 2
        row = index // 2
        x = 20 + col * 188
        y = 106 + row * 39
        pct = round(count * 100 / total, 1)
        color = COLORS[index] if index < len(COLORS) else "#8c959f"
        body.append(f'<circle cx="{x+5}" cy="{y-5}" r="5" fill="{color}"/><text x="{x+18}" y="{y}" fill="{MUTED}" font-family="-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif" font-size="14">{esc(language)} {pct}%</text>')
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
    build_activity_images()


if __name__ == "__main__":
    main()

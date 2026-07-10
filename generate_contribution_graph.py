"""
Generates a numbered GitHub contribution heatmap SVG (dark theme, counts inline),
using YOUR real contribution data via GitHub's GraphQL API.

Setup:
  1. Create a token at https://github.com/settings/tokens
     (classic token, no special scopes needed for public contribution data)
  2. Run:  export GITHUB_TOKEN=ghp_yourtokenhere
  3. Run:  python generate_contribution_graph.py Sriram-Nambiar
  4. Output: contributions.svg — embed it in your README, e.g.:
     ![contributions](contributions.svg)
     or upload it and use its raw URL.
"""

import os
import sys
import json
import urllib.request

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

def fetch_contributions(username, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": username}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return weeks

def level_color(v):
    if v == 0:
        return "#161b22"
    if v < 5:
        return "#0e4429"
    if v < 10:
        return "#006d32"
    if v < 20:
        return "#26a641"
    return "#39d353"

def build_svg(weeks):
    cell = 34
    gap = 3
    left_pad = 40
    top_pad = 30
    cols = len(weeks)
    rows = 7
    width = left_pad + cols * (cell + gap)
    height = top_pad + rows * (cell + gap)

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
    svg.append(f'<rect width="{width}" height="{height}" fill="#0d1117"/>')

    day_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for r, label in day_labels.items():
        y = top_pad + r * (cell + gap) + cell / 2 + 4
        svg.append(f'<text x="4" y="{y}" fill="#8b949e" font-size="11" font-family="sans-serif">{label}</text>')

    last_month = None
    for c, week in enumerate(weeks):
        days = week["contributionDays"]
        if days:
            month = days[0]["date"][5:7]
            if month != last_month:
                x = left_pad + c * (cell + gap)
                svg.append(f'<text x="{x}" y="16" fill="#8b949e" font-size="11" font-family="sans-serif">{days[0]["date"][:7]}</text>')
                last_month = month
        for r, day in enumerate(days):
            x = left_pad + c * (cell + gap)
            y = top_pad + r * (cell + gap)
            v = day["contributionCount"]
            color = level_color(v)
            text_color = "#6e7681" if v == 0 else "#e6edf3"
            svg.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" fill="{color}"/>')
            svg.append(f'<text x="{x + cell/2}" y="{y + cell/2 + 4}" fill="{text_color}" font-size="10" font-weight="600" font-family="sans-serif" text-anchor="middle">{v}</text>')

    svg.append("</svg>")
    return "\n".join(svg)

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "Sriram-Nambiar"
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Set GITHUB_TOKEN first: export GITHUB_TOKEN=ghp_yourtokenhere")
        sys.exit(1)

    weeks = fetch_contributions(username, token)
    svg = build_svg(weeks)
    with open("contributions.svg", "w") as f:
        f.write(svg)
    print("Wrote contributions.svg")
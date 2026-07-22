"""
Generates a numbered GitHub contribution heatmap SVG (dark theme, counts inline),
using YOUR real contribution data via GitHub's GraphQL API.

Setup:
  1. Create a token at https://github.com/settings/tokens
     (classic token, no special scopes needed for public contribution data)
  2. Run:  export GITHUB_TOKEN=ghp_yourtokenhere
  3. Run:  python generate_contribution_graph.py Sriram-Nambiar --weeks 26
  4. Output: contributions.svg — embed it in your README, e.g.:
     ![contributions](contributions.svg)
     or upload it and use its raw URL.

Options:
  --weeks N            only show the most recent N weeks (default: 26, ~6 months).
                        Use 0 to show the full year. This keeps the image legible
                        when embedded in a narrow README column, since more columns
                        means smaller cells once GitHub scales the image to fit.
  --start YYYY-MM-DD    alternative to --weeks: only include weeks on/after this
                        fixed date. If both are given, --start takes priority.
"""

import os
import sys
import json
import argparse
import urllib.request
from datetime import date

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

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def trim_weeks_by_date(weeks, start_date):
    if not start_date:
        return weeks
    return [
        week for week in weeks
        if week["contributionDays"] and week["contributionDays"][-1]["date"] >= start_date
    ]

def trim_weeks_by_count(weeks, num_weeks):
    if not num_weeks or num_weeks <= 0:
        return weeks
    return weeks[-num_weeks:]

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
                month_name = MONTH_NAMES[int(month) - 1]
                svg.append(f'<text x="{x}" y="16" fill="#8b949e" font-size="11" font-family="sans-serif">{month_name}</text>')
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
    parser = argparse.ArgumentParser()
    parser.add_argument("username", nargs="?", default="Sriram-Nambiar")
    parser.add_argument("--weeks", type=int, default=26,
                         help="Show only the most recent N weeks (default: 26). Use 0 for the full year.")
    parser.add_argument("--start", default=None,
                         help="Only show weeks on/after this fixed date, e.g. 2026-01-01. Overrides --weeks if set.")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Set GITHUB_TOKEN first: export GITHUB_TOKEN=ghp_yourtokenhere")
        sys.exit(1)

    weeks = fetch_contributions(args.username, token)

    if args.start:
        weeks = trim_weeks_by_date(weeks, args.start)
    else:
        weeks = trim_weeks_by_count(weeks, args.weeks)

    svg = build_svg(weeks)
    with open("contributions.svg", "w") as f:
        f.write(svg)
    print(f"Wrote contributions.svg ({len(weeks)} weeks)")
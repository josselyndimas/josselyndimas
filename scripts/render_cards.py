#!/usr/bin/env python3
"""Generate static, coffee-toned SVG cards for Josselyn's GitHub profile."""
import json
import re
import urllib.request
from pathlib import Path
from html.parser import HTMLParser
from datetime import date, datetime, timedelta
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "cards"
DATA = ROOT / "data"
CARDS.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)
USER = "josselyndimas"

PANEL = "#211A16"
LINE = "#4B392C"
INK = "#F0E4D5"
MUTED = "#B9A18A"
COFFEE = "#79583F"
CARAMEL = "#B88D68"
CREAM = "#E2C7A7"
SHADES = ["#2B211B", "#493629", "#73533D", "#A77B55", "#D5B18A"]


class ContributionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.days = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        day = attrs.get("data-date") or attrs.get("data-day")
        if not day or not re.match(r"^\d{4}-\d\d-\d\d$", day):
            return
        level, count = attrs.get("data-level"), attrs.get("data-count")
        if level is None and count is None:
            return
        try:
            self.days[day] = {
                "level": min(4, max(0, int(level or 0))),
                "count": int(count) if count is not None else None
            }
        except ValueError:
            pass


def collect():
    url = f"https://github.com/users/{USER}/contributions"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25) as response:
            page = response.read().decode("utf-8", "replace")
        parser = ContributionParser()
        parser.feed(page)
        if len(parser.days) < 100:
            raise RuntimeError(f"Only {len(parser.days)} contribution days parsed")
        payload = {
            "fetched_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "source": url,
            "days": parser.days
        }
        (DATA / "contributions.json").write_text(json.dumps(payload, indent=2), encoding="utf8")
        return parser.days, True
    except Exception as exc:
        cache = DATA / "contributions.json"
        if cache.exists():
            print("Using cached contribution data:", exc)
            return json.loads(cache.read_text(encoding="utf8"))["days"], True
        print("Could not retrieve contribution data:", exc)
        return {}, False


DAYS, AVAILABLE = collect()


def shell(width, height, title, subtitle):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img">'
        f'<title>{title}</title><rect width="{width}" height="{height}" rx="22" fill="{PANEL}"/>'
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="21" '
        f'stroke="{LINE}" stroke-width="2" fill="none"/>'
        f'<circle cx="29" cy="27" r="5" fill="#B88D68"/>'
        f'<circle cx="46" cy="27" r="5" fill="#79583F"/>'
        f'<circle cx="63" cy="27" r="5" fill="#D5B18A"/>'
        f'<text x="83" y="32" font-family="Courier New,monospace" font-size="12" '
        f'letter-spacing="1" fill="{MUTED}">josselyn@github ~/ {subtitle}</text>'
    )


def save(name, svg):
    (CARDS / name).write_text(svg + "</svg>", encoding="utf8")


# Single, static introduction panel. The portrait is placed beside it in README.md.
svg = shell(900, 390, "Josselyn Dimas — Software Development Engineering student", "hello")
svg += f"""
<text x="43" y="91" font-family="Courier New,monospace" font-size="13"
      letter-spacing="1.5" fill="{CARAMEL}">SOFTWARE DEVELOPMENT ENGINEERING STUDENT</text>
<text x="39" y="205" font-family="Georgia,serif" font-size="112" fill="{INK}">Josselyn</text>
<text x="43" y="292" font-family="Georgia,serif" font-size="82"
      font-style="italic" fill="{CREAM}">Dimas</text>
<path d="M45 316 H520" stroke="{COFFEE}" stroke-width="2"/>
<text x="45" y="351" font-family="Arial,Helvetica,sans-serif"
      font-size="18" fill="{MUTED}">I build useful software and turn ideas into practical solutions.</text>
"""
save("hero.svg", svg)

# Contribution heatmap uses only data returned by GitHub; no fabricated squares.
today = date.today()
start = today - timedelta(days=364)
start -= timedelta(days=(start.weekday() + 1) % 7)
weeks, cell, gap, left, top = 53, 11, 3, 47, 83
svg = shell(900, 235, "GitHub contribution calendar", "contributions")
svg += (
    f'<text x="35" y="60" font-family="Georgia,serif" font-size="22" fill="{INK}">'
    f'Every day, <tspan font-style="italic" fill="{CREAM}">in coffee</tspan></text>'
    f'<text x="865" y="59" text-anchor="end" font-family="Courier New,monospace" '
    f'font-size="11" fill="{MUTED}">REAL GITHUB ACTIVITY</text>'
)
for week in range(weeks):
    for weekday in range(7):
        current = start + timedelta(days=week * 7 + weekday)
        if current > today:
            continue
        info = DAYS.get(current.isoformat())
        level = info["level"] if info else 0
        fill = SHADES[level] if AVAILABLE else SHADES[0]
        title = f'{current.isoformat()}: {info.get("count", "level " + str(level))} contributions' if info else f'{current.isoformat()}: no public contribution data'
        svg += (
            f'<rect x="{left + week * (cell + gap)}" y="{top + weekday * (cell + gap)}" '
            f'width="{cell}" height="{cell}" rx="2.2" fill="{fill}">'
            f'<title>{title}</title></rect>'
        )
footer = ("Public GitHub contribution intensity · less → more" if AVAILABLE
          else "Contribution data unavailable; no activity has been fabricated")
svg += f'<text x="35" y="211" font-family="Arial,sans-serif" font-size="12" fill="{MUTED}">{footer}</text>'
save("heatmap.svg", svg)

# Monthly bars: static and based on collected contribution values.
months = []
year, month = today.year, today.month
for _ in range(12):
    months.append((year, month))
    month -= 1
    if month < 1:
        month, year = 12, year - 1
months.reverse()
sums = defaultdict(int)
for day, value in DAYS.items():
    try:
        yy, mm, _ = map(int, day.split("-"))
        sums[(yy, mm)] += value["count"] if value.get("count") is not None else value["level"]
    except (ValueError, TypeError):
        pass
maximum = max([sums[item] for item in months] + [1])
has_counts = AVAILABLE and bool(DAYS) and all(v.get("count") is not None for v in DAYS.values())

svg = shell(900, 300, "Monthly GitHub activity", "monthly_activity")
subtitle = "Verified contributions per month" if has_counts else (
    "Relative activity from GitHub intensity levels" if AVAILABLE else
    "Waiting for verified contribution data"
)
svg += (
    f'<text x="35" y="61" font-family="Georgia,serif" font-size="23" fill="{INK}">A year in review</text>'
    f'<text x="35" y="83" font-family="Arial,sans-serif" font-size="13" fill="{MUTED}">{subtitle}</text>'
)
for index, item in enumerate(months):
    value = sums[item]
    height = round(130 * value / maximum) if AVAILABLE else 0
    x = 52 + index * 67
    if height:
        svg += f'<rect x="{x}" y="{240-height}" width="34" height="{height}" rx="5" fill="{CREAM if value == maximum else COFFEE}"/>'
    svg += (
        f'<text x="{x+17}" y="263" text-anchor="middle" fill="{MUTED}" '
        f'font-family="Arial,sans-serif" font-size="12">{date(item[0], item[1], 1).strftime("%b")}</text>'
    )
svg += f'<line x1="42" x2="852" y1="240" y2="240" stroke="{LINE}"/>'
save("activity.svg", svg)

print("Generated static coffee-themed cards. Verified activity available:", AVAILABLE)

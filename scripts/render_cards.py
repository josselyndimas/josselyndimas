#!/usr/bin/env python3
"""Render Josselyn's coffee-toned GitHub profile cards from verified public activity."""
import os
import json
import re
import html
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from datetime import date, datetime, timedelta
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "cards"
CARDS.mkdir(exist_ok=True)
DATA = ROOT / "data"
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
            level = min(4, max(0, int(level or 0)))
            count = int(count) if count is not None else None
            old = self.days.get(day)
            if old is None or count is not None:
                self.days[day] = {"level": level, "count": count}
        except ValueError:
            pass


def collect():
    url = f"https://github.com/users/{USER}/contributions"
    try:
        request = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 JosselynProfile/1.0",
            "Accept": "text/html"
        })
        with urllib.request.urlopen(request, timeout=25) as response:
            page = response.read().decode("utf-8", "replace")
        parser = ContributionParser()
        parser.feed(page)
        days = parser.days
        if len(days) < 100:
            raise RuntimeError(f"Only {len(days)} calendar cells parsed")
        info = {
            "fetched_at": datetime.now().isoformat(timespec="seconds") + "Z",
            "source": url,
            "days": days
        }
        (DATA / "contributions.json").write_text(
            json.dumps(info, indent=2), encoding="utf8"
        )
        return days, True
    except Exception as error:
        cached = DATA / "contributions.json"
        if cached.exists():
            print("Using previously fetched data:", error)
            return json.loads(cached.read_text(encoding="utf8"))["days"], True
        print("Activity unavailable; rendering an empty calendar:", error)
        return {}, False


DAYS, AVAILABLE = collect()


def esc(value):
    return html.escape(str(value), quote=True)


def styles():
    return """<style>
    text{font-family:Arial,Helvetica,sans-serif}
    .serif{font-family:Georgia,'Times New Roman',serif}
    .mono{font-family:'Courier New',monospace;letter-spacing:1px}
    .enter{animation:appear .8s ease both}
    .sq{animation:appear .35s ease both}
    .bar{transform-box:fill-box;transform-origin:50% 100%;animation:grow 1s cubic-bezier(.2,.8,.2,1) both}
    @keyframes appear{from{opacity:0}to{opacity:1}}
    @keyframes grow{from{transform:scaleY(.03)}to{transform:scaleY(1)}}
    @media(prefers-reduced-motion:reduce){.sq,.bar,.enter{animation:none!important}}
    </style>"""


def shell(width, height, title, subtitle=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" aria-label="{esc(title)}">'
        f'<title>{esc(title)}</title><rect width="{width}" height="{height}" rx="22" fill="{PANEL}"/>'
        f'<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="21" stroke="{LINE}" '
        f'stroke-width="2" fill="none"/>{styles()}'
        f'<circle cx="29" cy="27" r="5" fill="#B88D68"/>'
        f'<circle cx="46" cy="27" r="5" fill="#79583F"/>'
        f'<circle cx="63" cy="27" r="5" fill="#D5B18A"/>'
        f'<text x="83" y="32" class="mono" font-size="12" fill="{MUTED}">'
        f'josselyn@github / {esc(subtitle)}</text>'
    )


def save(name, content):
    (CARDS / name).write_text(content + "</svg>", encoding="utf8")


# Large editorial-style introduction card.
svg = shell(900, 360, "Josselyn Dimas - Junior Software Engineer", "hello")
svg += f"""
<text x="43" y="91" class="mono enter" font-size="13" fill="{CARAMEL}">JUNIOR SOFTWARE ENGINEER / EL SALVADOR</text>
<text x="39" y="190" class="serif enter" font-size="91" fill="{INK}">Josselyn</text>
<text x="43" y="263" class="serif enter" font-size="73" font-style="italic" fill="{CREAM}">Dimas</text>
<path d="M45 286 H520" stroke="{COFFEE}" stroke-width="2"/>
<text x="45" y="320" font-size="17" fill="{MUTED}" class="enter">Web applications · REST APIs · automated testing</text>
<rect x="744" y="94" width="12" height="12" rx="2" fill="{COFFEE}"/>
<rect x="762" y="94" width="12" height="12" rx="2" fill="{CARAMEL}"/>
<rect x="780" y="94" width="12" height="12" rx="2" fill="{CREAM}"/>
<rect x="744" y="112" width="12" height="12" rx="2" fill="{CREAM}"/>
<rect x="762" y="112" width="12" height="12" rx="2" fill="{COFFEE}"/>
<rect x="780" y="112" width="12" height="12" rx="2" fill="{CARAMEL}"/>
<text x="744" y="157" class="mono" font-size="10" fill="{MUTED}">CODE / CREATE / LEARN</text>
"""
save("hero.svg", svg)

# Contribution heatmap: only actual GitHub activity is shown.
today = date.today()
start = today - timedelta(days=364)
start -= timedelta(days=(start.weekday() + 1) % 7)
weeks, cell, gap, left, top = 53, 11, 3, 47, 83
svg = shell(900, 235, "GitHub contribution calendar", "contributions")
svg += (
    f'<text x="35" y="60" font-size="21" font-weight="bold" fill="{INK}">'
    f'Every day, <tspan class="serif" font-style="italic" fill="{CREAM}">in coffee</tspan></text>'
    f'<text x="865" y="59" text-anchor="end" class="mono" font-size="11" fill="{MUTED}">'
    f'REAL GITHUB ACTIVITY</text>'
)
for week in range(weeks):
    for weekday in range(7):
        current = start + timedelta(days=week * 7 + weekday)
        if current > today:
            continue
        info = DAYS.get(current.isoformat())
        level = info["level"] if info else 0
        fill = SHADES[level] if AVAILABLE else SHADES[0]
        delay = min(3.8, .25 + week * .04)
        label = str(info.get("count", "")) if info else "0"
        if not AVAILABLE:
            label = "pending"
        svg += (
            f'<rect class="sq" style="animation-delay:{delay:.2f}s" '
            f'x="{left + week * (cell + gap)}" y="{top + weekday * (cell + gap)}" '
            f'width="{cell}" height="{cell}" rx="2.2" fill="{fill}">'
            f'<title>{current.isoformat()}: {label} contributions</title></rect>'
        )
svg += (
    f'<text x="35" y="211" font-size="12" fill="{MUTED}">'
    + ("Public GitHub contribution intensity · less → more" if AVAILABLE
       else "Waiting for verified GitHub contribution data")
    + "</text>"
)
save("heatmap.svg", svg)

# Monthly activity uses real counts when available, otherwise labels intensity levels.
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
        sums[(yy, mm)] += (
            value["count"] if value.get("count") is not None else value["level"]
        )
    except (ValueError, TypeError):
        continue
maximum = max([sums[item] for item in months] + [1])
has_counts = AVAILABLE and all(
    value.get("count") is not None for value in DAYS.values()
)
svg = shell(900, 300, "Monthly GitHub activity", "monthly_activity")
svg += (
    f'<text x="35" y="61" font-size="22" font-weight="bold" fill="{INK}">'
    f'A year in review</text>'
    f'<text x="35" y="83" font-size="13" fill="{MUTED}">'
    + ("Verified contributions per month" if has_counts else
       "Relative activity from GitHub intensity levels" if AVAILABLE else
       "Waiting for verified contribution data")
    + "</text>"
)
for index, item in enumerate(months):
    value = sums[item]
    height = round(130 * value / maximum) if AVAILABLE else 0
    x = 52 + index * 67
    if height:
        svg += (
            f'<rect x="{x}" y="{240-height}" width="34" height="{height}" rx="5" '
            f'fill="{CREAM if value == maximum else COFFEE}" class="bar" '
            f'style="animation-delay:{index*.08:.2f}s"/>'
        )
    svg += (
        f'<text x="{x+17}" y="263" text-anchor="middle" fill="{MUTED}" '
        f'font-size="12">{date(item[0], item[1], 1).strftime("%b")}</text>'
    )
svg += f'<line x1="42" x2="852" y1="240" y2="240" stroke="{LINE}"/>'
save("activity.svg", svg)


def tile(filename, label, title, description, accent):
    content = shell(288, 202, title, label.lower())
    content += f'<text x="23" y="78" class="mono" font-size="11" fill="{accent}">{esc(label)}</text>'
    content += f'<text x="22" y="124" class="serif" font-size="28" fill="{INK}">{esc(title)}</text>'
    content += f'<text x="22" y="157" font-size="13" fill="{MUTED}">{esc(description)}</text>'
    content += f'<path d="M22 177 H260" stroke="{LINE}" stroke-width="1"/>'
    save(filename, content)


tile("build.svg", "01 / OPEN SOURCE", "Contribute", "Apache Fineract · Angular · Playwright", CREAM)
tile("learn.svg", "02 / FULL STACK", "Build", "React · Python · FastAPI · Maps", CARAMEL)
tile("connect.svg", "03 / CREATIVE TECH", "Create", "Education tools · music · code", MUTED)

print("Generated coffee-themed profile cards; verified activity:", AVAILABLE, "days:", len(DAYS))

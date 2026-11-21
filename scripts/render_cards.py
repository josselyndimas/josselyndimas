#!/usr/bin/env python3
"""Generate the profile cards (hero, heatmap, activity, languages) for josselyndimas.

Editorial style inspired by AviVashishta29's profile, recoloured with a
coffee palette. Only real public data is used; nothing is invented.

    python scripts/render_cards.py            # light cards (default)
    THEME=dark python scripts/render_cards.py # dark cards
"""
import base64
import html
import json
import os
import re
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS, DATA, ASSETS = ROOT / "cards", ROOT / "data", ROOT / "assets"
CARDS.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)

USER = "josselyndimas"
TAGLINE = ["I build useful software and turn ideas", "into practical solutions."]
EYEBROW = "SOFTWARE DEVELOPMENT ENGINEERING STUDENT"

# ---- palette ---------------------------------------------------------------
FONDO, CHOCOLATE, CAFE, CAFE_MEDIO = "#171513", "#29221D", "#49382D", "#795D48"
CARAMELO, BEIGE, CREMA, MARFIL = "#B18C6B", "#D3B99B", "#E4D4BD", "#F0E5D5"

THEMES = {
    "light": dict(card=MARFIL, line=CREMA, ink=FONDO, muted=CAFE_MEDIO, accent=CAFE_MEDIO,
                  shades=[CREMA, BEIGE, CARAMELO, CAFE_MEDIO, CAFE]),
    "dark": dict(card=CHOCOLATE, line=CAFE, ink=MARFIL, muted=CARAMELO, accent=BEIGE,
                 shades=[CAFE, CAFE_MEDIO, CARAMELO, BEIGE, MARFIL]),
}
T = THEMES.get(os.environ.get("THEME", "light"), THEMES["light"])
SERIF = "Georgia,'Times New Roman',serif"
SANS = "'Segoe UI',Arial,Helvetica,sans-serif"
MONO = "'Courier New',Consolas,monospace"

def esc(s):
    return html.escape(str(s), quote=True)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")


# ---- data: contributions ----------------------------------------------------
def parse_contributions(page):
    """GitHub's calendar: <td data-date id data-level> + <tool-tip for=id>N contributions on ...</tool-tip>."""
    cells = {}
    for m in re.finditer(r'data-date="(\d{4}-\d\d-\d\d)"\s+id="([^"]+)"\s+data-level="(\d)"', page):
        cells[m.group(2)] = {"date": m.group(1), "level": int(m.group(3))}
    days = {}
    for m in re.finditer(r'<tool-tip[^>]*\sfor="([^"]+)"[^>]*>\s*([^<]*)<', page):
        cell = cells.get(m.group(1))
        if not cell:
            continue
        n = re.match(r"\s*(\d+)\s+contribution", m.group(2))
        count = int(n.group(1)) if n else 0
        days[cell["date"]] = {"level": cell["level"], "count": count}
    return days


def collect_days():
    cache = DATA / "contributions.json"
    try:
        days = parse_contributions(fetch(f"https://github.com/users/{USER}/contributions"))
        if len(days) < 300:
            raise RuntimeError(f"only {len(days)} days parsed")
        cache.write_text(json.dumps({"fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                     "source": f"https://github.com/users/{USER}/contributions",
                                     "days": days}, indent=1), encoding="utf8")
        return days, True
    except Exception as exc:
        print("Contribution fetch failed:", exc)
        if cache.exists():
            cached = json.loads(cache.read_text(encoding="utf8"))["days"]
            if cached and all(v.get("count") is not None for v in cached.values()):
                return cached, True
        return {}, False


DAYS, OK = collect_days()
TODAY = datetime.now(timezone.utc).date()
ordered = sorted((date.fromisoformat(k), v) for k, v in DAYS.items() if date.fromisoformat(k) <= TODAY)

# ---- metrics ----------------------------------------------------------------
total = sum(v["count"] for _, v in ordered)
active = sum(1 for _, v in ordered if v["count"] > 0)
best_day, best = (max(ordered, key=lambda x: x[1]["count"]) if ordered else (None, {"count": 0}))
longest = run = 0
for _, v in ordered:
    run = run + 1 if v["count"] > 0 else 0
    longest = max(longest, run)
current = 0
for i, (d, v) in enumerate(reversed(ordered)):
    if v["count"] > 0:
        current += 1
    elif i == 0:  # today not counted yet; the streak may still be alive
        continue
    else:
        break


# ---- svg helpers ------------------------------------------------------------
def svg(w, h, title, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(title)}">'
            f'<title>{esc(title)}</title>{defs}'
            f'<rect width="{w}" height="{h}" rx="24" fill="{T["card"]}"/>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="23" fill="none" stroke="{T["line"]}" stroke-width="2"/>'
            f'{body}</svg>')


def save(name, content):
    (CARDS / name).write_text(content, encoding="utf8")


def text(x, y, s, size, fill, family=SANS, weight="normal", style="normal", anchor="start", spacing=0):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'font-style="{style}" text-anchor="{anchor}" letter-spacing="{spacing}" fill="{fill}">{esc(s)}</text>')


# ---- hero -------------------------------------------------------------------
portrait = base64.b64encode((ASSETS / "portrait-hero.png").read_bytes()).decode()
body = (
    f'<rect x="44" y="52" width="11" height="11" rx="2.5" fill="{T["accent"]}"/>'
    + text(66, 63, EYEBROW, 13, T["muted"], MONO, spacing=2)
    + text(40, 196, "Josselyn", 118, T["ink"], SERIF)
    + text(44, 284, "Dimas", 94, T["accent"], SERIF, style="italic")
    + text(46, 335, TAGLINE[0], 19, T["muted"]) + text(46, 361, TAGLINE[1], 19, T["muted"])
    + text(46, 396, f"github.com/{USER}", 14, T["ink"], MONO)
    + f'<image x="535" y="34" width="330" height="330" xlink:href="data:image/png;base64,{portrait}" '
      f'preserveAspectRatio="xMidYMax meet" style="image-rendering:pixelated"/>'
)
save("hero.svg", svg(900, 430, "Josselyn Dimas — Software Development Engineering student", body))

# ---- heatmap ----------------------------------------------------------------
cell, gap, left, top = 12, 3, 52, 92
body = (f'<text x="40" y="62" font-family="{SERIF}" font-size="27" fill="{T["ink"]}">Every day, <tspan font-style="italic" fill="{T["accent"]}">in coffee</tspan></text>'
        + text(860, 60, "REFRESHED DAILY", 11, T["muted"], MONO, anchor="end", spacing=2))
if OK and ordered:
    first = ordered[0][0]
    first -= timedelta(days=(first.weekday() + 1) % 7)  # back to Sunday
    for d, v in ordered:
        wk, wd = (d - first).days // 7, (d.weekday() + 1) % 7
        n = v["count"]
        body += (f'<rect x="{left + wk*(cell+gap)}" y="{top + wd*(cell+gap)}" width="{cell}" height="{cell}" rx="2.5" '
                 f'fill="{T["shades"][v["level"]]}"><title>{d.isoformat()}: {n} contribution{"s" if n != 1 else ""}</title></rect>')
    caption = f"{total} contributions in the last year"
else:
    caption = "Contribution data unavailable right now"
body += text(40, 226, caption, 13, T["muted"])
lx = 860 - 5 * 17 - 70
body += text(lx - 8, 226, "less", 12, T["muted"], anchor="end")
for i, c in enumerate(T["shades"]):
    body += f'<rect x="{lx + i*17}" y="215" width="12" height="12" rx="2.5" fill="{c}"/>'
body += text(lx + 5 * 17 + 4, 226, "more", 12, T["muted"])
save("heatmap.svg", svg(900, 250, "GitHub contributions in coffee tones", body))

# ---- activity: monthly bars + streaks + busiest day --------------------------
months, y, m = [], TODAY.year, TODAY.month
for _ in range(12):
    months.append((y, m))
    m -= 1
    if m < 1:
        m, y = 12, y - 1
months.reverse()
sums = defaultdict(int)
for d, v in ordered:
    sums[(d.year, d.month)] += v["count"]
peak = max([sums[k] for k in months] + [1])
body = (f'<text x="40" y="62" font-family="{SERIF}" font-size="25" fill="{T["ink"]}">A year in <tspan font-style="italic" fill="{T["accent"]}">review</tspan></text>'
        + text(40, 86, "Contributions per month, last 12 months", 13, T["muted"]))
base = 248
for i, k in enumerate(months):
    x, n = 44 + i * 47, sums[k]
    h = round(120 * n / peak)
    top_y = base - max(h, 4)
    shade = T["shades"][4] if n == peak and n > 0 else (T["shades"][2] if n else T["shades"][0])
    body += f'<rect x="{x}" y="{top_y}" width="34" height="{max(h, 4)}" rx="6" fill="{shade}"/>'
    if n:
        body += text(x + 17, top_y - 7, n, 11, T["ink"], anchor="middle")
    body += text(x + 17, base + 22, date(k[0], k[1], 1).strftime("%b"), 12, T["muted"], anchor="middle")
body += f'<line x1="40" x2="610" y1="{base}" y2="{base}" stroke="{T["line"]}" stroke-width="2"/>'
body += f'<line x1="640" x2="640" y1="48" y2="262" stroke="{T["line"]}" stroke-width="2"/>'


def stat(x, y, label, value, sub):
    return (text(x, y, label, 10, T["muted"], MONO, spacing=0.8) + text(x, y + 38, value, 36, T["ink"], SERIF)
            + text(x, y + 60, sub, 12, T["muted"]))


best_sub = best_day.strftime("%b %d, %Y").replace(" 0", " ") if best_day else "-"
body += (stat(668, 78, "BUSIEST DAY", best["count"], best_sub) + stat(786, 78, "ACTIVE DAYS", active, "this year")
         + stat(668, 170, "LONGEST STREAK", longest, "day" + ("" if longest == 1 else "s"))
         + stat(786, 170, "CURRENT STREAK", current, "day" + ("" if current == 1 else "s")))
save("activity.svg", svg(900, 290, "Monthly GitHub activity", body))

# ---- languages card ------------------------------------------------------------
LANGS = [("Spanish", "Native"), ("English", "B2"), ("Portuguese", "A1")]
body = (f'<text x="40" y="52" font-family="{SERIF}" font-size="27" fill="{T["ink"]}">Languages, '
        f'<tspan font-style="italic" fill="{T["accent"]}">spoken</tspan></text>')
for k, (name, level) in enumerate(LANGS):
    x = 40 + k * 280
    body += (f'<rect x="{x}" y="84" width="10" height="10" rx="2.5" fill="{T["accent"]}"/>'
             + text(x + 20, 94, name.upper(), 12, T["muted"], MONO, spacing=2)
             + text(x, 140, level, 40, T["ink"], SERIF))
save("languages.svg", svg(900, 170, "Languages: Spanish native, English B2, Portuguese A1", body))

print(f"Done. theme={os.environ.get('THEME', 'light')} data_ok={OK} total={total} active={active} "
      f"longest={longest} current={current}")

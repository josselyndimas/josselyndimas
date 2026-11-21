#!/usr/bin/env python3
"""Render SVG GitHub profile cards using public GitHub contribution calendar, no fake counts."""
import os, json, re, html, urllib.request
from html.parser import HTMLParser
from pathlib import Path
from datetime import date, datetime, timedelta
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[1]
CARDS=ROOT/'cards'; CARDS.mkdir(exist_ok=True)
DATA=ROOT/'data'; DATA.mkdir(exist_ok=True)
USER='josselyndimas'
STATIC=os.getenv('STATIC')=='1'

class ContributionParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.days={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs); day=a.get('data-date') or a.get('data-day')
        if not day or not re.match(r'^\d{4}-\d\d-\d\d$',day): return
        level=a.get('data-level'); count=a.get('data-count')
        if level is None and count is None: return
        try:
            level=int(level or 0); count=int(count) if count is not None else None
            old=self.days.get(day)
            if old is None or count is not None:self.days[day]={'level':min(4,max(0,level)), 'count':count}
        except ValueError: pass

def collect():
    url=f'https://github.com/users/{USER}/contributions'
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 JosselynProfile/1.0','Accept':'text/html'})
        with urllib.request.urlopen(req,timeout=25) as r: page=r.read().decode('utf-8','replace')
        parser=ContributionParser();parser.feed(page)
        days=parser.days
        if len(days)<100: raise RuntimeError(f'Only {len(days)} calendar cells parsed')
        info={'fetched_at':datetime.now().isoformat(timespec='seconds')+'Z','source':url,'days':days}
        (DATA/'contributions.json').write_text(json.dumps(info,indent=2),encoding='utf8')
        return days, True
    except Exception as e:
        cached=DATA/'contributions.json'
        if cached.exists():
            print('Using previously fetched data:',e)
            return json.loads(cached.read_text(encoding='utf8'))['days'],True
        print('Activity not available yet, using empty non-numeric placeholder:',e)
        return {},False

DAYS,AVAILABLE=collect()
BG='#0d1117'; PANEL='#111923'; LINE='#263341'; WHITE='#e8f0ec'; MUTED='#95aaa6'; GREEN='#56e69b'; TEAL='#29b87d'; GOLD='#e1b48c'
SHADES=['#192720','#1b5037','#267c50','#37b874','#69f5a8']
def esc(s):return html.escape(str(s),quote=True)
def styles():
    return '''<style>
    text{font-family:Arial,Helvetica,sans-serif} .muted{fill:#95aaa6} .bright{fill:#e8f0ec}
    .enter{animation:appear .8s ease both} .spark{animation:spark 2s ease-in-out infinite}
    .sq{animation:appear .35s ease both} .bar{transform-box:fill-box;transform-origin:50% 100%;animation:grow 1s cubic-bezier(.2,.8,.2,1) both}
    @keyframes appear{from{opacity:0}to{opacity:1}} @keyframes grow{from{transform:scaleY(.03)}to{transform:scaleY(1)}}
    @keyframes spark{50%{opacity:.3}} @media(prefers-reduced-motion:reduce){.sq,.bar,.enter,.spark{animation:none!important}}
    </style>'''
def shell(w,h,title,subtitle=''):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(title)}"><rect width="{w}" height="{h}" rx="20" fill="{PANEL}"/><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="19" stroke="{LINE}" stroke-width="2" fill="none"/>{styles()}<circle cx="27" cy="24" r="5" fill="#fa7474"/><circle cx="44" cy="24" r="5" fill="#e3b561"/><circle cx="61" cy="24" r="5" fill="{GREEN}"/><text x="82" y="29" font-size="13" fill="{MUTED}">josselyn@github ~/ {esc(subtitle)}</text>'''
def save(name,txt): (CARDS/name).write_text(txt+'</svg>',encoding='utf8')

# Header greeting: separate GIF remains the hero portrait (SVG cannot reliably embed an external local GIF)
s=shell(900,180,'Josselyn Dimas - software developer','welcome')
s+='''<text x="36" y="93" fill="#e8f0ec" font-size="42" font-weight="bold" class="enter">Hello, I'm <tspan fill="#56e69b">Josselyn</tspan><tspan fill="#e1b48c"> ✦</tspan></text>
<text x="38" y="132" fill="#a2b6ad" font-size="19" class="enter">Software development · building ideas into real projects</text>
<circle cx="857" cy="106" r="12" fill="#56e69b" opacity=".12"/><circle cx="857" cy="106" r="4" fill="#56e69b" class="spark"/>'''
save('hero.svg',s)

# Heatmap with exact calendar levels from GitHub; unknown cells are left blank and explicitly labelled.
today=date.today(); start=today-timedelta(days=364); start-=timedelta(days=(start.weekday()+1)%7)
weeks=53;cell=11;gap=3;left=47;top=84
s=shell(900,235,'Actual GitHub contributions calendar','contributions')
s+=f'<text x="35" y="59" fill="{WHITE}" font-size="21" font-weight="bold">Contribution activity</text>'
for w in range(weeks):
  for d in range(7):
    dt=start+timedelta(days=w*7+d)
    if dt>today:continue
    info=DAYS.get(dt.isoformat())
    lv=info['level'] if info else 0
    color=SHADES[lv] if AVAILABLE else '#1b2730'
    delay=f'{min(3.8,.35+w*.04):.2f}'
    s+=f'<rect class="sq" style="animation-delay:{delay}s" x="{left+w*(cell+gap)}" y="{top+d*(cell+gap)}" width="{cell}" height="{cell}" rx="2.1" fill="{color}"><title>{dt.isoformat()}: {("" if info is None else str(info.get("count") or "level "+str(lv))) if AVAILABLE else "Data pending"}</title></rect>'
s+=f'<text x="35" y="211" fill="{MUTED}" font-size="12">'+('Live public GitHub activity · low → high' if AVAILABLE else 'Calendar layout ready · real activity will appear after first workflow run')+'</text>'
save('heatmap.svg',s)

# Last 12 months: proportions based on levels (not counts) unless actual counts are present.
months=[];y=today.year;m=today.month
for _ in range(12):
 months.append((y,m));m-=1
 if m<1:m=12;y-=1
months.reverse(); sums=defaultdict(int)
for dt,val in DAYS.items():
 try: yy,mm,_=map(int,dt.split('-'))
 except:continue
 sums[(yy,mm)]+=val['count'] if val.get('count') is not None else val['level']
maxv=max([sums[x] for x in months]+[1]);has_counts=AVAILABLE and all(v.get('count') is not None for v in DAYS.values())
s=shell(900,300,'Activity by month based on GitHub contributions','monthly_activity')
s+=f'<text x="35" y="61" font-size="22" fill="{WHITE}" font-weight="bold">Monthly activity</text>'
s+=f'<text x="35" y="82" font-size="13" fill="{MUTED}">'+('Contributions per month' if has_counts else 'Relative activity (GitHub intensity levels)' if AVAILABLE else 'Waiting for verified contribution data')+'</text>'
for i,month in enumerate(months):
 value=sums[month]; h=round(130*value/maxv) if AVAILABLE else 0; x=52+i*67
 if h:
  s+=f'<rect x="{x}" y="{240-h}" width="34" height="{h}" rx="5" fill="{GREEN if value==maxv else TEAL}" class="bar" style="animation-delay:{i*.08:.2f}s"/>'
 s+=f'<text x="{x+17}" y="263" text-anchor="middle" fill="{MUTED}" font-size="12">{date(month[0],month[1],1).strftime("%b")}</text>'
s+=f'<line x1="42" x2="852" y1="240" y2="240" stroke="{LINE}"/>'
save('activity.svg',s)

# Three visual feature tiles; links supplied in README.
def tile(filename,key,title,desc,accent,sub):
 s=shell(288,202,title,key.lower())
 s+=f'<text x="23" y="85" fill="{accent}" font-size="13" font-weight="bold">{esc(sub)}</text>'
 s+=f'<text x="22" y="130" fill="{WHITE}" font-size="30" font-weight="bold" class="enter">{esc(title)}</text>'
 s+=f'<text x="22" y="160" fill="{MUTED}" font-size="13">{esc(desc)}</text>'
 s+=f'<text x="253" y="160" fill="{accent}" font-size="23">↗</text>'
 save(filename,s)
tile('build.svg','01','BUILD','Projects and experiments',GREEN,'01 / MAKE IT REAL')
tile('learn.svg','02','LEARN','Always curious, always growing',GOLD,'02 / KEEP EXPLORING')
tile('connect.svg','03','CONNECT','GitHub and open source','#82b7ff','03 / SAY HELLO')
print('Generated cards; available activity data:',AVAILABLE,'days:',len(DAYS))

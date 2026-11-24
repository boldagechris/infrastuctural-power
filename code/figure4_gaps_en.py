"""Figure 4b: the stack with its holes. Companion to Figure 4.

Figure 4 shows the 108 systems where a cloud provider or hosting arrangement was identified. This figure shows
all 364 AI systems in use or planned and where knowledge of each one stops:
  AI systems -> developer (as coded) -> how the cloud information became known -> cloud provider.
Unit: AI systems. A system with several cloud providers is split equally between them, so flows add up to 364.
Grey = not known.
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import read_sheet
import re
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle

a = read_sheet(None, 'active')


def s(v):
    if pd.isna(v): return None
    v = str(v).strip()
    return v or None


GREY, GREY_TXT = '#d9d4d4', '#7a7272'
BIG3 = {'Microsoft': 'Microsoft', 'Microsoft Azure': 'Microsoft', 'Microzoft': 'Microsoft', 'Amazon': 'Amazon',
        'Amazon Web Services': 'Amazon', 'Google': 'Google', 'Google Cloud': 'Google', 'Google Platform': 'Google'}
SELF = 'On-premises / self-hosted / public IT'
OTHER = 'Other cloud or AI provider'
NONE_C = 'No cloud provider identified'


def cloud_groups(g):
    out = set()
    for col in ['CSP IaaS', 'CSP PaaS', 'CSP SaaS']:
        for c in g[col].dropna().astype(str):
            for x in re.split(r',\s*', c):
                x = re.sub(r'\s*\(.*?\)\s*', '', x).strip()
                if x: out.add(BIG3.get(x, OTHER))
    for h in g['CSP'].dropna().astype(str):
        if h.strip(): out.add(SELF)
    return out


DEV = ['Public developer, internal', 'Public developer, external', 'Private developer', 'Developer unknown']
SRC = ['Contact with public authority', 'Contact with vendor', 'Public documents (web search)',
       'Found, source not recorded', 'Not identified (not asked, no answer or not known: not recorded)']
CLOUD = ['Microsoft', 'Amazon', 'Google', OTHER, SELF, NONE_C]
rows = []
for sy, g in a.groupby('AI project'):
    pp = set(g['Public/private'].dropna().astype(str).str.strip())
    internal = (g['Internal/external/unknown'].astype(str).str.strip() == 'Internal').any()
    dev = ('Private developer' if 'Private' in pp else
           ('Public developer, internal' if internal else 'Public developer, external') if 'Public' in pp else 'Developer unknown')
    found = (g['Hosting or CSP found'].astype(str).str.strip().str.lower() == 'yes').any()
    if found:
        gy = g[g['Hosting or CSP found'].astype(str).str.strip().str.lower() == 'yes']
        srcs = set(gy['CSP source'].dropna().astype(str).str.strip())
        src = ('Contact with public authority' if 'Contact with public authority' in srcs else
               'Contact with vendor' if 'Contact with vendor' in srcs else
               'Public documents (web search)' if 'Web search' in srcs else 'Found, source not recorded')
        clouds = cloud_groups(gy) or {OTHER}
    else:
        src, clouds = SRC[-1], {NONE_C}
    for c in clouds:
        rows.append((sy, dev, src, c, 1 / len(clouds)))
R = pd.DataFrame(rows, columns=['System', 'Developer', 'Source', 'Cloud', 'Share'])
R.to_csv('figure4b_gaps_systems.csv', index=False)
N = R['System'].nunique()

ALL = f'AI systems in use or planned'
COLS = [[ALL], DEV, SRC, CLOUD]
F = [defaultdict(float) for _ in range(3)]
for r in R.itertuples():
    F[0][(ALL, r.Developer)] += r.Share
    F[1][(r.Developer, r.Source)] += r.Share
    F[2][(r.Source, r.Cloud)] += r.Share
SZ = []
for c in range(4):
    d = defaultdict(float)
    if c < 3:
        for (x, y), w in F[c].items(): d[x] += w
    if c > 0:
        e = defaultdict(float)
        for (x, y), w in F[c - 1].items(): e[y] += w
        d = {n: max(d.get(n, 0), e.get(n, 0)) for n in set(d) | set(e)}
    SZ.append(d)
COLS = [[n for n in col if SZ[c].get(n, 0) > 0] for c, col in enumerate(COLS)]
NSYS = R.groupby('Cloud')['System'].nunique().to_dict()     # systems that use each provider (labels)
unknown = lambda n: n in ('Developer unknown', SRC[-1], NONE_C, 'Found, source not recorded')

DCOL = {'Public developer, internal': '#86aac3', 'Public developer, external': '#4d7896', 'Private developer': '#5f2529',
        'Developer unknown': GREY}
SCOL = {'Contact with public authority': '#4d7896', 'Contact with vendor': '#a3585c', 'Public documents (web search)': '#e3b5b7',
        'Found, source not recorded': '#bdb5b5', SRC[-1]: GREY}
CCOL = {'Microsoft': '#4d7896', 'Amazon': '#4d7896', 'Google': '#4d7896', OTHER: '#86aac3', SELF: '#bad1e0', NONE_C: GREY}


def ncol(c, n):
    return '#a89c9c' if c == 0 else (DCOL if c == 1 else SCOL if c == 2 else CCOL)[n]


X = [0.0, 0.25, 0.52, 0.80]
W, GAP, H = 0.014, 0.025, 1.0
scale = min((H - GAP * (len(COLS[c]) - 1)) / N for c in range(4))
top = []
for c in range(4):
    span = N * scale + GAP * (len(COLS[c]) - 1)
    y, t = (H + span) / 2, {}
    for n in COLS[c]:
        t[n] = y; y -= SZ[c][n] * scale + GAP
    top.append(t)


def ribbon(ax, x0, y0, x1, y1, h, color, alpha):
    xm = (x0 + x1) / 2
    v = [(x0, y0), (xm, y0), (xm, y1), (x1, y1), (x1, y1 - h), (xm, y1 - h), (xm, y0 - h), (x0, y0 - h), (x0, y0)]
    cd = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(v, cd), facecolor=color, alpha=alpha, lw=0))


plt.rcParams.update({'font.family': 'DejaVu Sans'})
fig, ax = plt.subplots(figsize=(16, 9.5))
out, inn = [dict(t) for t in top], [dict(t) for t in top]
for st in range(3):
    ps, pt = {n: i for i, n in enumerate(COLS[st])}, {n: i for i, n in enumerate(COLS[st + 1])}
    ty = {}
    for k, w in sorted(F[st].items(), key=lambda kv: (pt[kv[0][1]], ps[kv[0][0]])):
        ty[k] = inn[st + 1][k[1]]; inn[st + 1][k[1]] -= w * scale
    for k, w in sorted(F[st].items(), key=lambda kv: (ps[kv[0][0]], pt[kv[0][1]])):
        h = w * scale; y0 = out[st][k[0]]; out[st][k[0]] -= h
        gap = unknown(k[1]) or unknown(k[0])
        col = GREY if gap else ncol(st + 1, k[1])
        ribbon(ax, X[st] + W, y0, X[st + 1], ty[k], h, col, 0.75 if gap else 0.5)


def fmt(x):
    return f'{x:.0f}' if abs(x - round(x)) < 0.05 else f'{x:.1f}'


for c in range(4):
    for n in COLS[c]:
        h = SZ[c][n] * scale; ym = top[c][n] - h / 2
        ax.add_patch(Rectangle((X[c], top[c][n] - h), W, h, color=ncol(c, n), lw=0))
        txtcol = GREY_TXT if unknown(n) else '#222'
        lab = f'{n}  ({NSYS[n]})' if c == 3 else f'{n}  ({fmt(SZ[c][n])})'
        if c == 0:
            ax.text(X[c] - 0.008, ym, f'{N}\n{n}'.replace(' in use', '\nin use'), ha='right', va='center', fontsize=10.5, color='#222')
        else:
            if n == SRC[-1]: lab = f'Not identified  ({fmt(SZ[c][n])})\nnot asked, no answer or not known:\nthe data do not say which'
            big = c == 3 and n in ('Microsoft', 'Amazon', 'Google')
            ax.text(X[c] + W + 0.006, ym, lab, ha='left', va='center', fontsize=10.5 if big else 9.5,
                    fontweight='bold' if big else 'normal', color=txtcol, style='italic' if unknown(n) else 'normal',
                    path_effects=[pe.withStroke(linewidth=3, foreground='white')], zorder=5)
HEAD = ['AI systems', 'Developer', 'How the cloud became known', 'Cloud service provider']
for c, h1 in enumerate(HEAD):
    ax.text(X[c] + W / 2, 1.03, h1, ha='center', va='bottom', fontsize=12, fontweight='bold', color='#222')
ax.set_xlim(-0.16, 1.08); ax.set_ylim(-0.03, 1.07); ax.axis('off')
ax.set_title('Figure 4b. The stack with its holes: where knowledge of each AI system stops', loc='left', fontweight='bold', fontsize=14)
fig.text(0.01, 0.008, f'All {N} AI systems in use or planned. Unit: AI systems. In the flows, a system with several cloud providers is split equally between them; '
         'cloud labels give the number of systems using each provider.\n'
         'Where several sources are recorded, contact with the authority is counted first. Grey = not known. '
         'Figure 4 shows only the coloured part. Developer as coded in the dataset.',
         fontsize=9, color='#555')
fig.tight_layout(rect=(0, 0.035, 1, 1))
fig.savefig('figure4b_gaps_en.png', dpi=200)
fig.savefig('figure4b_gaps_en.svg')
for c in range(1, 4):
    print({n: round(SZ[c][n], 1) for n in COLS[c]})

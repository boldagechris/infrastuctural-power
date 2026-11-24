"""Figure 4 on the 364 AI systems in use or planned: AI system -> vendor -> public authority -> cloud provider.
Built from the AI project sheet (one row = one system at one authority), restricted to privately developed
systems (Public/private = Private) where 'Hosting or CSP found' = yes. Cloud providers come from the columns
CSP IaaS / PaaS / SaaS (one per comma) and the column CSP (vendor-hosted, on-premises, other hosting).
Unit and flows as in figure4b_sankey_en.py: one deployment = one authority using one system, split equally over
that deployment's own vendor x cloud links, so flows are conserved.

Usage: python figure4_364_sankey_en.py aktive_364.xlsx [sheet]
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import read_sheet, DATASETS_ACTIVE
import re, sys
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle, Patch
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from names_en import split_vendors, short_en, en

a = read_sheet(None, 'active')


def s(v):
    if pd.isna(v): return None
    v = str(v).strip()
    return v or None


INHOUSE = 'In-house (the authority itself)'
VFIX = {'NTT DATA Business Solutions': 'NTT Data Business Solutions', 'Indsigt.ai': 'indsigt.ai',
        'indsigt.ai / Potentielt KOMPAS': 'indsigt.ai', 'syv.ai (open source)': 'syv.ai',
        'Epic Systems Corporation (US)': 'Epic Systems Corporation', 'Deloitte Statsautoriseret Revisionspartnerselskab': 'Deloitte'}
CFIX = {'OVH Cloud': 'OVHCloud', 'Google Platform': 'Google', 'Microzoft': 'Microsoft', 'Interxion Deutschland GmbH': 'Interxion',
        'team.blue Denmark': 'team.blue', 'Microsoft Azure': 'Microsoft', 'Amazon Web Services': 'Amazon', 'Google Cloud': 'Google'}
AFIX = {'Mors Kommune': 'Morsø Kommune', 'Århus Kommune': 'Aarhus Kommune', 'Oddsherred Kommune': 'Odsherred Kommune',
        'Nordfyn Kommune': 'Nordfyns Kommune', 'Høje Taastrup Kommune': 'Høje-Taastrup Kommune'}


def vendors(cell):
    out = []
    for v in split_vendors(cell or ''):
        v = re.sub(r'\s*\b(ApS|A/S|PTE\. LTD\.|Ltd\.?)\s*$', '', VFIX.get(v, v)).strip()
        if v and v.lower() != 'unknown': out.append(v)
    return out


def csps(r):
    out = []
    for layer, col in [('IaaS', 'CSP IaaS'), ('PaaS', 'CSP PaaS'), ('SaaS', 'CSP SaaS')]:
        for c in re.split(r',\s*', s(r[col]) or ''):
            c = re.sub(r'\s*\(.*?\)\s*', '', c).strip(); c = CFIX.get(c, c)
            if c: out.append((c, layer))
    h = s(r['CSP'])
    if h:
        hl = h.lower()
        h = ('Vendor-hosted (no external CSP)' if hl.startswith('vendor hosted') else
             'On-premises' if hl.startswith('on-prem') else re.sub(r'\s*\(.*?\)\s*', '', h).strip())
        out.append((h, 'Not specified'))
    return out


DTYPES = ['Private developer (external)', 'Public developer, external', 'Public developer, internal']
DCOL = {'Private developer (external)': '#5f2529', 'Public developer, external': '#4d7896', 'Public developer, internal': '#86aac3'}
DTXT = {'Private developer (external)': '#5f2529', 'Public developer, external': '#2f4f66', 'Public developer, internal': '#2f4f66'}
DEVTYPE = {}
rows = []
for _, r in a.iterrows():
    pp = s(r['Public/private'])
    if pp not in ('Private', 'Public') or str(r['Hosting or CSP found']).strip().lower() != 'yes': continue
    auth = s(r['Offentlig myndighed']); system = s(r['AI project'])
    if not auth or not system: continue
    auth = AFIX.get(auth, auth)
    internal = pp == 'Public' and s(r['Internal/external/unknown']) == 'Internal'
    devs = [INHOUSE] if internal else (vendors(s(r['Vendor'])) or ['Unknown developer'])
    for v in devs:
        DEVTYPE[v] = ('Public developer, internal' if internal else
                      'Private developer (external)' if pp == 'Private' else 'Public developer, external')
    for v in devs:
        for c, l in csps(r):
            if c == 'Vendor-hosted (no external CSP)' and v in ('Microsoft', 'Amazon', 'Google'):
                c = v                                     # a Big Three vendor hosting its own system = dependency on that provider
            rows.append((auth, system, v, c, l))
ROWS = pd.DataFrame(rows, columns=['Authority', 'System', 'Vendor', 'CSP', 'Layer']).drop_duplicates()
ROWS.to_csv('figure4_364_all_rows.csv', index=False)


def auth_type(n):
    if re.search(r'Kommune$', n): return 'Municipality'
    if re.search(r'Region|hospital|Hospital|Sygehus|Rigshospitalet', n, re.I): return 'Region / hospital'
    if re.search(r'Universitet|Statens Serum', n): return 'University / research'
    return 'State agency'


# ---------------- flows (as figure4b_sankey_en.py)
F = [defaultdict(float), defaultdict(float), defaultdict(float)]
for (au, sy), g in ROWS.groupby(['Authority', 'System']):
    share = 1 / len(g)
    for r in g.itertuples():
        F[0][(sy, r.Vendor)] += share
        F[1][(r.Vendor, au)] += share
        F[2][(au, r.CSP, r.Layer)] += share
SYS_PER_CSP = ROWS.groupby('CSP')['System'].nunique()
nA = ROWS.groupby('System')['Authority'].nunique().to_dict()
LAYERS = ['IaaS', 'PaaS', 'SaaS', 'AIaaS', 'Not specified']
LCOL = {'IaaS': '#5f2529', 'PaaS': '#86aac3', 'SaaS': '#e3b5b7', 'AIaaS': '#4d7896', 'Not specified': '#c9c3c3'}
ACOL = {'Municipality': '#bad1e0', 'Region / hospital': '#4d7896', 'State agency': '#e3b5b7', 'University / research': '#a3585c'}
ATXT = {'Municipality': '#2f4f66', 'Region / hospital': '#3b5f78', 'State agency': '#9c5a5e', 'University / research': '#7d3a3e'}
BIG3 = ['Microsoft', 'Amazon', 'Google']
VCOL, SCOL, INCOL = '#5f2529', '#a89c9c', '#4d7896'


def node_size(col):
    inn, out = defaultdict(float), defaultdict(float)
    if col > 0:
        for k, w in F[col - 1].items(): inn[k[1]] += w
    if col < 3:
        for k, w in F[col].items(): out[k[0]] += w
    return {n: max(inn[n], out[n]) for n in set(inn) | set(out)}


SZ = [node_size(c) for c in range(4)]
bround = lambda x: int(round(x)) if abs(x - int(x) - 0.5) > 1e-9 else (int(x) if int(x) % 2 == 0 else int(x) + 1)
csp_order = sorted(SZ[3], key=lambda c: (-SZ[3][c], c))          # largest first, by flow size
cpos = {c: i for i, c in enumerate(csp_order)}
ab = defaultdict(list)
for (au, c, l), w in F[2].items(): ab[au] += [cpos[c]] * max(1, bround(w * 2))
auth_order = sorted(SZ[2], key=lambda x: (sum(ab[x]) / len(ab[x]), x))
apos = {x: i for i, x in enumerate(auth_order)}
vb = defaultdict(list)
for (v, au), w in F[1].items(): vb[v] += [apos[au]] * max(1, bround(w * 2))
vend_order = sorted(SZ[1], key=lambda v: (v == INHOUSE, sum(vb[v]) / len(vb[v]), v.lower()))
vpos = {v: i for i, v in enumerate(vend_order)}
sb = defaultdict(list)
for (sy, v), w in F[0].items(): sb[sy].append(vpos[v])
sys_order = sorted(SZ[0], key=lambda x: (min(sb[x]), x.lower()))
ORDER = [sys_order, vend_order, auth_order, csp_order]

# ---------------- geometry
X = [0.0, 0.30, 0.58, 0.88]
W = 0.012
GAP = [0.004, 0.006, 0.003, 0.010]
H = 1.0
scale = min((H - GAP[c] * (len(ORDER[c]) - 1)) / sum(SZ[c].values()) for c in range(4))
top = []
for c in range(4):
    span = sum(SZ[c].values()) * scale + GAP[c] * (len(ORDER[c]) - 1)
    y, t = (H + span) / 2, {}
    for n in ORDER[c]:
        t[n] = y; y -= SZ[c][n] * scale + GAP[c]
    top.append(t)


def ribbon(ax, x0, y0, x1, y1, h, color, alpha):
    xm = (x0 + x1) / 2
    verts = [(x0, y0), (xm, y0), (xm, y1), (x1, y1), (x1, y1 - h), (xm, y1 - h), (xm, y0 - h), (x0, y0 - h), (x0, y0)]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), facecolor=color, alpha=alpha, lw=0))


plt.rcParams.update({'font.family': 'DejaVu Sans'})
FH = max(19, 0.3 * max(len(o) for o in ORDER))
fig, ax = plt.subplots(figsize=(17, FH))
outoff, inoff = [dict(t) for t in top], [dict(t) for t in top]
for st in range(3):
    ps, pt = {n: i for i, n in enumerate(ORDER[st])}, {n: i for i, n in enumerate(ORDER[st + 1])}
    lay = (lambda k: LAYERS.index(k[2])) if st == 2 else (lambda k: 0)
    ty = {}
    for k, w in sorted(F[st].items(), key=lambda kv: (pt[kv[0][1]], ps[kv[0][0]], lay(kv[0]))):
        ty[k] = inoff[st + 1][k[1]]; inoff[st + 1][k[1]] -= w * scale
    for k, w in sorted(F[st].items(), key=lambda kv: (ps[kv[0][0]], pt[kv[0][1]], lay(kv[0]))):
        h = w * scale
        y0 = outoff[st][k[0]]; outoff[st][k[0]] -= h
        col, al = (DCOL[DEVTYPE[k[1]]], 0.4) if st == 0 else \
                  ((ACOL[auth_type(k[1])], 0.6) if st == 1 else (LCOL[k[2]], 0.6))
        ribbon(ax, X[st] + W, y0, X[st + 1], ty[k], h, col, al)
halo = [pe.withStroke(linewidth=2.5, foreground='white')]
for c in range(4):
    for n in ORDER[c]:
        h = SZ[c][n] * scale; ym = top[c][n] - h / 2
        col = SCOL if c == 0 else (DCOL[DEVTYPE[n]] if c == 1 else (ACOL[auth_type(n)] if c == 2 else ('#4d7896' if n in BIG3 else '#86aac3')))
        ax.add_patch(Rectangle((X[c], top[c][n] - h), W, h, color=col, lw=0))
        if c == 0:
            lab = n if len(n) <= 40 else n[:38] + '…'
            if nA[n] > 1: lab += f'  ({nA[n]})'
            ax.text(X[c] - 0.006, ym, lab, ha='right', va='center', fontsize=7.5, color='#333')
        elif c == 1:
            t = ax.text(X[c] + W + 0.004, ym, n, ha='left', va='center', fontsize=8, fontweight='bold', color=DTXT[DEVTYPE[n]], zorder=5)
            t.set_path_effects(halo)
        elif c == 2:
            t = ax.text(X[c] + W + 0.004, ym, en(n), ha='left', va='center', fontsize=7,
                        color=ATXT[auth_type(n)], zorder=5)
            t.set_path_effects(halo)
        else:
            big = n in BIG3
            ax.text(X[c] + W + 0.006, ym, n, ha='left', va='center',
                    fontsize=11 if big else 8.5, fontweight='bold' if big else 'normal', color='#222')
ndev = len([v for v in vend_order if v != INHOUSE])
HEAD = [('AI systems', '(no. of authorities)'),
        ('Developers', ''),
        ('Public authorities', ''), ('Cloud service providers', '')]
for c, (h1, h2) in enumerate(HEAD):
    ax.text(X[c] + W / 2, 1.026, h1, ha='center', va='bottom', fontsize=12, fontweight='bold', color='#222')
    if h2: ax.text(X[c] + W / 2, 1.008, h2, ha='center', va='bottom', fontsize=9.5, color='#555')
l1 = ax.legend(handles=[Patch(color=ACOL[t], label=t) for t in ACOL if any(auth_type(x) == t for x in auth_order)],
               title='Public authority', frameon=False, loc='lower left', bbox_to_anchor=(-0.02, -0.035),
               fontsize=9.5, title_fontsize=9.5, ncol=2)
ax.add_artist(l1)
l3 = ax.legend(handles=[Patch(color=DCOL[d], label=d) for d in DTYPES if d in set(DEVTYPE[v] for v in vend_order)],
               title='Developer', frameon=False, loc='lower center', bbox_to_anchor=(0.45, -0.035), fontsize=9.5, title_fontsize=9.5, ncol=1)
ax.add_artist(l3)
ax.legend(handles=[Patch(color=LCOL[l], alpha=0.75, label=l) for l in LAYERS if any(k[2] == l for k in F[2])],
          title='Cloud layer', frameon=False, loc='lower right', bbox_to_anchor=(1.02, -0.035), fontsize=9.5, title_fontsize=9.5, ncol=3)
ax.set_xlim(-0.2, 1.1); ax.set_ylim(-0.04, 1.06); ax.axis('off')
ax.set_title('Figure 4. Cloud services built into AI systems deployed by public authorities',
             loc='left', fontweight='bold', fontsize=14)
fig.text(0.01, 0.003, f'AI systems in use or planned with an identified cloud provider or hosting arrangement ({len(sys_order)} of 364). '
         f'One deployment = one authority using one system; {len(ROWS.groupby(["Authority", "System"]))} deployments.\n'
         'Internal = built by the deploying authority itself. Developer type as coded in the dataset (e.g. KMD Letbetaling is coded as public).',
         fontsize=9, color='#555')
fig.tight_layout(rect=(0, 0.014, 1, 1))
fig.savefig('figure4_364_all_sankey_en.png', dpi=200)
fig.savefig('figure4_364_all_sankey_en.svg')
print(len(sys_order), 'systems', len(vend_order), 'vendors', len(auth_order), 'authorities', len(csp_order), 'providers',
      len(ROWS.groupby(['Authority', 'System'])), 'deployments')
print(sorted(csp_order)); print([v for v in vend_order])

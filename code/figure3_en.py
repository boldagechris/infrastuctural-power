"""Figure 3: Private AI vendors and the cloud service providers (CSPs) they build on,
by layer of the cloud stack (IaaS, PaaS, SaaS, AIaaS).

Data: sheet 'Vendor' (CSP, CSM). Vendor-level relations, not tied to individual AI systems.
Scope: vendors that appear as private vendors in Figure 2 (sheet given as 2nd argument,
default 'filter'). All links with a named CSP are kept; missing/'Non specified' layer = 'Not specified'.

Outputs: figure3_network_en.png, figure3_matrix_en.png, figure3_sankey_en.png,
         figure3_links.csv, figure3_network.gexf

Usage:  python figure3_en.py Nyt_datasæt.xlsx [sheet]
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import read_sheet, DATASETS_ACTIVE
import re, sys
from names_en import short_en
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, FancyArrowPatch, PathPatch, Rectangle
from matplotlib.path import Path

F, SHEET = None, 'active'


def norm(s):
    s = re.sub(r'\b(ApS|A/S|AB|AS|Inc\.?|Ltd\.?|PTE\.?|DK|Denmark|DANMARK|Group)\b', '', str(s).strip(), flags=re.I)
    return re.sub(r'[^a-z0-9]', '', s.lower())


# --- Figure 2 vendors (private vendors in the selected sheet)
d = read_sheet(F, SHEET)
d = d[d['Public/private'].astype(str).str.strip() == 'Private']
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from names_en import split_vendors                    # several vendors in one cell = several vendors
fig2 = {}
for v in d['Vendor'].dropna().astype(str).str.strip():
    for x in split_vendors(v):
        x = {'NTT DATA Business Solutions': 'NTT Data Business Solutions'}.get(x.strip(), x.strip())
        fig2[norm(x)] = x
ALIAS = {norm('Teacherspace ApS'): 'EdSpace'}       # company behind the EdSpace product

# --- Vendor -> CSP links
v = read_sheet(F, 'Vendor').dropna(subset=['CSP'])
BIG3 = ['Microsoft', 'Amazon', 'Google']
COMPANY = {'Microsoft Azure': 'Microsoft', 'Amazon Web Services': 'Amazon', 'Google Cloud': 'Google', 'Oracle Cloud': 'Oracle'}
rows = []
for _, r0 in v.iterrows():
  for vv in split_vendors(r0['Vendor']):
    r = r0.copy(); r['Vendor'] = vv
    key = norm(r['Vendor'])
    name = fig2.get(key) or ALIAS.get(key)
    if name is None:
        continue
    layer = str(r['CSM']).strip() if pd.notna(r['CSM']) else 'Not specified'
    layer = {'Non specified': 'Not specified'}.get(layer, layer)
    csp_raw = str(r['CSP']).replace('Anthropic Ireland, Limited', 'Anthropic')
    for c in re.split(r',\s*', csp_raw):
        c = re.sub(r'\s*\(.*?\)\s*', '', c).strip()          # drop '(projekt specifikt)'
        c = {'OCI': 'Oracle Cloud', 'raffle.ai ApS': 'raffle.ai', 'team.blue Denmark A/S': 'team.blue',
             'Anthropic Ireland, Limited': 'Anthropic', 'Cleura AB': 'Cleura', 'Cantab Research Ltd.': 'Speechmatics', 'Microzoft Azure': 'Microsoft Azure', 'Google': 'Google Cloud', 'UpCloud Ltd.': 'UpCloud', 'team.blue Denmark': 'team.blue',
             'Microsoft': 'Microsoft Azure', 'Amazon': 'Amazon Web Services', 'Google Platform': 'Google Cloud', 'Syv.ai': 'syv.ai'}.get(c, c)
        c = COMPANY.get(c, c)                                 # providers are shown by company name
        if c and norm(c) == norm(name) and c not in BIG3: c = 'Vendor-hosted (no external CSP)'   # vendor runs it on its own infrastructure
        # skip text that is not a provider name (e.g. chat messages pasted into the CSP cell)
        if c and len(c.split()) <= 5 and not re.search(r'[!?]|:\)', c):
            rows.append((name, c, layer))
        elif c:
            print('SKIPPED invalid CSP value for', name, ':', c[:60])
L = pd.DataFrame(rows, columns=['Vendor', 'CSP', 'Layer']).drop_duplicates()
L.to_csv('figure3_links.csv', index=False)

LAYERS = ['IaaS', 'PaaS', 'SaaS', 'AIaaS', 'Not specified']
LCOL = {'IaaS': '#5f2529', 'PaaS': '#86aac3', 'SaaS': '#e3b5b7', 'AIaaS': '#4d7896', 'Not specified': '#c9c3c3'}
VCOL, CCOL_BIG, CCOL = '#5f2529', '#4d7896', '#bad1e0'

n_csp = L.groupby('Vendor')['CSP'].nunique()
csp_vendors = L.groupby('CSP')['Vendor'].nunique().sort_values(ascending=False)
vendors = n_csp.sort_values(kind='stable').index.tolist()
vendors = sorted(vendors, key=lambda x: (n_csp[x], x.lower()))
csps = csp_vendors.index.tolist()
layers_present = [l for l in LAYERS if l in set(L['Layer'])]
legend_layers = [Line2D([], [], color=LCOL[l], lw=3, label=l) for l in layers_present]
plt.rcParams.update({'font.family': 'DejaVu Sans'})
TITLE = 'Figure 3. Private AI vendors and the cloud service providers they build on'
halo = [pe.withStroke(linewidth=2.2, foreground='white')]

# =====================================================================================
# 1. NETWORK
# =====================================================================================
G = nx.Graph()
for x in vendors: G.add_node(x, kind='vendor')
for c in csps:
    if c in G and c in BIG3:                          # e.g. Microsoft: vendor (Copilot) and Big Three provider
        G.nodes[c]['kind'] = 'csp'; G.nodes[c]['also_vendor'] = True
    elif c in G: G.nodes[c]['also_provider'] = True   # e.g. raffle.ai: vendor that also supplies other vendors
    else: G.add_node(c, kind='csp')
for (a, b), g in L.groupby(['Vendor', 'CSP']):
    if a != b: G.add_edge(a, b, layers=sorted(set(g['Layer']), key=LAYERS.index))   # own cloud: no self-loop
deg = dict(G.degree())
comps = sorted(nx.connected_components(G), key=len, reverse=True)
main = G.subgraph(comps[0])
anchor = {'Microsoft': (-0.75, 0.15), 'Amazon': (0.75, 0.15), 'Google': (0.0, -0.75)}
fixed = [c for c in anchor if c in main]
pos = nx.spring_layout(main, pos={c: anchor[c] for c in fixed}, fixed=fixed,
                       k=0.55, iterations=800, seed=4)
# push apart overlapping nodes
nodes = list(pos)
for _ in range(300):
    moved = False
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            (xa, ya), (xb, yb) = pos[a], pos[b]
            dx, dy = xb - xa, yb - ya
            dist = (dx * dx + dy * dy) ** 0.5 or 1e-6
            need = 0.16
            if dist < need:
                push = (need - dist) / 2; ux, uy = dx / dist, dy / dist
                if a not in fixed: pos[a] = (xa - ux * push, ya - uy * push)
                if b not in fixed: pos[b] = (xb + ux * push, yb + uy * push)
                moved = True
    if not moved: break
xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
yb = min(ys) - 0.3
for i, c in enumerate(comps[1:]):
    cx = min(xs) + (i + 0.5) * (max(xs) - min(xs)) / max(1, len(comps) - 1)
    for j, n in enumerate(sorted(c, key=lambda n: G.nodes[n]['kind'], reverse=True)):
        pos[n] = (cx + (j - (len(c) - 1) / 2) * 0.55, yb)
STRIP = {n for c in comps[1:] for n in c}

fig, ax = plt.subplots(figsize=(15, 12))
for a, b in G.edges():
    ls = G[a][b]['layers']
    k = len(ls)
    for i, l in enumerate(ls):
        rad = 0 if k == 1 else (-0.18 + 0.36 * i / (k - 1))
        ax.add_patch(FancyArrowPatch(pos[a], pos[b], connectionstyle=f'arc3,rad={rad}', arrowstyle='-',
                                     color=LCOL[l], lw=1.6, alpha=0.75, zorder=1))
vn = [n for n in G if G.nodes[n]['kind'] == 'vendor']
cn = [n for n in G if G.nodes[n]['kind'] == 'csp']
nx.draw_networkx_nodes(G, pos, nodelist=vn, node_shape='s', node_color=VCOL, ax=ax,
                       node_size=[60 + 25 * deg[n] for n in vn], edgecolors='white', linewidths=0.6)
nx.draw_networkx_nodes(G, pos, nodelist=cn, node_shape='o', ax=ax,
                       node_color=[CCOL_BIG if n in BIG3 else CCOL for n in cn],
                       node_size=[80 + 45 * deg[n] for n in cn], edgecolors='white', linewidths=0.8)
leg = [Line2D([], [], marker='s', ls='', ms=10, color=VCOL, label='Private AI vendor'),
       Line2D([], [], marker='o', ls='', ms=11, color=CCOL_BIG, label='Big Three cloud provider'),
       Line2D([], [], marker='o', ls='', ms=10, color=CCOL, label='Other cloud / AI provider')]
l1 = ax.legend(handles=leg, frameon=False, loc='upper left', fontsize=10)
ax.add_artist(l1)
ax.set_title(TITLE, loc='left', fontweight='bold', fontsize=14)
l2 = ax.legend(handles=legend_layers, title='Cloud layer', frameon=False, loc='upper right', fontsize=10, title_fontsize=10)
ax.axis('off')
fig.tight_layout()
from labels_above import place_labels_above
def rnode(n): return ((80 + 45 * deg[n]) if G.nodes[n]['kind'] == 'csp' else (60 + 25 * deg[n])) ** 0.5 / 2
items = []
for n in G:
    big = n in BIG3; csp = G.nodes[n]['kind'] == 'csp'
    items.append(dict(x=pos[n][0], y=pos[n][1], text=short_en(n), r=rnode(n), below=n in STRIP, fixed=big,
                      kw=dict(fontsize=12 if big else (9 if csp else 8.5), fontweight='bold' if (big or csp) else 'normal',
                              color='#111' if csp else '#5f2529', zorder=5)))
place_labels_above(fig, ax, items, obstacles_nodes=[(pos[n][0], pos[n][1], rnode(n)) for n in G],
                   obstacle_boxes=[l1, l2], max_shift=14)
fig.savefig('figure3_network_en.png', dpi=200)
plt.close(fig)

# GEXF
H = nx.MultiGraph()
def rgb(h): return {'r': int(h[1:3], 16), 'g': int(h[3:5], 16), 'b': int(h[5:7], 16), 'a': 1.0}
for n in G:
    k = G.nodes[n]['kind']
    cat = ('Private AI vendor (also provider)' if G.nodes[n].get('also_provider') else 'Private AI vendor') if k == 'vendor' else ('Big Three cloud provider' if n in BIG3 else 'Other cloud / AI provider')
    col = VCOL if k == 'vendor' else (CCOL_BIG if n in BIG3 else CCOL)
    H.add_node(n, label=n, node_type=k, category=cat, big_three=n in BIG3, degree=deg[n],
               n_providers=int(n_csp[n]) if k == 'vendor' else 0,
               n_vendors=int(csp_vendors[n]) if n in csp_vendors.index else 0,
               layers='; '.join(sorted(set(L.loc[L.Vendor == n, 'Layer']) | set(L.loc[L.CSP == n, 'Layer']), key=LAYERS.index)),
               viz={'color': rgb(col), 'size': float(6 + (3 if k == 'csp' else 2) * deg[n]),
                    'position': {'x': float(pos[n][0]) * 1000, 'y': float(pos[n][1]) * 1000, 'z': 0.0}})
for _, r in L.iterrows():
    h = LCOL[r.Layer]
    H.add_edge(r.Vendor, r.CSP, layer=r.Layer, weight=1.0, viz={'color': rgb(h)})
nx.write_gexf(H, 'figure3_network.gexf')

# =====================================================================================
# 2. MATRIX  (rows = vendors sorted by number of providers; columns = providers)
# =====================================================================================
fig, ax = plt.subplots(figsize=(1.0 + 0.62 * len(csps) + 3.2, 1.2 + 0.36 * len(vendors)))
cell = {(r.Vendor, r.CSP): [] for r in L.itertuples()}
for r in L.itertuples(): cell[(r.Vendor, r.CSP)].append(r.Layer)
for i, vnd in enumerate(vendors):
    if i % 2 == 0:
        ax.add_patch(Rectangle((-0.5, i - 0.5), len(csps), 1, color='#faf2f2', lw=0, zorder=0))
    for j, c in enumerate(csps):
        ls = sorted(set(cell.get((vnd, c), [])), key=LAYERS.index)
        k = len(ls)
        for q, l in enumerate(ls):
            w = 0.78 / k
            ax.add_patch(Rectangle((j - 0.39 + q * w, i - 0.32), w, 0.64, color=LCOL[l], lw=0.6,
                                   ec='white', zorder=2))
# separators between 1-provider and multi-provider vendors
for k in sorted(set(n_csp))[1:]:
    first = next(i for i, x in enumerate(vendors) if n_csp[x] == k)
    ax.axhline(first - 0.5, color='#999', lw=0.6, ls=(0, (3, 3)))
for i, vnd in enumerate(vendors):
    ax.text(len(csps) - 0.3, i, str(n_csp[vnd]), va='center', ha='left', fontsize=9, color='#555')
ax.text(len(csps) - 0.3, -1.1, 'No. of\nproviders', fontsize=8.5, color='#555', va='bottom')
ax.set_xticks(range(len(csps)))
ax.set_xticklabels([f'{c} ({csp_vendors[c]})' for c in csps], rotation=50, ha='left', fontsize=9.5)
for lab in ax.get_xticklabels():
    if lab.get_text().split(' (')[0] in BIG3: lab.set_fontweight('bold')
ax.xaxis.tick_top()
ax.set_yticks(range(len(vendors))); ax.set_yticklabels(vendors, fontsize=9.5, color='#5f2529')
ax.set_xlim(-0.5, len(csps) + 0.6); ax.set_ylim(len(vendors) - 0.5, -0.5)
for s in ax.spines.values(): s.set_visible(False)
ax.tick_params(length=0)
ax.legend(handles=[Patch(color=LCOL[l], label=l) for l in layers_present], title='Cloud layer',
          frameon=False, loc='upper left', bbox_to_anchor=(1.04, 0.3), fontsize=9.5, title_fontsize=9.5)
fig.suptitle(TITLE, x=0.01, ha='left', fontweight='bold', fontsize=13)
fig.tight_layout()
fig.savefig('figure3_matrix_en.png', dpi=200, bbox_inches='tight')
plt.close(fig)

# =====================================================================================
# 3. SANKEY  (vendors -> providers, one unit per vendor-provider-layer link)
# =====================================================================================
S = L.copy()
vtot = S.groupby('Vendor').size()
ctot = S.groupby('CSP').size()
right = ctot.sort_values(ascending=False).index.tolist()
# order vendors by the mean position of the providers they use (reduces crossings)
rpos = {c: i for i, c in enumerate(right)}
bary = S.assign(r=S['CSP'].map(rpos)).groupby('Vendor')['r'].mean()
left = sorted(vtot.index, key=lambda x: (bary[x], n_csp[x], x.lower()))
total = len(S)
GAP_L, GAP_R = 0.006, 0.012
s = min((1 - GAP_L * (len(left) - 1)) / total, (1 - GAP_R * (len(right) - 1)) / total)


def tops(names, tot, gap):
    h = tot[names] * s
    span = h.sum() + gap * (len(names) - 1)
    y = (1 + span) / 2
    out = {}
    for n in names: out[n] = y; y -= h[n] + gap
    return out, h


yl, hl = tops(left, vtot, GAP_L)
yr, hr = tops(right, ctot, GAP_R)
offl, offr = dict(yl), dict(yr)
fig, ax = plt.subplots(figsize=(13, 15))
XL, XR, W = 0.0, 1.0, 0.018
S['li'] = S['Vendor'].map({n: i for i, n in enumerate(left)})
S['ri'] = S['CSP'].map({n: i for i, n in enumerate(right)})
S['lay'] = S['Layer'].map(LAYERS.index)
# draw: iterate by vendor (left order), then provider, so left bands stack in provider order;
# right bands stack in vendor order -> need consistent ordering on both ends
order = S.sort_values(['ri', 'li', 'lay'])  # right side stacking order
right_off = {}
for r in order.itertuples():
    right_off[(r.Vendor, r.CSP, r.Layer)] = offr[r.CSP]; offr[r.CSP] -= s
for r in S.sort_values(['li', 'ri', 'lay']).itertuples():
    y0 = offl[r.Vendor]; offl[r.Vendor] -= s
    y1 = right_off[(r.Vendor, r.CSP, r.Layer)]
    x0, x1 = XL + W, XR; xm = (x0 + x1) / 2
    verts = [(x0, y0), (xm, y0), (xm, y1), (x1, y1), (x1, y1 - s), (xm, y1 - s), (xm, y0 - s), (x0, y0 - s), (x0, y0)]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO,
             Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), facecolor=LCOL[r.Layer], alpha=0.55, lw=0))
for n in left:
    ax.add_patch(Rectangle((XL, yl[n] - hl[n]), W, hl[n], color=VCOL, lw=0))
    ax.text(XL - 0.01, yl[n] - hl[n] / 2, n, ha='right', va='center', fontsize=8.5, color='#5f2529')
for n in right:
    ax.add_patch(Rectangle((XR, yr[n] - hr[n]), W, hr[n], color=CCOL_BIG if n in BIG3 else CCOL, lw=0))
    ax.text(XR + W + 0.01, yr[n] - hr[n] / 2, f'{n}  ({csp_vendors[n]})', ha='left', va='center',
            fontsize=11 if n in BIG3 else 9, fontweight='bold' if n in BIG3 else 'normal', color='#222')
ax.text(XL + W / 2, 1.015, 'Private AI vendors', ha='center', fontsize=11, color='#333')
ax.text(XR + W / 2, 1.015, 'Cloud service providers\n(no. of vendors)', ha='center', fontsize=11, color='#333')
ax.legend(handles=[Patch(color=LCOL[l], alpha=0.7, label=l) for l in layers_present], title='Cloud layer',
          frameon=False, loc='lower right', bbox_to_anchor=(1.05, 0.0), fontsize=10, title_fontsize=10)
ax.set_xlim(-0.3, 1.38); ax.set_ylim(-0.01, 1.04); ax.axis('off')
ax.set_title(TITLE, loc='left', fontweight='bold', fontsize=13)
fig.tight_layout()
fig.savefig('figure3_sankey_en.png', dpi=200)
plt.close(fig)

# --- summary
print(f'{len(vendors)} vendors, {len(csps)} providers, {len(L)} vendor-provider-layer links')
print('Providers per vendor:', n_csp.value_counts().sort_index().to_dict())
mono = [x for x in vendors if n_csp[x] == 1]
print('Single-provider vendors:', {x: L[L.Vendor == x].CSP.iloc[0] for x in mono})
print('Vendors per provider:', csp_vendors.to_dict())
print('Layer counts:', L['Layer'].value_counts().to_dict())

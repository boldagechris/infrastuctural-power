"""Figure 2: Network of public authorities and private vendors linked by deployed AI systems.

Nodes: public authorities and private vendors. Edges: AI systems a vendor has delivered
to an authority (edge weight = number of distinct AI systems).
Data: sheet 'AI project'; rows with Public/private == 'Private', Deleted rows excluded.

Usage:  python figure2_en.py Nyt_datasæt.xlsx [sheet]
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import read_sheet, DATASETS_ACTIVE
import re, sys
from names_en import short_en
import matplotlib.patheffects as pe
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

d = read_sheet(None, 'active')            # AI systems in use or planned (closed rows removed)
d = d[d['Deleted'] != 1].copy() if 'Deleted' in d.columns else d.copy()
for c in ['Vendor', 'Public/private', 'Offentlig myndighed', 'AI project']:
    d[c] = d[c].astype(str).str.strip().replace('nan', None)
d = d[(d['Public/private'] == 'Private')].dropna(subset=['Vendor', 'Offentlig myndighed'])

# --- Clean vendor names: split joint vendors, harmonise spellings
VENDOR_FIX = {'NTT DATA Business Solutions': 'NTT Data Business Solutions',
              '*Potentielt Promte': 'Promte (potential)'}
from names_en import split_vendors                    # several vendors in one cell = several vendors
SPLIT = sorted({v for v in d['Vendor'] if len(split_vendors(v)) > 1})
if SPLIT: print('Split multi-vendor cells:', SPLIT)
d['Vendor'] = d['Vendor'].map(split_vendors)
d = d.explode('Vendor')
d['Vendor'] = d['Vendor'].str.strip().map(lambda v: VENDOR_FIX.get(v, v))

# --- Clean authority names
AUTH_FIX = {'Politi': 'Politiet', 'Hjørring': 'Hjørring Kommune', 'Mors Kommune': 'Morsø Kommune'}
d['Auth'] = d['Offentlig myndighed'].map(lambda a: AUTH_FIX.get(a, a))


def auth_type(n):
    if re.search(r'Kommune$', n): return 'Municipality'
    if re.search(r'Region|hospital|Hospital|Sygehus|Psykiatri|OUH|CAMES|læger|Medcom|sundhed\.dk', n, re.I):
        return 'Region / hospital'
    if re.search(r'Universitet|DTU|Statens Serum', n): return 'University / research'
    return 'State agency'


edges = (d.groupby(['Auth', 'Vendor'])['AI project'].nunique().reset_index(name='w'))
edges.to_csv('figure2_edges.csv', index=False)

G = nx.Graph()
for a in edges['Auth'].unique(): G.add_node(a, kind='auth', atype=auth_type(a))
for v in edges['Vendor'].unique(): G.add_node(v, kind='vendor')
for _, r in edges.iterrows(): G.add_edge(r.Auth, r.Vendor, weight=r.w)

# --- Node sizes (matplotlib area in pt^2), scaled by number of ties
deg = dict(G.degree())
def area(n):
    return (30 + 22 * deg[n]) if G.nodes[n]['kind'] == 'vendor' else (14 + 9 * deg[n])

FIG_W, FIG_H = 18, 15
PT_PER_UNIT = FIG_W * 72 * 0.92 / 2          # layout is normalised to [-1, 1] on x

def radius(n):                                 # node radius in layout units
    return (area(n) / 3.1416) ** 0.5 / PT_PER_UNIT

# --- Layout: force-directed, then push apart nodes that overlap relative to their size
comps = sorted(nx.connected_components(G), key=len, reverse=True)
main = G.subgraph(comps[0])
pos = nx.kamada_kawai_layout(main)
pos = nx.spring_layout(main, pos=pos, k=1.6 / len(main) ** 0.5, iterations=500, seed=11)
xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
cx, cy, sc = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, (max(xs) - min(xs)) / 2
pos = {n: ((x - cx) / sc, (y - cy) / sc * 0.85) for n, (x, y) in pos.items()}

GAP = 2.6   # minimum distance = GAP * (r1 + r2): larger nodes get more room
nodes = list(pos)
for _ in range(400):
    moved = False
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            (xa, ya), (xb, yb) = pos[a], pos[b]
            dx, dy = xb - xa, yb - ya
            dist = (dx * dx + dy * dy) ** 0.5 or 1e-6
            need = GAP * (radius(a) + radius(b)) + 0.012
            if dist < need:
                push = (need - dist) / 2
                ux, uy = dx / dist, dy / dist
                pos[a] = (xa - ux * push, ya - uy * push)
                pos[b] = (xb + ux * push, yb + uy * push)
                moved = True
    if not moved:
        break

# small components in a strip along the bottom; each keeps its own branching
ys = [p[1] for p in pos.values()]
yb = min(ys) - 0.24
small = comps[1:]
SMALL = {n for c in small for n in c}
widths = [0.42 if len(c) > 2 else 0.2 for c in small]
gap = (1.9 - sum(widths)) / max(1, len(small) - 1)
x = -0.95
for c, w in zip(small, widths):
    sub = G.subgraph(c)
    if len(c) > 2:
        sp = nx.kamada_kawai_layout(sub)
        sx = [p[0] for p in sp.values()]; sy = [p[1] for p in sp.values()]
        cx0, cy0 = (max(sx) + min(sx)) / 2, (max(sy) + min(sy)) / 2
        sc = max(max(sx) - min(sx), (max(sy) - min(sy)) * 1.6) or 1
        for n, (px, py) in sp.items():
            pos[n] = (x + w / 2 + (px - cx0) / sc * w, yb + (py - cy0) / sc * w * 0.62)
    else:
        a, b = sorted(c, key=lambda n: G.nodes[n]['kind'])
        pos[a] = (x + 0.03, yb); pos[b] = (x + w - 0.03, yb)
    x += w + gap

# --- Colours: authority types clearly distinct from each other and from vendors
COL = {'Municipality': '#bad1e0', 'Region / hospital': '#4d7896', 'State agency': '#e3b5b7',
       'University / research': '#a3585c', 'vendor': '#5f2529'}

plt.rcParams.update({'font.family': 'DejaVu Sans'})
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
nx.draw_networkx_edges(G, pos, ax=ax, width=[0.3 + 0.5 * G[u][v]['weight'] for u, v in G.edges()],
                       edge_color='#9a9a9a', alpha=0.28)
auth = [n for n in G if G.nodes[n]['kind'] == 'auth']
vend = [n for n in G if G.nodes[n]['kind'] == 'vendor']
nx.draw_networkx_nodes(G, pos, nodelist=auth, ax=ax, node_shape='o',
                       node_color=[COL[G.nodes[n]['atype']] for n in auth],
                       node_size=[area(n) for n in auth], edgecolors='white', linewidths=0.6)
nx.draw_networkx_nodes(G, pos, nodelist=vend, ax=ax, node_shape='s', node_color=COL['vendor'],
                       node_size=[area(n) for n in vend], edgecolors='white', linewidths=0.6)

# --- Labels (placed after the legend so they keep clear of it): every vendor; authorities with >= AUTH_LABEL_MIN ties
AUTH_LABEL_MIN = 8
handles = [Line2D([], [], marker='s', ls='', ms=10, color=COL['vendor'], label='Private vendor')] + \
          [Line2D([], [], marker='o', ls='', ms=10, color=COL[t], label=t)
           for t in ['Municipality', 'Region / hospital', 'State agency', 'University / research']
           if any(G.nodes[n].get('atype') == t for n in auth)]
ax.set_title('Figure 2. Public authorities and private vendors linked by deployed AI systems',
             loc='left', fontweight='bold', fontsize=14)
leg = ax.legend(handles=handles, frameon=False, loc='upper right', fontsize=11)
ax.axis('off')
fig.tight_layout(rect=(0, 0.03, 1, 1))
from labels_above import place_labels_above
items = []
for n in G:
    k = G.nodes[n]['kind']
    r = (area(n) ** 0.5) / 2                                   # node radius in points
    if k == 'vendor':
        items.append(dict(x=pos[n][0], y=pos[n][1], text=short_en(n), r=r,
                          kw=dict(fontsize=min(6.5 + 0.18 * deg[n], 11), fontweight='bold' if deg[n] >= 5 else 'normal',
                                  color='#5f2529', zorder=5)))
    elif deg[n] >= AUTH_LABEL_MIN or n in SMALL:
        items.append(dict(x=pos[n][0], y=pos[n][1], text=short_en(n), r=r, below=n in SMALL,   # bottom row: authority under its node
                          kw=dict(fontsize=7.5, fontstyle='italic', color='#2f4f66', zorder=5)))
place_labels_above(fig, ax, items, obstacles_nodes=[(pos[n][0], pos[n][1], (area(n) ** 0.5) / 2) for n in G],
                   obstacle_boxes=[leg], max_shift=14, line_color='#777', line_width=0.45)
ax.axis('off')
fig.text(0.01, 0.01,
         f'{len(vend)} private vendors, {len(auth)} public authorities, {G.number_of_edges()} vendor–authority ties '
         f'({d["AI project"].nunique()} privately developed AI systems). Node size = number of ties; '
         'edge width = number of AI systems.\nLabels: all vendors (bold: ≥5 ties); authorities with '
         f'≥{AUTH_LABEL_MIN} vendor ties (italic). Bottom row: separate networks not connected to the main one (all nodes labelled).',
         fontsize=9, color='#555')
fig.savefig('figure2_en.png', dpi=200)

# --- Export to GEXF (Gephi): same layout, colours and sizes as the PNG
systems = d.groupby(['Auth', 'Vendor'])['AI project'].agg(lambda s: '; '.join(sorted(set(s))))
H = nx.Graph()
for n in G:
    k = G.nodes[n]['kind']
    t = 'Private vendor' if k == 'vendor' else G.nodes[n]['atype']
    hexc = COL['vendor'] if k == 'vendor' else COL[t]
    r, g_, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    x, y = pos[n]
    H.add_node(n, label=n, node_type='vendor' if k == 'vendor' else 'authority', category=t, degree=deg[n],
               labelled=bool(k == 'vendor' or deg[n] >= AUTH_LABEL_MIN or n in SMALL),
               viz={'color': {'r': r, 'g': g_, 'b': b, 'a': 1.0},
                    'position': {'x': float(x) * 1000, 'y': float(y) * 1000, 'z': 0.0},
                    'size': float(radius(n) * 1000)})
for u, v in G.edges():
    a, vend_ = (u, v) if G.nodes[u]['kind'] == 'auth' else (v, u)
    H.add_edge(u, v, weight=float(G[u][v]['weight']), ai_systems=systems[(a, vend_)])
nx.write_gexf(H, 'figure2_network.gexf')

top = sorted(((deg[v], v) for v in vend), reverse=True)[:12]
print('Top vendors by number of authorities:', top)
print('Components:', nx.number_connected_components(G))

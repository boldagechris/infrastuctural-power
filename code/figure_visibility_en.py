"""Two figures kept apart:
  M (methods)  The research funnel: what our data collection could make visible, and how it was obtained.
  F (findings) What remains invisible to an outside observer, by type of developer.
Universe: the full AI project register (closed systems shown as removed in M; F uses systems in use or planned).
Usage: python figure_visibility_en.py Datasæt.xlsx AI_datasets_uden_lukkede.xlsx
Outreach outcomes (not searched / no reply / declined) are not in the data yet: 'not found' is shown without a reason.
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import read_sheet, DATASETS_ACTIVE
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

SRC, DS = None, DATASETS_ACTIVE
BURG, BURG_MID, BLUE, BLUE_MID, BLUE_DARK, PINK, PINK_MID = '#5f2529', '#a3585c', '#bad1e0', '#86aac3', '#4d7896', '#f4e2e2', '#e3b5b7'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})

a = read_sheet(SRC, 'AI project')
a['n'] = a['AI project'].astype(str).str.strip()
a['St'] = a['Status'].astype(str).str.strip()
n_reg = a['n'].nunique()
closed = a.groupby('n')['St'].agg(lambda s: set(s) == {'Lukket'})
S = read_sheet(DS, 'AI systems')
n_act = len(S)
vt = S['Vendor type(s)'].fillna('').map(lambda x: 'Private company' if 'Private' in x else ('Public sector' if x else 'No vendor identified'))
n_vendor = int((S['Vendor known'] == 'Yes').sum())
priv = S[vt == 'Private company']
n_priv, n_priv_cloud = len(priv), int((priv['CSP known'] == 'Yes').sum())

act = a[a['St'] != 'Lukket']
src = act.groupby('n')['CSP source'].agg(lambda s: set(s.dropna().astype(str)))
found = S.set_index('AI system')['CSP known'] == 'Yes'
how = {'Contact with public authority': 0, 'Contact with vendor': 0, 'Web search': 0, 'Source not recorded': 0}
for name in found[found].index:
    s = src.get(name, set())
    if 'Contact with public authority' in s: how['Contact with public authority'] += 1
    elif 'Contact with vendor' in s: how['Contact with vendor'] += 1
    elif 'Web search' in s: how['Web search'] += 1
    else: how['Source not recorded'] += 1
n_found = int(found.sum())

# ---------------- Figure M: research funnel
fig = plt.figure(figsize=(13, 5.6))
gs = fig.add_gridspec(1, 2, width_ratios=[2.1, 1], wspace=0.45)
ax = fig.add_subplot(gs[0])
steps = [('Registered in the\nAI project register', n_reg, 'public sources and contact\nwith authorities'),
         ('In use or planned', n_act, f'{int(closed.sum())} closed systems removed'),
         ('Vendor identified', n_vendor, 'public bodies count as vendors\nwhen they built the system'),
         ('Private company vendor', n_priv, ''),
         ('Cloud provider or hosting\nidentified for the system', n_priv_cloud, 'among systems with a\nprivate company vendor')]
labels = [s[0] for s in steps][::-1]; vals = [s[1] for s in steps][::-1]; notes = [s[2] for s in steps][::-1]
cols = [BURG, BURG, BURG_MID, PINK_MID, PINK][::-1]
ax.barh(range(len(vals)), [n_reg] * len(vals), color='#f6f1f1', height=0.62, zorder=0)
ax.barh(range(len(vals)), vals, color=cols, height=0.62, edgecolor='white')
for i, (v, nt) in enumerate(zip(vals, notes)):
    ax.text(v + n_reg * 0.012, i + (0.1 if nt else 0), f'{v}  ({v / n_reg:.0%} of registered)', va='center', fontsize=9.5, fontweight='bold', color=BURG)
    if nt: ax.text(v + n_reg * 0.012, i - 0.2, nt, va='center', fontsize=8, color='#555', linespacing=1.1)
ax.set_yticks(range(len(vals))); ax.set_yticklabels(labels, fontsize=9.5)
ax.set_xlim(0, n_reg * 1.32); ax.set_xlabel('Number of AI systems')
ax.set_title('What the data collection made visible', loc='left', fontsize=11, color='#222')

ax2 = fig.add_subplot(gs[1])
keys = list(how); vals2 = [how[k] for k in keys]
cols2 = [BLUE_DARK, BLUE_MID, BLUE, '#d9d2d2']
bottom = 0
for k, v, c in zip(keys, vals2, cols2):
    ax2.bar([0], [v], bottom=bottom, color=c, width=0.55, edgecolor='white')
    ax2.text(0.33, bottom + v / 2, f'{k}: {v}', va='center', fontsize=9, color='#222')
    bottom += v
ax2.set_xlim(-0.4, 1.9); ax2.set_ylim(0, n_found * 1.05)
ax2.set_xticks([]); ax2.spines['bottom'].set_visible(False)
ax2.set_ylabel('AI systems with cloud provider or hosting identified')
ax2.set_title(f'How the {n_found} cloud/hosting entries\nwere obtained (all developers)', loc='left', fontsize=11, color='#222')
fig.suptitle('Figure M. The research funnel: what an outside observer could establish, step by step', x=0.01, ha='left',
             fontweight='bold', fontsize=12.5, y=1.02)
fig.text(0.01, -0.06, 'Each step depends on information being published or on someone answering our requests. The bars therefore show what our '
         'approach could make visible, not how AI systems or cloud dependencies are distributed in the public sector.', fontsize=8.5, color='#555')
fig.savefig('figure_M_research_funnel_en.png', dpi=200, bbox_inches='tight')
fig.savefig('figure_M_research_funnel_en.svg', bbox_inches='tight')
plt.close(fig)

# ---------------- Figure F: what remains invisible, by developer type
order = ['Public sector', 'Private company', 'No vendor identified']
T = pd.crosstab(vt, S['CSP known']).reindex(order).fillna(0).astype(int)
fig, ax = plt.subplots(figsize=(10, 3.6))
for i, g in enumerate(order):
    y, n = T.loc[g, 'Yes'], T.loc[g, 'Yes'] + T.loc[g, 'No']
    ax.barh(i, y, color=BURG, height=0.6, edgecolor='white')
    ax.barh(i, n - y, left=y, color=PINK, height=0.6, edgecolor='white')
    if y: ax.text(y / 2, i, f'{y}', ha='center', va='center', color='white', fontsize=9)
    ax.text(y + (n - y) / 2, i, f'{n - y}', ha='center', va='center', color='#333', fontsize=9)
    ax.text(n + 3, i, f'{y / n:.0%} visible', va='center', fontsize=9.5, fontweight='bold', color=BURG)
lab = {'Public sector': 'Built by a public body', 'Private company': 'Private company vendor', 'No vendor identified': 'No vendor identified'}
ax.set_yticks(range(len(order))); ax.set_yticklabels([f'{lab[g]}  (n = {T.loc[g].sum()})' for g in order])
ax.invert_yaxis(); ax.set_xlim(0, T.sum(axis=1).max() * 1.2)
ax.set_xlabel(f'AI systems in use or planned (n = {n_act})')
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=BURG, label='Cloud provider or hosting identified'),
                   Patch(color=PINK, label='Not identified (outreach outcome not yet coded)')],
          frameon=False, loc='upper center', bbox_to_anchor=(0.45, -0.28), ncol=2, fontsize=9)
ax.set_title('Figure F. Where the infrastructure layer stays invisible to an outside observer', loc='left', fontweight='bold', fontsize=12)
fig.savefig('figure_F_invisible_infrastructure_en.png', dpi=200, bbox_inches='tight')
fig.savefig('figure_F_invisible_infrastructure_en.svg', bbox_inches='tight')
print(dict(registered=n_reg, active=n_act, vendor=n_vendor, private=n_priv, private_cloud=n_priv_cloud, found=n_found, how=how)); print(T)

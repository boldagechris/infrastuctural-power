"""Figures on missing information.
  A  completeness of key variables (active AI systems, closed ones removed)
  C  share of active systems with missing information, by sector
Usage: python figure_missing_en.py   (run build_datasets.py first)
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import read_sheet, DATASETS_ACTIVE
import sys, re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from names_en import split_vendors

SRC, DS = None, DATASETS_ACTIVE
BURG, BURG_MID, BLUE, BLUE_DARK, PINK, PINK_MID = '#5f2529', '#a3585c', '#bad1e0', '#4d7896', '#f4e2e2', '#e3b5b7'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})

S = read_sheet(DS, 'AI systems')
N = len(S)
raw = read_sheet(SRC, 'AI project')
raw = raw[raw['Status'].astype(str).str.strip() != 'Lukket'].copy()
raw['AI project'] = raw['AI project'].astype(str).str.strip()
vend_raw = raw.groupby('AI project')['Vendor'].agg(lambda s: set(s.dropna().astype(str).str.strip()))


def vendor_state(name):
    v = vend_raw.get(name, set())
    if any(x.lower() != 'unknown' for x in v): return 'known'
    return 'unknown' if v else 'blank'


def state(col, unknown=('Unknown', 'Ukendt')):
    out = []
    for x in S[col]:
        if pd.isna(x): out.append('blank')
        elif str(x).strip() in unknown: out.append('unknown')
        else: out.append('known')
    return out


VARS = {
    'Vendor': [vendor_state(n) for n in S['AI system']],
    'Developer (private/public)': state('Public/private'),
    'Development (internal/external)': state('Internal/external/unknown'),
    'Sector': state('Område'),
    'Main function': state('Hovedfunktion'),
    'Status': state('Status'),
    'Cloud provider or hosting': ['known' if x == 'Yes' else 'unknown' for x in S['CSP known']],
    'Uses an LLM': state('LLM'),
    'Risk category': state('Risikokategori'),
}
T = pd.DataFrame({k: pd.Series(v).value_counts() for k, v in VARS.items()}).T.reindex(columns=['known', 'unknown', 'blank']).fillna(0).astype(int)
T = T.sort_values('known')

# ---------------- A: completeness
fig, ax = plt.subplots(figsize=(10, 5.6))
COLS = [('known', BURG, 'Information registered'), ('unknown', BLUE, 'Coded as unknown / searched but not found'),
        ('blank', PINK, 'Not registered (blank)')]
left = np.zeros(len(T))
for key, col, lab in COLS:
    v = T[key].values
    ax.barh(T.index, v, left=left, color=col, label=lab, height=0.66, edgecolor='white', linewidth=0.6)
    for i, (l, x) in enumerate(zip(left, v)):
        if x >= 12:
            ax.text(l + x / 2, i, f'{x}', ha='center', va='center', fontsize=8.5, color='white' if key == 'known' else '#333')
    left += v
for i, k in enumerate(T['known']):
    ax.text(N + 4, i, f'{k / N:.0%}', va='center', fontsize=9, fontweight='bold', color=BURG)
ax.text(N + 4, len(T) - 0.35, 'known', fontsize=8.5, color='#555', va='bottom')
ax.set_xlim(0, N * 1.1)
ax.set_xlabel(f'Number of AI systems (n = {N}, in use or planned)')
ax.legend(frameon=False, loc='upper center', bbox_to_anchor=(0.45, -0.13), ncol=3, fontsize=9)
ax.set_title('Figure A. Missing information about AI systems in the register', loc='left', fontweight='bold', fontsize=12)
fig.tight_layout()
fig.savefig('figure_missing_A_variables_en.png', dpi=200, bbox_inches='tight')
fig.savefig('figure_missing_A_variables_en.svg', bbox_inches='tight')
plt.close(fig)

# ---------------- C: missing by sector
S2 = S.assign(Sector=S['Område'].fillna('Ukendt').str.split('; ')).explode('Sector')
S2['Sector'] = S2['Sector'].replace({'Ukendt': 'Sector unknown', 'Byggeri': 'Construction'})
cols = {'Vendor': lambda d: d['Vendor known'] == 'No',
        'Developer\n(private/public)': lambda d: d['Public/private'].isna() | (d['Public/private'] == 'Unknown'),
        'Cloud provider\nor hosting': lambda d: d['CSP known'] == 'No',
        'Main function': lambda d: d['Hovedfunktion'].isna() | (d['Hovedfunktion'] == 'Ukendt'),
        'Uses an LLM': lambda d: d['LLM'].isna(),
        'Risk category': lambda d: d['Risikokategori'].isna()}
rows, ns = [], []
for sec, d in S2.groupby('Sector'):
    rows.append([fn(d).mean() for fn in cols.values()]); ns.append((sec, len(d)))
H = pd.DataFrame(rows, index=[s for s, _ in ns], columns=list(cols))
H['n'] = [n for _, n in ns]
H = H.sort_values('n', ascending=False)
H = pd.concat([H[H.index != 'Sector unknown'], H[H.index == 'Sector unknown']])
cmap = LinearSegmentedColormap.from_list('miss', ['#ffffff', PINK, PINK_MID, BURG_MID, BURG])
fig, ax = plt.subplots(figsize=(10, 0.42 * len(H) + 1.8))
M = H[list(cols)].values
ax.imshow(M, cmap=cmap, vmin=0, vmax=1, aspect='auto')
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        ax.text(j, i, f'{M[i, j]:.0%}', ha='center', va='center', fontsize=8.5, color='white' if M[i, j] > 0.6 else '#333')
ax.set_xticks(range(len(cols))); ax.set_xticklabels(list(cols), fontsize=9)
ax.xaxis.tick_top()
ax.set_yticks(range(len(H))); ax.set_yticklabels([f'{s}  (n = {n})' for s, n in zip(H.index, H['n'])], fontsize=9)
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(length=0)
ax.set_xticks(np.arange(-.5, len(cols), 1), minor=True); ax.set_yticks(np.arange(-.5, len(H), 1), minor=True)
ax.grid(which='minor', color='white', linewidth=1.5); ax.tick_params(which='minor', length=0)
ax.set_title('Figure C. Share of AI systems with missing information, by sector', loc='left', fontweight='bold', fontsize=12, pad=38)
fig.text(0.01, -0.02, f'AI systems in use or planned (n = {N}). Systems in several sectors count in each. '
         'Missing = blank, coded unknown, or searched but not found.', fontsize=8.5, color='#555')
fig.tight_layout()
fig.savefig('figure_missing_C_sectors_en.png', dpi=200, bbox_inches='tight')
fig.savefig('figure_missing_C_sectors_en.svg', bbox_inches='tight')
print(T.to_string())

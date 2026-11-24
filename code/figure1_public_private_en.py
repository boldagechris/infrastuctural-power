"""Figure 1 (public/private): AI systems by sector and developer type (private/public/unknown).
Projects with no Public/private coding are left out (as with blank development in figure1_en.py).

Variabler: 'AI project', 'Internal/external/unknown', 'Område' (ark 'AI project').
Kun kodede projekter indgår: rækker med Deleted = 1 eller tom Internal/external/unknown
eller tomt Område udelades. Analyseenhed: unikke AI-projekter.
Projekter med både Internal og External (samme system brugt af flere myndigheder)
kodes External, da systemet er udviklet uden for mindst én af de anvendende myndigheder.

Brug:  python figur1_v2.py Nyt_datasæt.xlsx
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import read_sheet, DATASETS_ACTIVE
import sys
import pandas as pd
import matplotlib.pyplot as plt

# Optional 2nd argument: a sheet with a pre-filtered selection (e.g. 'filter').
# In a pre-filtered sheet every project is kept and blank development counts as Unknown.
d = read_sheet(None, 'active')            # AI systems in use or planned (closed rows removed)
d = d[d['Deleted'] != 1].copy() if 'Deleted' in d.columns else d.copy()
d['PP'] = d['Public/private'].fillna('').astype(str).str.strip().replace('', None)
d = d.dropna(subset=['PP', 'Område'])


def saml(s):
    v = set(s)
    if 'Private' in v: return 'Private'
    if 'Public' in v: return 'Public'
    return 'Unknown'


p = d.groupby('AI project').agg(PP=('PP', saml), Omr=('Område', 'first'))
p.to_csv('projects_figure1_pp_en.csv')

DA_OMR = {'Health': 'Health', 'Other': 'Other', 'Case processing': 'Case processing',
          'Employment': 'Employment', 'Social work': 'Social work', 'Transportation': 'Transportation',
          'Nature and environment': 'Nature and environment', 'Construction': 'Construction', 'Education': 'Education',
          'Immigration and asylum': 'Immigration and asylum', 'Culture': 'Culture', 'Police': 'Police',
          'Ukendt': 'Sector unknown', 'Byggeri': 'Construction'}
DA_IE = {'Private': 'Private developer', 'Public': 'Public developer', 'Unknown': 'Unknown developer'}
FARVER = {'Private developer': '#5f2529', 'Public developer': '#bad1e0', 'Unknown developer': '#f4e2e2'}

p['Område'] = p['Omr'].map(DA_OMR).fillna(p['Omr'])
p['Udvikling'] = p['PP'].map(DA_IE)
tab = pd.crosstab(p['Område'], p['Udvikling'])[[c for c in FARVER if c in set(p['Udvikling'])]]
# Sortering: efter antal eksternt udviklede, dernæst internt; 'Andet' sidst
tab = tab.assign(_tot=tab.sum(axis=1)).sort_values('_tot', ascending=False, kind='stable').drop(columns='_tot')   # by total
orden = [o for o in tab.index if o != 'Sector unknown'] + [o for o in tab.index if o == 'Sector unknown']   # unknown sector last
tab = tab.loc[orden]

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False})
fig, ax = plt.subplots(figsize=(9, 5.8))
left = pd.Series(0.0, index=tab.index)
for col in tab.columns:  # stablet: orange, blå, grå
    ax.barh(tab.index, tab[col], left=left, color=FARVER[col], label=col, height=0.66,
            edgecolor='white', linewidth=0.5)
    for i, (l, v) in enumerate(zip(left, tab[col])):
        if v >= 2:
            ax.text(l + v / 2, i, int(v), ha='center', va='center', fontsize=8.5,
                    color='white' if col == 'Private developer' else '#333')
    left += tab[col]
for i, n in enumerate(tab.sum(axis=1)):
    ax.text(n + 0.5, i, f'{int(n)}', va='center', fontsize=8.5, color='#333', fontweight='bold')
ax.invert_yaxis()
ax.set_xlim(0, tab.sum(axis=1).max() * 1.08)
ax.set_xlabel('Number of AI systems')
ax.legend(frameon=False, ncol=1, loc='center right', bbox_to_anchor=(1, 0.55))
ax.set_title('Figure 1. AI systems by sector and developer (private/public)', loc='left', fontweight='bold', fontsize=12)
fig.tight_layout()
fig.savefig('figure1_public_private_en.png', dpi=200)

print(tab.assign(I_alt=tab.sum(axis=1)).to_string())

"""Three datasets from the 902 rows in 'AI project':
  1. AI systems (one row per unique system)
  2. Vendors   (one row per vendor; cells naming several vendors are split)
  3. CSP       (one row per cloud service provider / hosting form)
  + System-CSP links (long format) and a README.
Usage: python build_datasets.py Datasæt.xlsx out.xlsx
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from common import read_sheet, DATASETS_ACTIVE
import sys, re
from collections import defaultdict
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from names_en import split_vendors

SRC, OUT = 'ai_register.csv', sys.argv[1]
a = read_sheet(None, 'AI project')


def s(v):
    if pd.isna(v): return None
    v = str(v).strip()
    return v or None


for c in a.columns:
    if c not in ("1 = speciale, 2 = nye",): a[c] = a[c].map(s)
a['AI project'] = a['AI project'].map(s)
a = a.dropna(subset=['AI project'])
N_SOURCE = len(a)
EXCLUDE_CLOSED = '--exclude-closed' in sys.argv
if EXCLUDE_CLOSED:                                   # drop every row marked 'Lukket'
    closed_rows = (a['Status'] == 'Lukket').sum()
    gone = set(a['AI project']) - set(a.loc[a['Status'] != 'Lukket', 'AI project'])
    a = a[a['Status'] != 'Lukket'].copy()
UNK = re.compile(r'^(unknown|ukendt|n/?a|none|-|\?)$', re.I)


VENDOR_FIX = {'Deloitte Statsautoriseret Revisionspartnerselskab': 'Deloitte', 'NTT DATA Business Solutions': 'NTT Data Business Solutions', 'indsigt.ai / Potentielt KOMPAS': 'indsigt.ai',
              'Indsigt.ai': 'indsigt.ai', 'syv.ai (open source)': 'syv.ai', 'Epic Systems Corporation (US)': 'Epic Systems Corporation'}


def vendors_of(cell):
    cell = s(cell)
    return [VENDOR_FIX.get(v, v) for v in split_vendors(cell) if not UNK.match(v)] if cell else []


def csp_parts(cell):
    out = []
    cell = s(cell)
    if not cell: return out
    for c in re.split(r',\s*', cell):
        c = re.sub(r'\s*\(.*?\)\s*', '', c).strip()          # 'Servicepoint (Interxion …)' -> 'Servicepoint'
        c = {'OVH Cloud': 'OVHCloud', 'Google Platform': 'Google', 'Microzoft': 'Microsoft',
             'Interxion Deutschland GmbH': 'Interxion', 'team.blue Denmark': 'team.blue'}.get(c, c)
        if c: out.append(c)
    return out


def hosting(cell):
    cell = s(cell)
    if not cell: return None
    c = cell.lower()
    if c.startswith('vendor hosted'): return 'Vendor-hosted (no external CSP)'
    if c.startswith('on-prem'): return 'On-premises'
    return re.sub(r'\s*\(.*?\)\s*', '', cell).strip()


def uniq(xs):
    seen, out = set(), []
    for x in xs:
        if x and x not in seen: seen.add(x); out.append(x)
    return out


def multi(series, split=False):
    vals = []
    for v in series.dropna():
        vals += [p.strip() for p in str(v).split(',')] if split else [v]
    return '; '.join(uniq(vals)) or None


PUBLIC_INFRA = {'Statens IT', 'Danish National Genome Center', 'Regional IT Syddanmark', 'Danmarks Tekniske Universitet',
                'DCAI - Danish Centre for AI Innovation'}

# ---------------- long table: system x CSP x layer (from each row)
links = []
for _, r in a.iterrows():
    for layer, col in [('IaaS', 'CSP IaaS'), ('PaaS', 'CSP PaaS'), ('SaaS', 'CSP SaaS')]:
        for c in csp_parts(r[col]):
            links.append((r['AI project'], c, layer, 'Public-sector infrastructure' if c in PUBLIC_INFRA else 'Cloud / AI service provider', s(r['Offentlig myndighed'])))
    h = hosting(r['CSP'])
    if h:
        typ = 'No external CSP' if h in ('Vendor-hosted (no external CSP)', 'On-premises') else 'Public-sector infrastructure'
        links.append((r['AI project'], h, 'Not specified', typ, s(r['Offentlig myndighed'])))
L = pd.DataFrame(links, columns=['AI system', 'CSP', 'Layer', 'CSP type', 'Authority'])

AUTHS = set(a['Offentlig myndighed'].dropna().map(str).str.strip())
PUB_RE = re.compile(r'Kommune|Region|Hospital|Sygehus|Universitet|styrelse|Styrelsen|Institut|^DTU|Danmarks Tekniske|Center for Digital '
                    r'Psykiatri|Praktiserende læger|Rigshospital|OUH|Telecare|Centre for Clinical Robotics|KOMBIT|Udbetaling|Statens|EU-LISA|'
                    r'Koncern IT|^CFU|Regional IT|Politi|SIRI|MedCom|Sundhed', re.I)
PRIVATE_OVERRIDE = {'Alexandra Instituttet', 'SAS Institute'}
PUBLIC_EXTRA = {'IT University of Copenhagen', 'GeoDanmark'}


def vendor_type(v):
    if v in PRIVATE_OVERRIDE: return 'Private company'
    return 'Public sector' if (v in AUTHS or v in PUBLIC_EXTRA or PUB_RE.search(v)) else 'Private company'


FOUND_COL = 'Hosting or CSP found' if 'Hosting or CSP found' in a.columns else None

# ---------------- Vendor sheet: cloud data per vendor (vendor level, not per system)
def norm(x):
    x = re.sub(r'\b(ApS|A/S|AB|AS|Inc\.?|Ltd\.?|PTE\.?|DK|Denmark|DANMARK|Group)\b', '', str(x), flags=re.I)
    return re.sub(r'[^a-z0-9]', '', x.lower())
VS = read_sheet(None, 'Vendor')
CSP_FIX = {'OCI': 'Oracle', 'Oracle Cloud': 'Oracle', 'raffle.ai ApS': 'raffle.ai', 'Raffle.ai': 'raffle.ai', 'team.blue Denmark A/S': 'team.blue',
           'team.blue Denmark': 'team.blue', 'Cleura AB': 'Cleura', 'Cantab Research Ltd.': 'Speechmatics', 'Microzoft Azure': 'Microsoft',
           'Microsoft Azure': 'Microsoft', 'Amazon Web Services': 'Amazon', 'Google Cloud': 'Google', 'Google Platform': 'Google',
           'UpCloud Ltd.': 'UpCloud', 'OVH Cloud': 'OVHCloud', 'Syv.ai': 'syv.ai', 'Interxion Deutschland GmbH': 'Interxion'}
VCSP = defaultdict(list)
for _, r0 in VS.iterrows():
    if pd.isna(r0['CSP']): continue
    lay = s(r0.get('CSM')) or 'Not specified'
    lay = 'Not specified' if lay == 'Non specified' else lay
    for vv in split_vendors(r0['Vendor']):
        vv = VENDOR_FIX.get(vv, vv)
        for c in str(r0['CSP']).replace('Anthropic Ireland, Limited', 'Anthropic').split(','):
            c = re.sub(r'\s*\(.*?\)\s*', '', c).strip(); c = CSP_FIX.get(c, c)
            if c and len(c.split()) <= 5 and not re.search(r'[!?]|:\)', c):
                if norm(c) == norm(vv) and c not in ('Microsoft', 'Amazon', 'Google'): c = 'Vendor-hosted (no external CSP)'
                VCSP[norm(vv)].append((c, lay))

# ---------------- 1. AI systems
rows = []
for name, g in a.groupby('AI project', sort=False):
    V = uniq(v for cell in g['Vendor'] for v in vendors_of(cell))
    pp = set(g['Public/private'].dropna())
    ie = set(g['Internal/external/unknown'].dropna())
    st = set(g['Status'].dropna())
    rnd = sorted(set(g['1 = speciale, 2 = nye'].dropna().astype(str).str.replace(r'\.0$', '', regex=True)))
    lg = L[L['AI system'] == name]
    rows.append({
        'AI system': name,
        'Vendor(s)': '; '.join(V) or None,
        'No. of vendors': len(V),
        'Vendor known': 'Yes' if V else 'No',
        'Vendor type(s)': '; '.join(uniq(vendor_type(v) for v in V)) or None,
        'Private company vendor known': 'Yes' if any(vendor_type(v) == 'Private company' for v in V) else 'No',
        'Public/private': 'Private' if 'Private' in pp else 'Public' if 'Public' in pp else 'Unknown' if 'Unknown' in pp else None,
        'Public/private (all codings)': '; '.join(sorted(pp)) or None,
        'Internal/external/unknown': 'External' if 'External' in ie else 'Internal' if 'Internal' in ie else 'Unknown' if 'Unknown' in ie else None,
        'Område': multi(g['Område']),
        'Hovedfunktion': multi(g['Hovedfunktion'], split=True),
        'Data collection round': '; '.join(rnd) or None,
        'Status': 'I brug' if 'I brug' in st else 'Planlægges taget i brug' if 'Planlægges taget i brug' in st else 'Lukket' if st == {'Lukket'} else None,
        'Status (all rows)': '; '.join(sorted(st)) or None,
        'Closed at all authorities': 'Yes' if st == {'Lukket'} else 'No',
        'No. of rows': len(g),
        'No. of authorities': g['Offentlig myndighed'].nunique(),
        'Authorities': multi(g['Offentlig myndighed']),
        'Udbredelse': multi(g['Udbredelse'], split=True),
        'CSP IaaS': '; '.join(uniq(lg.loc[lg.Layer == 'IaaS', 'CSP'])) or None,
        'CSP PaaS': '; '.join(uniq(lg.loc[lg.Layer == 'PaaS', 'CSP'])) or None,
        'CSP SaaS': '; '.join(uniq(lg.loc[lg.Layer == 'SaaS', 'CSP'])) or None,
        'Hosting (no external CSP / other)': '; '.join(uniq(lg.loc[lg['CSP type'] != 'Cloud / AI service provider', 'CSP'])) or None,
        'CSP known': (('Yes' if any(str(x).strip().lower() == 'yes' for x in g[FOUND_COL].dropna()) else 'No')
                      if FOUND_COL else ('Yes' if len(lg) else 'No')),
        'LLM': 'Ja' if 'Ja' in set(g['LLM'].dropna()) else 'Nej' if len(g['LLM'].dropna()) else None,
        'Signaturprojekt': 'Ja' if 'Ja' in set(g['Signaturprojekt'].dropna()) else 'Nej' if len(g['Signaturprojekt'].dropna()) else None,
        'Risikokategori': multi(g['Risikokategori']),
    })
SYS = pd.DataFrame(rows).sort_values('AI system', key=lambda x: x.str.lower()).reset_index(drop=True)

# ---------------- 2. Vendors
vs = defaultdict(lambda: {'systems': [], 'auth': set(), 'rows': 0})
for _, r in a.iterrows():
    for v in vendors_of(r['Vendor']):
        d = vs[v]; d['rows'] += 1
        if r['AI project'] not in d['systems']: d['systems'].append(r['AI project'])
        if s(r['Offentlig myndighed']): d['auth'].add(s(r['Offentlig myndighed']))
sysinfo = SYS.set_index('AI system')
vrows = []
for v, d in vs.items():
    si = sysinfo.loc[d['systems']]
    lv = L[L['AI system'].isin(d['systems'])]
    pp = si['Public/private'].fillna('Not coded').value_counts()
    vrows.append({
        'Vendor': v,
        'Vendor type': vendor_type(v),
        'No. of AI systems': len(d['systems']),
        'No. of authorities': len(d['auth']),
        'No. of rows': d['rows'],
        'Systems: Private': int(pp.get('Private', 0)), 'Systems: Public': int(pp.get('Public', 0)),
        'Systems: Unknown': int(pp.get('Unknown', 0)), 'Systems: Not coded': int(pp.get('Not coded', 0)),
        'Systems in use/planned': int((si['Closed at all authorities'] == 'No').sum()),
        'Område': '; '.join(uniq(x for o in si['Område'].dropna() for x in o.split('; '))) or None,
        'CSPs (via its systems)': '; '.join(uniq(lv.loc[lv['CSP type'] == 'Cloud / AI service provider', 'CSP'])) or None,
        'Hosting (no external CSP / other)': '; '.join(uniq(lv.loc[lv['CSP type'] != 'Cloud / AI service provider', 'CSP'])) or None,
        'CSPs (Vendor sheet)': '; '.join(uniq(c for c, _ in VCSP.get(norm(v), []))) or None,
        'CSP layers (Vendor sheet)': '; '.join(uniq(f'{c} ({l})' for c, l in VCSP.get(norm(v), []))) or None,
        'AI systems': '; '.join(d['systems']),
        'Authorities': '; '.join(sorted(d['auth'])),
    })
VEN = pd.DataFrame(vrows).sort_values(['No. of AI systems', 'Vendor'], ascending=[False, True]).reset_index(drop=True)

# ---------------- 3. CSP
crows = []
sysv = SYS.set_index('AI system')['Vendor(s)']
for c, g in L.groupby('CSP'):
    systems = uniq(g['AI system'])
    lay = g.drop_duplicates(['AI system', 'Layer'])['Layer'].value_counts()
    vend = uniq(v for sname in systems for v in (s(sysv.get(sname)) or '').split('; ') if v)
    crows.append({
        'CSP': c,
        'CSP type': g['CSP type'].iloc[0],
        'Big Three': 'Yes' if c in ('Microsoft', 'Amazon', 'Google') else 'No',
        'No. of AI systems': len(systems),
        'Systems: IaaS': int(lay.get('IaaS', 0)), 'Systems: PaaS': int(lay.get('PaaS', 0)),
        'Systems: SaaS': int(lay.get('SaaS', 0)), 'Systems: not specified': int(lay.get('Not specified', 0)),
        'No. of vendors (via systems)': len(vend),
        'No. of authorities': g['Authority'].nunique(),
        'No. of rows': len(g.drop_duplicates(['AI system', 'Authority', 'Layer'])),
        'Vendors': '; '.join(vend) or None,
        'AI systems': '; '.join(systems),
    })
CSP = pd.DataFrame(crows).sort_values(['No. of AI systems', 'CSP'], ascending=[False, True]).reset_index(drop=True)
LINKS = (L.groupby(['AI system', 'CSP', 'Layer', 'CSP type'])['Authority'].agg(lambda x: x.dropna().nunique())
         .reset_index().rename(columns={'Authority': 'No. of authorities'}))
LINKS.insert(1, 'Vendor(s)', LINKS['AI system'].map(sysv))

# ---------------- write
with pd.ExcelWriter(OUT, engine='openpyxl') as w:
    pd.DataFrame().to_excel(w, 'README', index=False)
    SYS.to_excel(w, 'AI systems', index=False)
    VEN.to_excel(w, 'Vendors', index=False)
    CSP.to_excel(w, 'CSP', index=False)
    LINKS.to_excel(w, 'System-CSP links', index=False)

wb = load_workbook(OUT)
ARIAL = 'Arial'
HEAD = PatternFill('solid', fgColor='1D4E6E')
WRAP = {'Kort beskrivelse', 'AI systems', 'Authorities', 'Vendors', 'Hovedfunktion', 'Vendor(s)'}
for ws in wb.worksheets[1:]:
    for cell in ws[1]:
        cell.font = Font(name=ARIAL, bold=True, color='FFFFFF'); cell.fill = HEAD
        cell.alignment = Alignment(wrap_text=True, vertical='center')
    for row in ws.iter_rows(min_row=2):
        for cell in row: cell.font = Font(name=ARIAL, size=10); cell.alignment = Alignment(vertical='top')
    for i, cell in enumerate(ws[1], 1):
        vals = [len(str(c.value)) for c in ws[get_column_letter(i)][1:200] if c.value is not None]
        width = max([len(str(cell.value))] + vals) if vals else len(str(cell.value))
        ws.column_dimensions[get_column_letter(i)].width = min(60 if cell.value in WRAP else 34, max(10, width + 2))
    ws.row_dimensions[1].height = 32
    ws.freeze_panes = 'B2'; ws.auto_filter.ref = ws.dimensions

L_ = lambda col: get_column_letter(list(SYS.columns).index(col) + 1)
r = wb['README']
lines = [
    ('Datasets built from the AI project sheet', None),
    (f'Source: {SRC.split("/")[-1]}, sheet "AI project". Built {__import__("datetime").date.today():%d %b %Y} from the working file of 23 Nov 2026. ' + (f'Filter: all {closed_rows} rows with Status = Lukket removed ({len(gone)} systems closed at every authority drop out; systems still in use elsewhere keep their other rows).' if EXCLUDE_CLOSED else 'All rows, no filters.'), None),
    ('', None),
    ('Count', 'Value'),
    ('Rows in AI project (source)', N_SOURCE),
    ('Rows used (after filter)', len(a)),
    ('Unique AI systems', "=COUNTA('AI systems'!A:A)-1"),
    ('… with a known vendor', f"=COUNTIF('AI systems'!{L_('Vendor known')}:{L_('Vendor known')},\"Yes\")"),
    ('… with a known private company vendor', f"=COUNTIF('AI systems'!{L_('Private company vendor known')}:{L_('Private company vendor known')},\"Yes\")"),
    ('… with a known CSP or hosting form', f"=COUNTIF('AI systems'!{L_('CSP known')}:{L_('CSP known')},\"Yes\")"),
    ('… closed at all authorities', f"=COUNTIF('AI systems'!{L_('Closed at all authorities')}:{L_('Closed at all authorities')},\"Yes\")"),
    ('Unique vendors', "=COUNTA(Vendors!A:A)-1"),
    ('… private companies', "=COUNTIF(Vendors!B:B,\"Private company\")"),
    ('… public-sector developers (authority itself or other public body)', "=COUNTIF(Vendors!B:B,\"Public sector\")"),
    ('Unique CSPs / hosting forms', "=COUNTA(CSP!A:A)-1"),
    ('System–CSP links', "=COUNTA('System-CSP links'!A:A)-1"),
    ('', None),
    ('Rules', None),
    ('One row in AI project = one system at one authority. Systems are matched on their name (trimmed).', None),
    ('A cell naming several vendors ("Thales, EU-LISA") counts as several vendors; legal suffixes stay with the company ("Groove X, Inc."). "Unknown" and blank are not vendors.', None),
    ('Vendor spellings merged: NTT DATA -> NTT Data Business Solutions; Indsigt.ai and "indsigt.ai / Potentielt KOMPAS" -> indsigt.ai; "syv.ai (open source)" -> syv.ai; "Epic Systems Corporation (US)" -> Epic Systems Corporation.', None),
    ('Public/private per system: Private if any row is Private, else Public, else Unknown; blank = not coded. All codings are listed in the next column.', None),
    ('Status per system: I brug if any row is in use, else Planlægges taget i brug, else Lukket if every row is closed.', None),
    ('CSP comes from the columns CSP IaaS / PaaS / SaaS (one provider per comma) and the column CSP (vendor-hosted, on-premises, public-sector infrastructure). Text in brackets is dropped; OVH Cloud -> OVHCloud, team.blue Denmark -> team.blue, Interxion Deutschland GmbH -> Interxion.', None),
    ('CSP type: Cloud / AI service provider (commercial), Public-sector infrastructure (Statens IT, Danish National Genome Center, Regional IT Syddanmark, DTU, DCAI), or No external CSP (vendor-hosted, on-premises).', None),
    ('Vendors per CSP are the vendors of the systems that use the CSP.', None),
    ('Vendor type: "Public sector" when the vendor is a public authority or other public body (in-house development is coded with the authority itself as vendor); otherwise "Private company". Alexandra Instituttet and SAS Institute count as private.', None),
    ('CSP known (AI systems sheet) = the column "Hosting or CSP found" is yes on at least one of the system\'s rows (matches Pivot Table 3).', None),
    ('Vendors sheet: "CSPs (Vendor sheet)" lists the providers given for the vendor in the Vendor sheet (vendor level, not tied to a specific system). Providers are named by company (Microsoft, Amazon, Google, Oracle).', None),
]
RULES_ROW = [k for k, _ in lines].index('Rules') + 1
for i, (k, v) in enumerate(lines, 1):
    r.cell(i, 1, k).font = Font(name=ARIAL, size=10, bold=(i in (1, 4, RULES_ROW)))
    if v is not None:
        c = r.cell(i, 2, v); c.font = Font(name=ARIAL, size=10, bold=(i == 4))
r['A1'].font = Font(name=ARIAL, size=13, bold=True)
r['B5'].font = Font(name=ARIAL, size=10, color='0000FF'); r['B6'].font = Font(name=ARIAL, size=10, color='0000FF')
r.cell(6, 3, 'Counted in Python from the source file').font = Font(name=ARIAL, size=9, italic=True, color='666666')
r.cell(5, 3, 'Counted from the source file').font = Font(name=ARIAL, size=9, italic=True, color='666666')
r.column_dimensions['A'].width = 48; r.column_dimensions['B'].width = 12
for i in range(RULES_ROW + 1, len(lines) + 1):
    r.cell(i, 1).alignment = Alignment(wrap_text=False)
wb.save(OUT)
print(len(SYS), 'systems', len(VEN), 'vendors', len(CSP), 'CSPs', len(LINKS), 'links')
print('known vendor', (SYS['Vendor known'] == 'Yes').sum(), 'known CSP', (SYS['CSP known'] == 'Yes').sum())
print(CSP[['CSP', 'CSP type', 'No. of AI systems']].to_string())

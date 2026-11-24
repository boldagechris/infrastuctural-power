"""Create the published input data (../data/*.csv) from the project's working Excel file.

Only the columns needed for the analysis are kept. Free-text columns are left out because they contain
personal data (names, e-mail addresses and phone numbers of public employees in 'Kilder') or long descriptions
copied from the sources the register builds on (see README, 'Data sources').

Usage: python export_from_excel.py Datasæt.xlsx
"""
import os, sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import REGISTER, VENDOR_CLOUD

REGISTER_COLS = ['AI project', 'Vendor', 'Vendor=konsulent?', 'Internal/external/unknown', 'Public/private',
                 '1 = speciale, 2 = nye', 'Offentlig myndighed', 'Område', 'Hovedfunktion', 'Status', 'Udbredelse',
                 'Signaturprojekt', 'LLM', 'Risikokategori', 'Infrastruktur / Cloud',
                 'CSP', 'CSP IaaS', 'CSP PaaS', 'CSP SaaS', 'Hosting or CSP found', 'CSP source', 'CSP source (link)']
DROPPED_REGISTER = ['Kort beskrivelse', 'Kilder', 'Menneskeretlige overvejelser', 'I. Hvor bruges systemet?',
                    'II. Hvornår implementeret?', 'III. Brug af AI?', 'IV. Træningsdata?', 'V. Sikkerhedsforanstaltninger?',
                    'VI. Pilotprojekter?', 'VII. Begrundelse?', 'VIII. Lignende systemer?', 'Offentlig myndighed.1',
                    'Offentlig myndighed.2', 'Public authority', ' ']
VENDOR_COLS = ['Vendor', 'AI system', 'CSP', 'CSM', 'Cloud service source', 'CSM confidence', 'Cloud service description',
               'Link', 'Notes']
# 'Notes' holds the coders' reasoning (e.g. why a provider does not apply, or that nothing could be found).
# Check it for personal names before each release.

src = sys.argv[1]
a = pd.read_excel(src, sheet_name='AI project')
missing = [c for c in REGISTER_COLS if c not in a.columns]
if missing: sys.exit(f'Missing columns in AI project: {missing}')
a = a[REGISTER_COLS]
a = a[a['AI project'].notna()]
v = pd.read_excel(src, sheet_name='Vendor')
v = v[[c for c in VENDOR_COLS if c in v.columns]].dropna(how='all')
a.to_csv(REGISTER, index=False, encoding='utf-8')
v.to_csv(VENDOR_CLOUD, index=False, encoding='utf-8')
print(f'{len(a)} register rows -> {REGISTER}\n{len(v)} vendor rows -> {VENDOR_CLOUD}')

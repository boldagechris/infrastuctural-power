"""Shared paths and data loading for the replication code.

All scripts read the published input data in ../data:
  ai_register.csv   one row per AI system x public authority (the 'AI project' sheet, without free-text columns)
  vendor_cloud.csv  one row per vendor x cloud provider x cloud layer (the 'Vendor' sheet)
and write their outputs to the current working directory (run_all.sh runs them from ../figures).
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
DERIVED = os.path.join(DATA, 'derived')
REGISTER = os.path.join(DATA, 'ai_register.csv')
VENDOR_CLOUD = os.path.join(DATA, 'vendor_cloud.csv')
DATASETS_ALL = os.path.join(DERIVED, 'ai_datasets_all.xlsx')
DATASETS_ACTIVE = os.path.join(DERIVED, 'ai_datasets_active.xlsx')


def load_register(active_only=False):
    """The register. active_only=True drops every row with Status = 'Lukket' (closed)."""
    d = pd.read_csv(REGISTER, encoding='utf-8')
    d['AI project'] = d['AI project'].astype(str).str.strip()
    if active_only:
        d = d[d['Status'].astype(str).str.strip() != 'Lukket'].copy()
    return d


# Vendor-sheet rows that are kept in the data but left out of the analysis, with the reason.
#  - rows whose note says the cloud information does not apply to the AI system in question;
#  - entries in the CSP column that are AI products a vendor distributes, not cloud providers.
NOT_APPLICABLE_NOTE = r'^\s*Gælder ikke'          # e.g. Human Bytes: "Gælder ikke AI-projektet, AI Mammo, som hostes on-prem"
NOT_A_CLOUD_PROVIDER = {
    'Human Bytes': {'Combinostics', 'Eyenuk', 'Harrison.ai', 'Milvue', 'Screenpoint Medical', 'Therapanacea'},
}


def load_vendor_cloud(clean=True, verbose=False):
    """Vendor x cloud provider rows. clean=True applies the two exclusions above."""
    v = pd.read_csv(VENDOR_CLOUD, encoding='utf-8')
    if not clean:
        return v
    notes = v['Notes'].astype(str) if 'Notes' in v.columns else pd.Series('', index=v.index)
    na = notes.str.contains(NOT_APPLICABLE_NOTE, regex=True, na=False)
    prod = v.apply(lambda r: str(r['CSP']).strip() in NOT_A_CLOUD_PROVIDER.get(str(r['Vendor']).strip(), set()), axis=1)
    if verbose:
        for i in v.index[na | prod]:
            why = 'note: not applicable' if na[i] else 'not a cloud provider'
            print(f"  excluded vendor-cloud row: {v.at[i, 'Vendor']} -> {v.at[i, 'CSP']} ({why})")
    return v[~(na | prod)].copy()


def read_sheet(src, sheet):
    """Drop-in for the pd.read_excel(src, sheet) calls the scripts were written with.
    'AI project' = full register, 'aktive'/'active' = register without closed rows, 'Vendor' = vendor cloud data;
    any other sheet is read from the Excel file `src` (used for the derived datasets)."""
    if sheet == 'AI project': return load_register(False)
    if sheet in ('aktive', 'active'): return load_register(True)
    if sheet == 'Vendor': return load_vendor_cloud(verbose=True)
    return pd.read_excel(src, sheet_name=sheet)

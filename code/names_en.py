"""English display names for authorities and Danish-named vendors."""
AUTH = {
    'Aarhus Universitetshospital': 'Aarhus University Hospital',
    'Beskæftigelsesministeriet': 'Ministry of Employment',
    'Bispebjerg Hospital': 'Bispebjerg Hospital',
    'CAMES Rigshospitalet': 'CAMES, Copenhagen University Hospital (Rigshospitalet)',
    'Familieretshuset': 'Agency of Family Law',
    'Frederiksberg Forsyning': 'Frederiksberg Utilities',
    'Frederiksberg Hospital': 'Frederiksberg Hospital',
    'Grænsemyndighederne': 'Danish Border Authorities',
    'Miljøstyrelsen': 'Danish Environmental Protection Agency',
    'Minksekretariatet': 'Mink Secretariat',
    'Naturstyrelsen': 'Danish Nature Agency',
    'Nævnenes Hus': 'Danish Appeals Boards (Nævnenes Hus)',
    'OUH Svendborg': 'Odense University Hospital, Svendborg',
    'Odense Universitetshospital': 'Odense University Hospital',
    'Parkeringsklagenævnet': 'Parking Appeals Board',
    'Patent- og Varemærkestyrelsen': 'Danish Patent and Trademark Office',
    'Plan- og Landdistriktsstyrelsen': 'Danish Agency for Planning and Rural Districts',
    'Politiet': 'Danish Police',
    'Region Hovedstaden': 'Capital Region of Denmark',
    'Region Midtjylland': 'Central Denmark Region',
    'Region Nordjylland': 'North Denmark Region',
    'Region Sjælland': 'Region Zealand',
    'Region Syddanmark': 'Region of Southern Denmark',
    'Regionshospital Nordjylland': 'North Denmark Regional Hospital',
    'Regionshospitalet Horsens': 'Horsens Regional Hospital',
    'Regionshospitalet Randers': 'Randers Regional Hospital',
    'Rigshospitalet': 'Copenhagen University Hospital (Rigshospitalet)',
    'Rigshospitalet-Glostrup': 'Copenhagen University Hospital, Glostrup',
    'Rigsrevisionen': 'National Audit Office of Denmark',
    'Social- og Boligstyrelsen': 'National Board of Social Services and Housing',
    'Styrelsen for Patientklager': 'Danish Patient Complaints Board',
    'Syddansk Universitet': 'University of Southern Denmark',
    'Sygehus Sønderjylland': 'Hospital of Southern Jutland',
    'Trafikstyrelsen': 'Danish Transport Authority',
    'Udbetaling Danmark': 'Payment Denmark (Udbetaling Danmark)',
    'Udlændingestyrelsen': 'Danish Immigration Service',
    'Københavns Universitet': 'University of Copenhagen',
    'Statens Serum Institut': 'Statens Serum Institut',
    'Lægemiddelstyrelsen (Danish Medicines Agency)': 'Danish Medicines Agency',
    'Digitaliseringsstyrelsen': 'Danish Agency for Digital Government',
    'Udlændinge- og Integrationsministeriet': 'Ministry of Immigration and Integration',
    'Aalborg Universitetshospital': 'Aalborg University Hospital',
    'Hvidovre Hospital': 'Hvidovre Hospital',
    'Færdselsstyrelsen': 'Danish Road Traffic Authority',
    'Sundhedsstyrelsen': 'Danish Health Authority',
    'Sydvestjysk Sygehus': 'Hospital South West Jutland',
    'Sygehus Lillebælt': 'Lillebaelt Hospital',
}
MUNI_FIX = {'Københavns': 'Copenhagen', 'Bornholms': 'Bornholm', 'Nordfyns': 'Nordfyn'}



VENDOR = {'TOPDESK DANMARK': 'TOPdesk Denmark', 'SERVICENOW DENMARK': 'ServiceNow Denmark',
          'Alexandra Instituttet': 'The Alexandra Institute', 'EG Danmark': 'EG Denmark'}


def en(name):
    if name in AUTH: return AUTH[name]
    if name in VENDOR: return VENDOR[name]
    if name.endswith(' Kommune'):
        place = name[:-len(' Kommune')]
        return f'{MUNI_FIX.get(place, place)} Municipality'
    return name


def short_en(name):
    """Short label for drawings: 'Aarhus' instead of 'Aarhus Municipality'."""
    return en(name).replace(' Municipality', '')


import re as _re
_LEGAL = _re.compile(r'^(inc\.?|ltd\.?|limited|a/s|aps|ab|as|gmbh|llc|s\.?a\.?|oy|corp\.?|co\.?|pte\.?(\s*ltd\.?)?)$', _re.I)


def split_vendors(v):
    """A cell naming several vendors ('Thales, EU-LISA') is several vendors. Split on commas and
    semicolons, but keep legal suffixes with the company ('Groove X, Inc.' stays one vendor)."""
    out = []
    for p in _re.split(r'[;,]', str(v)):
        p = p.strip()
        if not p: continue
        if out and _LEGAL.match(p): out[-1] = out[-1] + ', ' + p
        else: out.append(p)
    return out

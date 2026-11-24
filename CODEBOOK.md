# Codebook

Data snapshot: 23 November 2026. Column names in the input files are kept as in the project's working file
(partly Danish), so that the code can run on new versions of that file.

## 1. `data/ai_register.csv`

One row = one AI system at one public authority (a *deployment*). 902 rows, 452 AI systems, 893 unique
system × authority combinations (a few combinations appear more than once; the code counts each combination once).

| Column | Meaning | Values |
|---|---|---|
| `AI project` | Name of the AI system | text |
| `Vendor` | Developer of the system. In-house development is coded with the authority itself as developer. A cell may name several developers, separated by commas. | text |
| `Vendor=konsulent?` | Consultancy involved alongside the developer, where known | text |
| `Internal/external/unknown` | Whether the system was built by the deploying authority itself (*Internal*) or by another organisation (*External*) | Internal, External, Unknown, blank |
| `Public/private` | Whether the developer is a public body or a private company | Public, Private, Unknown, blank |
| `1 = speciale, 2 = nye` | Data collection round in which the system was registered | 1, 2, 3 |
| `Offentlig myndighed` | Deploying public authority (Danish name) | text |
| `Område` | Sector | Health, Case processing, Employment, Social work, Education, Transportation, Nature and environment, Construction (also *Byggeri*), Culture, Police, Immigration and asylum, Other, Ukendt (unknown) |
| `Hovedfunktion` | Main function(s), comma-separated | e.g. Beslutningsstøttende værktøj (decision support), Sagsbehandling (case processing), Anbefaling (recommendation), Ukendt |
| `Status` | Status at the authority | I brug (in use), Planlægges taget i brug (planned), Lukket (closed), blank |
| `Udbredelse` | Level of deployment | Kommunalt, Regionalt, Danmark, EU, Internationalt (combinations possible) |
| `Signaturprojekt` | Part of the national signature projects programme | Ja, Nej, blank |
| `LLM` | Uses a large language model | Ja, Nej, blank (mostly blank, see LIMITATIONS) |
| `Risikokategori` | Risk category as stated in an external source | Høj risiko, Lav risiko, Minimal risiko, blank (see LIMITATIONS) |
| `Infrastruktur / Cloud` | Infrastructure as stated in the original register | text |
| `CSP IaaS`, `CSP PaaS`, `CSP SaaS` | Cloud service provider(s) used by this deployment, per cloud service model; several separated by commas; named by company (Microsoft, Amazon, Google) | text |
| `CSP` | Hosting without an external cloud provider, or other hosting | Vendor hosted (No external CSP), On-premises, or a named public body (e.g. Regional IT Syddanmark) |
| `Hosting or CSP found` | Whether a cloud provider or hosting arrangement was identified | yes, no, blank (closed systems) |
| `CSP source` | How the cloud information was obtained | Contact with public authority, Contact with vendor, Web search, blank |
| `CSP source (link)` | Public source, where available | URL or text |

Cloud service models follow the standard definitions: Infrastructure as a Service (IaaS), Platform as a Service
(PaaS) and Software as a Service (SaaS). Vendors' informal descriptions were coded into these models by the authors.

## 2. `data/vendor_cloud.csv`

One row = one developer × cloud provider × cloud service model, at developer level (not tied to a specific
deployment unless `AI system` is filled in).

| Column | Meaning |
|---|---|
| `Vendor` | Developer |
| `AI system` | AI system the information refers to, where specific |
| `CSP` | Cloud service provider(s), comma-separated |
| `CSM` | Cloud service model: IaaS, PaaS, SaaS, Non specified |
| `Cloud service source` | Type of source, e.g. Vendor website, sub-processors list, data processing agreement, Vendor contact, Public authority contact |
| `CSM confidence` | How directly the source states the cloud service model: Explicit, Inferred, Ambiguous |
| `Cloud service description` | Short description of the service |
| `Link` | Source URL |
| `Notes` | Coders' notes: why a provider does or does not apply, that nothing could be found ("Kan pt ikke finde noget"), or that a vendor was set aside ("Sparket til side pga. scope og størrelse") |

**Rows left out of the analysis** (kept in the file, removed in `code/common.py`, and listed when the code runs):
rows whose note begins "Gælder ikke" (the cloud information does not apply to the AI system, e.g. Human Bytes'
general use of AWS, Azure and Google, where AI Mammo is hosted on-premises), and CSP entries that are AI products a
vendor distributes rather than cloud providers (Human Bytes: Combinostics, Eyenuk, Harrison.ai, Milvue, Screenpoint
Medical, Therapanacea).

## 3. Coding rules applied in the code

1. **Several developers in one cell are several developers.** Cells are split on commas and semicolons; legal
   suffixes stay with the company (*Groove X, Inc.* is one developer).
2. **Developer type** (derived datasets): *Public sector* when the developer is a public authority or other public
   body, otherwise *Private company*. Alexandra Instituttet and SAS Institute count as private; IT University of
   Copenhagen and GeoDanmark as public.
3. **Per system**, codings across rows are combined: *Public/private* is Private if any row is Private, else Public,
   else Unknown; *Status* is I brug if any row is in use, else Planlægges, else Lukket if every row is closed;
   *Internal* if any row is Internal.
4. **In use or planned** (the 364 systems): every row with Status = Lukket is removed. Systems closed at all
   authorities drop out; systems still in use elsewhere keep their other rows.
5. **Cloud providers are named by company** (Microsoft rather than Azure). Text in brackets is dropped.
6. **A Big Three developer hosting its own system** (e.g. Microsoft 365 Copilot coded as vendor-hosted) counts as a
   dependency on that provider (Microsoft). A non-Big-Three developer hosting its own system is shown as
   *Vendor-hosted (no external CSP)*.
7. **Deployments** (Figure 4): one deployment = one authority using one AI system, split equally over that
   deployment's own developer × cloud links, so flows are conserved.
8. **Spelling and translation**: all corrections are listed in `data/name_harmonisation.csv`.

## 4. Derived datasets (`data/derived/`)

Built by `code/build_datasets.py`; `_all` uses all rows, `_active` excludes closed rows. The Excel versions include a
README sheet with counts as formulas.

- `ai_systems_*.csv`: one row per AI system with developer(s), developer type, private company developer known,
  combined codings (rule 3), data collection round, status, number and list of authorities, cloud providers per model,
  hosting, *CSP known* (= `Hosting or CSP found` is yes on at least one row), LLM, signature project, risk category.
- `developers_*.csv`: one row per developer with type, number of systems and authorities, systems by developer
  type, sectors, cloud providers via its systems, and cloud providers listed in `vendor_cloud.csv`.
- `cloud_providers_*.csv`: one row per cloud provider or hosting form with type (commercial, public-sector
  infrastructure, no external provider), Big Three flag, and number of systems per cloud service model, developers
  and authorities.
- `system_cloud_links_*.csv`: one row per AI system × cloud provider × model, with number of authorities.

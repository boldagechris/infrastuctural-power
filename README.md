# Infrastructural power: AI systems, developers and cloud dependencies in the Danish public sector

Data, code and figures for the article *[TITLE OF ARTICLE]* ([AUTHORS], [YEAR]).

The article presents an explorative analysis of the infrastructural dependencies that shape the implementation of
artificial intelligence (AI) systems across the Danish public sector. It builds on a mapping of AI systems in the
Danish public sector, the market actors procured to supply them, and the external cloud infrastructures used to
develop and run them. This repository contains the coded data behind that mapping, the code that produces every
figure in the article, and a small web app that redraws the figures from an updated dataset.

> **Data snapshot:** 23 November 2026. The underlying register keeps changing; the figures in the article are built
> from this version.

## Contents

| Path | What it is |
|---|---|
| `data/ai_register.csv` | The register: one row per AI system × public authority (902 rows, 452 AI systems). Input to all figures. |
| `data/vendor_cloud.csv` | Cloud providers per developer (vendor) as found in vendors' sub-processor lists, data processing agreements, websites and by contact (210 rows). |
| `data/name_harmonisation.csv` | Every spelling correction and translation applied in the code (93 mappings). |
| `data/derived/` | Derived datasets built by the code, for all systems (`_all`) and for systems in use or planned (`_active`): AI systems, developers, cloud providers and system–cloud links (CSV and Excel). |
| `code/` | Python scripts: one per figure, a dataset builder, shared helpers, and `export_from_excel.py` to recreate the input CSVs from the project's working Excel file. |
| `figures/` | All figures (PNG, and SVG where useful), network files for Gephi (GEXF) and the edge/link tables behind each figure. |
| `index.html` | Web app (also on GitHub Pages) that redraws Figures 1–4 from an uploaded Excel file in the browser. |
| `CODEBOOK.md` | Variables, values and coding rules. |
| `LIMITATIONS.md` | What the data can and cannot show. Please read before reusing the data. |

## Figures

| Figure | Script | Universe |
|---|---|---|
| 1. AI systems by sector and developer | `figure1_public_private_en.py` | 364 AI systems in use or planned |
| 2. Public authorities and private developers | `figure2_en.py` | 182 privately developed systems in use or planned |
| 3. Private developers and cloud providers (network, matrix, Sankey) | `figure3_en.py` | developers in Figure 2 with cloud data in `vendor_cloud.csv` |
| 4. AI system → developer → authority → cloud (Sankey) | `figure4_364_all_sankey_en.py` | 108 systems with an identified cloud provider or hosting arrangement (295 deployments) |
| 4b. The stack with its holes: where knowledge of each system stops | `figure4_gaps_en.py` | all 364 AI systems in use or planned |
| M. Research funnel | `figure_visibility_en.py` | full register |
| F. Visibility of the infrastructure layer by developer type | `figure_visibility_en.py` | 364 AI systems in use or planned |
| A, C. Missing information (by variable, by sector) | `figure_missing_en.py` | 364 AI systems in use or planned |

## How to reproduce

```bash
pip install -r requirements.txt
bash run_all.sh
```

This rebuilds `data/derived/` and `figures/` from the two CSV files in `data/`. Network layouts use fixed seeds, so
repeated runs give the same figures.

To update with a new version of the working Excel file (sheets *AI project* and *Vendor*):

```bash
python code/export_from_excel.py path/to/dataset.xlsx
bash run_all.sh
```

## Data sources

The register of AI systems builds on and contributes to the Danish open-access database
[Offentlig-AI.dk](https://offentlig-ai.dk) (Küçüksu & Godzimirska, 2026). Some systems were added from the
Nordic AI Health Map (New Nordics AI) and KL's AI-landkort. Developer and cloud information was collected by the
authors through sources used by the database, web searches, vendors' sub-processor lists, data processing
agreements and terms of use, procurement documents (udbud.dk), and direct contact with vendors and public
authorities.

**Left out for privacy and rights reasons:** free-text descriptions and source notes from the working file
(columns *Kort beskrivelse*, *Kilder*, the questions I–VIII and *Menneskeretlige overvejelser*). They contain
names, e-mail addresses and phone numbers of public employees, and text copied from the sources above. System
descriptions can be found at Offentlig-AI.dk. Correspondence with vendors and authorities is not published.

## Licence

- Code: MIT (see `LICENSE`).
- Data and figures: CC BY 4.0 (see `LICENSE-DATA`). [CHECK: confirm that the licence of Offentlig-AI.dk allows
  redistribution of the register fields under CC BY 4.0.]

## How to cite

See `CITATION.cff`. A DOI is issued by Zenodo for each GitHub release.

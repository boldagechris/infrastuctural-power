#!/usr/bin/env bash
# Rebuild all derived datasets and figures from the data in ./data.
#   bash run_all.sh
# Requires Python 3.10+ and the packages in requirements.txt.
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"
mkdir -p data/derived figures

echo "== Derived datasets"
python code/build_datasets.py data/derived/ai_datasets_all.xlsx
python code/build_datasets.py data/derived/ai_datasets_active.xlsx --exclude-closed
python - <<'PY'
import pandas as pd
for tag in ('all', 'active'):
    x = pd.ExcelFile(f'data/derived/ai_datasets_{tag}.xlsx')
    for sh, name in [('AI systems', 'ai_systems'), ('Vendors', 'developers'), ('CSP', 'cloud_providers'), ('System-CSP links', 'system_cloud_links')]:
        pd.read_excel(x, sh).to_csv(f'data/derived/{name}_{tag}.csv', index=False, encoding='utf-8')
PY

cd figures
echo "== Figure 1: AI systems by sector and developer"
python "$ROOT/code/figure1_public_private_en.py" > /dev/null
echo "== Figure 2: authority-developer network"
python "$ROOT/code/figure2_en.py" > /dev/null
python "$ROOT/code/gexf_to_english.py" figure2_network.gexf figure2_network_en.gexf
echo "== Figure 3: developer-cloud network, matrix and Sankey"
python "$ROOT/code/figure3_en.py"
echo "== Figure 4: Sankey AI system -> developer -> authority -> cloud"
python "$ROOT/code/figure4_364_all_sankey_en.py" | head -1
echo "== Figures M and F: research funnel and visibility"
python "$ROOT/code/figure_visibility_en.py" > /dev/null
echo "== Figures A and C: missing information"
python "$ROOT/code/figure_missing_en.py" > /dev/null
echo "Done. Outputs in ./figures and ./data/derived"

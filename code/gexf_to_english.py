"""Make an English version of figure2_network.gexf: authority names translated, Danish name kept
as attribute 'name_da'. Usage: python gexf_to_english.py figure2_network.gexf figure2_network_en.gexf"""
import sys
import networkx as nx

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from names_en import AUTH, VENDOR, en


src, dst = sys.argv[1], sys.argv[2]
G = nx.read_gexf(src)
H = nx.Graph()
missing = []
for n, d in G.nodes(data=True):
    d = dict(d)
    if d.get('node_type') == 'authority':
        new = en(n)
        if new == n and not n.endswith(' Kommune') and n not in AUTH: missing.append(n)
        d['name_da'] = n
    else:
        new = VENDOR.get(n, n)
        d['name_da'] = n
    d['label'] = new
    H.add_node(new, **d)
for u, v, d in G.edges(data=True):
    d = {k: val for k, val in d.items() if k != 'id'}
    f = lambda x: en(x) if G.nodes[x].get('node_type') == 'authority' else VENDOR.get(x, x)
    H.add_edge(f(u), f(v), **d)
nx.write_gexf(H, dst)
print(H.number_of_nodes(), H.number_of_edges(), 'untranslated:', missing)

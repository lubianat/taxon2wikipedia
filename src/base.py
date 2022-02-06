from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd 
from jinja2 import Template
import sys
import requests


template_path = "data/full_query_taxon.rq.jinja"
taxon_qid = sys.argv[1]

with open(template_path) as f:
    t = Template(f.read())

query = t.render(taxon=taxon_qid)

print(query)
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()



results_df = pd.io.json.json_normalize(results['results']['bindings'])
print(results_df)


taxon_rank_label = results_df["taxon_rankLabel.value"][0]
parent_taxon_label = results_df["parent_taxonLabel.value"][0]
parent_taxon = results_df["parent_taxon.value"][0]
taxon_name = results_df["taxon_name.value"][0]

print(f"""

''''{taxon_name} ''''' is a species of the group [[{parent_taxon_label}]].







""")
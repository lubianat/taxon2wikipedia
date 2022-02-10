from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd 
from jinja2 import Template
import sys
import requests
from qid2taxobox import *

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
print(results_df.columns)


taxon_rank_label = results_df["taxon_rankLabel.value"][0]
parent_taxon_label = results_df["parent_taxonLabel.value"][0]
parent_taxon = results_df["parent_taxon.value"][0]
taxon_name = results_df["taxon_name.value"][0]
try:
    taxon_author_label = results_df["taxon_authorLabel.value"][0]
    description_year = results_df["description_year.value"][0]
except:
    taxon_author_label = "TEMPORARY REPLACEMENT"
    description_year = "TEMPORARY REPLACEMENT"

try:
    common_name = results_df["taxon_common_name_pt.value"][0]
except:
    common_name = "TEMPORARY REPLACEMENT"

taxobox =  get_taxobox(taxon_qid)


print(f"""
{taxobox}
'''''{taxon_name}''''', também conhecido como '''{common_name}''', é uma espécie do grupo [[{parent_taxon_label}]] decrita em [[{description_year}]] por [[{taxon_author_label}]].


{{{{Referencias}}}}
{{{{Controle de autoridade|colapsar}}}}
{{{{esboço}}}}

""")

print(f"""https://pt.wikipedia.org/wiki/{taxon_name.replace(" ", "_")}?action=edit&veswitched=1""")
print(f"""https://www.google.com/search?q={taxon_name.replace(" ", "_")}""")
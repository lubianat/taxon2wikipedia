#!/usr/bin/env python3
from cgi import test
from .qid2taxobox import *
from .cleanup import *
from pathlib import Path
from .process_reflora import *
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
import requests


disable_warnings(InsecureRequestWarning)

HERE = Path(__file__).parent.resolve()


def render_cnc_flora(taxon_name):
    if test_cnc_flora(taxon_name):
        return f"* [http://cncflora.jbrj.gov.br/portal/pt-br/profile/{quote(taxon_name)} ''{taxon_name}'' no portal do Centro Nacional de Conservação da Flora (Brasil)]"
    else:
        return ""


def test_cnc_flora(name):
    url = f"http://cncflora.jbrj.gov.br/portal/pt-br/profile/{name}"
    response = requests.get(url)
    return "Avaliador" in response.text


# Wikidata-based session rendering
def render_additional_reading(qid):
    """
    Renders an "additional readings" session based on Wikidata main subjects
    """
    query = f"""
    SELECT * WHERE {{ 
        ?article wdt:P921 wd:{qid}  .
    }}
    """
    df = get_rough_df_from_wikidata(query)
    if "?article.value" not in df:
        return ""
    article_ids = list(df["article.value"])

    additional_reading = """== Leitura adicional =="""
    for id in article_ids:
        additional_reading += f"""
      * {{{{ Citar Q | {qid} }}}}"""
    return additional_reading


def get_gbif_ref(qid):
    "Renders the GBIF reference for this QID."
    query = f"""
    SELECT * WHERE {{ 
        wd:{qid} wdt:P846 ?gbif_id .
        wd:{qid} wdt:P225 ?taxon_name . }}
    """
    df = get_rough_df_from_wikidata(query)
    if "gbif_id.value" not in df:
        return ""
    gbif_id = list(df["gbif_id.value"])[0]
    taxon_name = list(df["taxon_name.value"])[0]
    ref = f"""<ref>{{{{Citar web|url=https://www.gbif.org/species/{gbif_id}|titulo={taxon_name}|acessodata=2022-04-18|website=www.gbif.org|lingua=en}}}}</ref>"""
    return ref


def render_taxonomy(reflora_data, results_df, qid):
    """
    Renders the taxonomy session  for the taxon.
    """

    if "taxon_authorLabel.value" not in results_df:
        description = ""
    else:
        taxon_author_labels = results_df["taxon_authorLabel.value"].values
        description_year = results_df["description_year.value"][0]

        taxon_author_labels = [f"[[{name}]]" for name in taxon_author_labels]
        description = f"A espécie foi descrita em [[{description_year}]] por {render_list_without_dict(taxon_author_labels)}. {get_gbif_ref(qid)}"

    text = f"""
== Taxonomia ==
{description}
{get_subspecies_from_reflora(reflora_data)}
{get_synonyms_from_reflora(reflora_data)}"""

    return text


# Mixed Wikida and Reflora
def render_common_name(results_df, reflora_data):
    """
    Renders the common name for the taxon using either Wikidata (if available)
    or data from Reflora
    """

    try:
        common_names = results_df["taxon_common_name_pt.value"]
    except:
        try:
            common_names = get_common_names(reflora_data)
        except:
            return ""

    common_names = [f"'''{a}'''" for a in common_names]

    if len(common_names) == 0:
        return ""
    elif len(common_names) == 1:
        return f""", também conhecido como {common_names[0]},"""
    else:
        common_list = ", ".join(common_names[:-1])
        return f""", também conhecido como {common_list} ou {common_names[-1]},"""

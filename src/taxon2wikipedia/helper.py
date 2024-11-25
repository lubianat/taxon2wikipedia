#!/usr/bin/env python3
import os
import webbrowser
from cgi import test
from pathlib import Path
from urllib.parse import quote
import re
import collections

import pywikibot
import requests
from jinja2 import Template
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from wdcuration import render_qs_url, search_wikidata

from wikidata2df import wikidata2df

disable_warnings(InsecureRequestWarning)

import click
import pandas as pd
from SPARQLWrapper import JSON, SPARQLWrapper

def check_if_is_basionym(qid):
    # P12766 
    query = f"""
    SELECT * WHERE {{
        wd:{qid} wdt:P12766 ?current_name .
    }}  
    """
    df = get_rough_df_from_wikidata(query)
    if "current_name.value" not in df:
        return False
    #return current name qid
    return df["current_name.value"][0].split("/")[-1]

def check_if_has_basionym(qid):
    # P566 
    query = f"""
    SELECT * WHERE {{
        wd:{qid} wdt:P566 ?basionym .
    }}  
    """
    df = get_rough_df_from_wikidata(query)
    if "basionym.value" not in df:
        return False
    #return current name qid
    return df["basionym.value"][0].split("/")[-1]


def merge_equal_refs(wikipage):
    results = re.findall(f"(<ref>.*?</ref>)", wikipage)
    repeated_refs = [item for item, count in collections.Counter(results).items() if count > 1]

    for i, repeated_ref in enumerate(repeated_refs):
        parts = wikipage.partition(repeated_ref)  # returns a tuple
        print("========")
        wikipage = (
            parts[0]
            + re.sub(
                re.escape(repeated_ref),
                f'<ref name=":ref_{str(i)}"> {repeated_ref.replace("<ref>", "")}',
                parts[1],
            )
            + re.sub(
                re.escape(repeated_ref),
                f'<ref name=":ref_{str(i)}"/>',
                parts[2],
            )
        )
    return wikipage

def render_list_without_dict(list_of_names):
    text = ""
    for i, name in enumerate(list_of_names):
        if i == 0:
            text = text + name
        elif i == len(list_of_names) - 1:
            text = text + " e " + name
        else:
            text = text + ", " + name
    return text


def render_list(list_of_ids, dict_of_wikitexts):
    text = ""
    for i, entry in enumerate(list_of_ids):
        if i == 0:
            text = text + dict_of_wikitexts[entry]
        elif i == len(list_of_ids) - 1:
            text = text + " e " + dict_of_wikitexts[entry]
        else:
            text = text + ", " + dict_of_wikitexts[entry]
    return text


def get_parent_taxon_df(qid):
    query = (
        """
    SELECT 
    ?taxonRankLabel
    ?taxonName
    ?taxon_range_map_image
    WHERE 
    {
    VALUES ?taxon {   wd:"""
        + qid
        + """} .
    ?taxon wdt:P171* ?parentTaxon.
    ?parentTaxon wdt:P105 ?taxonRank.
    ?parentTaxon wdt:P225 ?taxonName.
    SERVICE wikibase:label { bd:serviceParam wikibase:language "pt". }
    OPTIONAL { ?taxon wdt:P181 ?taxon_range_map_image } . 

    }"""
    )
    results_df = get_rough_df_from_wikidata(query)

    return results_df


def get_rough_df_from_wikidata(query):
    sparql = SPARQLWrapper(
        "https://query.wikidata.org/sparql",
        agent="taxon2wikipedia (https://github.com/lubianat/taxon2wikipedia)",
    )

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    results_df = pd.json_normalize(results["results"]["bindings"])
    return results_df


def get_taxobox_from_df(parent_taxon_df):
    # Define problematic taxa that conflict with "Aves"
    excluded_taxa_for_aves = {
        "Dinosauria", "Reptilia", "Saurischia", "Theropoda", 
        "Maniraptora", "Maniraptoriformes", "Tetanurae", 
        "Coelurosauria", "Neocoelurosauria", "Osteichthyes", "Elpistostegalia"
    }

    result = "{{Info/Taxonomia\n"
    result += "| imagem                = \n"

    for i, row in parent_taxon_df.iterrows():
        rank = row["taxonRankLabel.value"]
        name = row["taxonName.value"]

        # Exclude problematic taxa when "Aves" is present in the lineage
        if "Aves" in parent_taxon_df["taxonName.value"].values and name in excluded_taxa_for_aves:
            continue

        # Skip problematic ranks
        if rank in ["super-reino", "subdivisão"]:
            continue

        # Align field formatting
        n_space = 22 - len(rank)
        multiple_spaces = " " * max(n_space, 1)  # Ensure at least 1 space

        to_append = f"| {rank}{multiple_spaces}= [[{name}]]    \n"
        result += to_append

    # Add map image if available
    try:
        map_image = parent_taxon_df["taxon_range_map_image.value"].iloc[0]
        map_file = map_image.split("/")[-1].replace("%20", " ")
        result += f"| mapa = {map_file}\n"
    except (KeyError, IndexError):
        # Map field not available
        pass

    # Finalize the template
    result += "}}"

    return result


def get_taxobox(qid):
    df = get_parent_taxon_df(qid)
    a = get_taxobox_from_df(df)
    return a


@click.command(name="taxobox")
@click.option("--qid")
@click.option("--taxon", is_flag=True, help="Ask for a taxon name.")
@click.option("--taxon_name", help="Provide a taxon name directly (and quoted)")
def print_taxobox(qid: str, taxon: str, taxon_name: str):

    if taxon or taxon_name:
        qid = get_qid_from_name(taxon_name)
    taxobox = get_taxobox(qid)
    print(taxobox)


HERE = Path(__file__).parent.resolve()


def test_invasive_species(taxon_id):
    query = "SELECT ?item WHERE {" f"wd:{taxon_id} wdt:P5626 ?item" "}"
    df = wikidata2df(query)

    if (len(df)) == 0:
        return False
    else:
        return df["item"][0]


def render_reflora_link(taxon_name, qid):
    reflora_id = get_reflora_id(qid)
    if reflora_id == "" or reflora_id is None:
        return ""

    return f"* [http://reflora.jbrj.gov.br/reflora/listaBrasil/FichaPublicaTaxonUC/FichaPublicaTaxonUC.do?id={reflora_id} ''{taxon_name}'' no projeto Flora e Funga do Brasil]"


def get_results_dataframe_from_wikidata(qid):
    template_path = Path(f"{HERE}/data/full_query_taxon.rq.jinja")
    t = Template(template_path.read_text())
    query = t.render(taxon=qid)
    results_df = get_rough_df_from_wikidata(query)
    return results_df


def get_qid_from_name(taxon_name):
    if not taxon_name:
        taxon_name = input("Nome científico do taxon:")
    taxon_result = search_wikidata(taxon_name)
    taxon_ok = input(
        f'Wikidata found {taxon_result["label"]} ({taxon_result["description"]}). Is it correct (y/n)?'
    )
    if taxon_ok == "y":
        qid = taxon_result["id"]
    else:
        create_ok = input("Do you want to create the taxon? (y/n)")
        if create_ok == "y":
            os.system(f"taxon2wikipedia create --taxon_name '{taxon_name}'")
        print("quitting...")
        quit()
    return qid


def render_cnc_flora(taxon_name):
    if test_cnc_flora(taxon_name):
        return f"* [http://cncflora.jbrj.gov.br/portal/pt-br/profile/{quote(taxon_name)} ''{taxon_name}'' no portal do Centro Nacional de Conservação da Flora (Brasil)]"
    else:
        return ""
    
def render_bhl(taxon_name):
    if test_bhl(taxon_name):
        return f"* [https://www.biodiversitylibrary.org/name/{quote(taxon_name)} Documentos sobre ''{taxon_name}'' na Biodiversity Heritage Library]"
    else:
        return ""

def render_gbif(taxon_name, qid):
    gbif_id = get_gbif_id(qid)
    if get_gbif_id(qid):
        return f"* [https://www.gbif.org/species/{gbif_id} ''{taxon_name}'' no GBIF]"
    else:
        return ""

def get_gbif_id(qid):
    query = f"""
    SELECT * WHERE {{ 
        wd:{qid} wdt:P846 ?gbif_id .
    }}
    """
    df = get_rough_df_from_wikidata(query)
    if "gbif_id.value" not in df:
        return ""
    gbif_id = list(df["gbif_id.value"])[0]
    return gbif_id

def render_inaturalist(taxon_name, qid):
    inat_id = get_inaturalist_id(qid)
    if get_inaturalist_id(qid):
        return f"* [https://www.inaturalist.org/taxa/{inat_id} Observações de ''{taxon_name}'' no iNaturalist]"
    else:
        return ""

def get_reflora_id(qid):
    query = f"""
    SELECT * WHERE {{ 
        wd:{qid} wdt:P10701 ?reflora_id .
    }}
    """
    df = get_rough_df_from_wikidata(query)
    if "reflora_id.value" not in df:
        return ""
    reflora_id = list(df["reflora_id.value"])[0]
    return reflora_id


def get_inaturalist_id(qid):
    query = f"""
    SELECT * WHERE {{ 
        wd:{qid} wdt:P3151 ?inaturalist_id .
    }}
    """
    df = get_rough_df_from_wikidata(query)
    if "inaturalist_id.value" not in df:
        return ""
    inaturalist_id = list(df["inaturalist_id.value"])[0]
    return inaturalist_id

def test_bhl(name):
    return True #PLACEHOLDER FOR A TEST FOR PRESENCE OF TAXON IN BHL 

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


def render_taxonomy(results_df, qid):
    """
    Renders the taxonomy session  for the taxon.
    """
    if "taxon_authorLabel.value" not in results_df:
        description = ""
    else:
        taxon_author_labels = results_df["taxon_authorLabel.value"].values
        description_year = results_df["description_year.value"][0]

        taxon_author_labels = [f"[[{name}]]" for name in taxon_author_labels]
        description = f"O táxon foi descrito oficialmente em [[{description_year}]] por {render_list_without_dict(taxon_author_labels)}. {get_gbif_ref(qid)}"

    text = f"""
{description}
"""
    qid_for_basionym = check_if_has_basionym(qid)
    print(qid_for_basionym) 
    if qid_for_basionym:
        basionym_results_df = get_results_dataframe_from_wikidata(qid_for_basionym)
        basionym_author_labels = basionym_results_df["taxon_authorLabel.value"].values
        basionym_year = basionym_results_df["description_year.value"][0]
        basionym_author_labels = [f"[[{name}]]" for name in basionym_author_labels]
        text += f"""
        
A espécie havia sido descrita anteriormente sob o [[basiônimo]] '''''{basionym_results_df["taxon_name.value"][0]}''''' (gênero ''[[{basionym_results_df["parent_taxonLabel.value"][0]}]]'') em {basionym_year} por {render_list_without_dict(basionym_author_labels)}. {get_gbif_ref(qid_for_basionym)}
"""

    if text.isspace():
        return ""
    else:
        text = f"""
== Taxonomia ==
{text}
"""
        return text


# Mixed Wikida and Reflora
def render_common_name(results_df):
    """
    Renders the common name for the taxon using Wikidata
    """

    try:
        common_names = results_df["taxon_common_name_pt.value"]
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

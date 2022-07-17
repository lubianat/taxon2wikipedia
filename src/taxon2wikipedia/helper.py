#!/usr/bin/env python3

from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
from jinja2 import Template
import sys
from .qid2taxobox import *
from .cleanup import *
import pywikibot
from pathlib import Path
from .process_reflora import *
import click
import webbrowser
from wdcuration import render_qs_url
from pywikibot.page import Page
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

disable_warnings(InsecureRequestWarning)

HERE = Path(__file__).parent.resolve()


def render_additional_reading(qid):
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

    if "taxon_authorLabel.value" not in results_df:
        description = ""
    else:
        taxon_author_labels = results_df["taxon_authorLabel.value"].values
        description_year = results_df["description_year.value"][0]

        taxon_author_labels = [f"[[{name}]]" for name in taxon_author_labels]
        description = f"A espécie foi descrita em [[{description_year}]] por {render_list_without_dict(taxon_author_labels)}. {get_gbif_ref(qid)}"

    text = f"""== Taxonomia ==
{description}
{get_subspecies_from_reflora(reflora_data)}
{get_synonyms_from_reflora(reflora_data)}"""

    return text


def render_common_name(results_df, reflora_data):

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

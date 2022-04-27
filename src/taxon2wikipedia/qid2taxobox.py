from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
from jinja2 import Template
import sys
import requests


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
    results_df = pd.io.json.json_normalize(results["results"]["bindings"])
    return results_df


def get_taxobox_from_df(parent_taxon_df):

    result = "{{Info/Taxonomia\n"
    to_append = "| imagem                = \n"

    result = result + to_append

    for i, row in parent_taxon_df.iterrows():
        rank = row["taxonRankLabel.value"]
        name = row["taxonName.value"]

        # super-reino and subdivisão leads to issues in pt-wiki
        if rank == "super-reino" or rank == "subdivisão":
            continue

        n_space = 22 - len(rank)
        multiple_spaces = " " * n_space

        to_append = f"| {rank} {multiple_spaces}= [[{name}]]    \n"

        result = result + to_append

    try:
        map = (
            parent_taxon_df["taxon_range_map_image.value"][0]
            .split("/")[-1]
            .replace("%20", " ")
        )
        to_append = f"| mapa = { map}\n"
        result = result + to_append
    except:
        pass

    to_append = "}}"
    result = result + to_append

    return result


def get_taxobox(qid):
    df = get_parent_taxon_df(qid)
    a = get_taxobox_from_df(df)
    return a

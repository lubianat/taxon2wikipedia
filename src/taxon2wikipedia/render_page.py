#!/usr/bin/env python3
import click
import webbrowser
import json
import re
import requests
import sys

import pywikibot
from wdcuration import render_qs_url
from taxon2wikipedia.helper import *

def get_class_name(parent_taxon_df):
    try:
        class_name = parent_taxon_df["taxonName.value"][
            parent_taxon_df["taxonRankLabel.value"] == "classe"
        ].item()
    except ValueError as e:
        print(e)
        if "Aves" in parent_taxon_df["taxonName.value"].values:
            class_name = "Aves"
        else:
            class_name=""
    return class_name

def get_kingdom_name(parent_taxon_df):
    genus_name = parent_taxon_df["taxonName.value"][
        parent_taxon_df["taxonRankLabel.value"] == "reino"
    ].item()
    return genus_name

# Functions
def get_family_name(parent_taxon_df):
    family_name = parent_taxon_df["taxonName.value"][
        parent_taxon_df["taxonRankLabel.value"] == "família"
    ].item()
    return family_name


def get_genus_name(parent_taxon_df):
    genus_name = parent_taxon_df["taxonName.value"][
        parent_taxon_df["taxonRankLabel.value"] == "género"
    ].item()
    return genus_name


def get_year_category(results_df):
    if "description_year.value" not in results_df:
        year_cat = ""
    else:
        description_year = results_df["description_year.value"][0]
        year_cat = f"[[Categoria:Espécies descritas em {description_year}]]"
    return year_cat


def get_pt_wikipage_from_qid(qid):
    invasive_count = test_invasive_species(qid)

    if invasive_count:
        print(invasive_count)
    results_df = get_results_dataframe_from_wikidata(qid)

    parent_taxon_df = get_parent_taxon_df(qid)
    kingdom_name   = get_kingdom_name(parent_taxon_df)
    family_name = get_family_name(parent_taxon_df)
    class_name = get_class_name(parent_taxon_df)
    genus_name = get_genus_name(parent_taxon_df)
    taxon_name = results_df["taxon_name.value"][0]

    year_category = get_year_category(results_df)

    wiki_page = get_wiki_page(
        qid,
        taxon_name,
        results_df,
        kingdom_name,
        class_name,
        family_name,
        genus_name,
        year_category,
    )

    return wiki_page


def render_external_links(taxon_name, qid, bird_links):
    text = f"""
== Ligações externas ==
{render_reflora_link(taxon_name, qid)}
{render_cnc_flora(taxon_name)}
{render_bhl(taxon_name)}
{render_inaturalist(taxon_name, qid)}
{render_gbif(taxon_name, qid)}
{bird_links}
  """
    basionym_qid = check_if_has_basionym(qid)
    if basionym_qid:
        basionym_name = get_results_dataframe_from_wikidata(basionym_qid)["taxon_name.value"][0]
        text += f"""
=== Ligações externas para sinônimos ===
{render_reflora_link(basionym_name, basionym_qid)}
{render_bhl(basionym_name)}
{render_inaturalist(basionym_name, basionym_qid)}
{render_gbif(basionym_name, basionym_qid)}
"""
        

    return text

from SPARQLWrapper import SPARQLWrapper, JSON


def get_bird_identifiers(qid):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

    query = """
    SELECT ?wiki_aves_bird_id ?ebird_taxon_id ?xeno_canto_species_id ?bird_label WHERE {
      wd:%s wdt:P4664 ?wiki_aves_bird_id.
      wd:%s wdt:P3444 ?ebird_taxon_id.
      wd:%s wdt:P2426 ?xeno_canto_species_id.
      OPTIONAL {
        wd:%s rdfs:label ?bird_label.
        FILTER (lang(?bird_label) = "pt").
      }
    }
    """ % (
        qid,
        qid,
        qid,
        qid,
    )   

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results["results"]["bindings"]


def get_bird_links(qid):
    results = get_bird_identifiers(qid)

    if len(results) > 0:
        res = results[0]
        wiki_aves_bird_id = res.get("wiki_aves_bird_id", {}).get("value")
        ebird_taxon_id = res.get("ebird_taxon_id", {}).get("value")
        xeno_canto_species_id = res.get("xeno_canto_species_id", {}).get("value")
        bird_label = res.get("bird_label", {}).get("value", "essa ave")
        bird_label = bird_label.lower()
        wikipedia_bird_links = f"""
* [https://www.wikiaves.com.br/wiki/{wiki_aves_bird_id} Página do Wikiaves sobre a  {bird_label}]
* [https://ebird.org/species/{ebird_taxon_id} Informações do eBird sobre a {bird_label}]
* [https://www.xeno-canto.org/species/{xeno_canto_species_id} Vocalizações de {bird_label} no Xeno-canto]"""

        return wikipedia_bird_links
    else:
        return ""



def get_wiki_page(qid, taxon_name, results_df,kingdom,class_name, family, genus, year_cat):
        taxobox = get_taxobox(qid)

        if family is None:
            family_sentence = ""
        else:
            family_sentence = f" da família [[{family}]] e"

        if class_name == "Aves":
            bird_links = get_bird_links(qid)
        else:
            bird_links = ""

        if kingdom == "Plantae":
            kingdom_text = "de planta"
        else:
            kingdom_text = ""

        wiki_page = f"""
{{{{Título em itálico}}}}
{taxobox}
'''''{taxon_name}''''' é uma espécie {kingdom_text}{family_sentence} do gênero ''[[{genus}]]''.  {get_gbif_ref(qid)}
{render_taxonomy(results_df, qid)}
{{{{Referencias}}}}
{render_external_links(taxon_name,qid,bird_links)}
{render_additional_reading(qid)}
{{{{Controle de autoridade}}}}
{{{{esboço-biologia}}}}
[[Categoria:{genus}]]{year_cat}"""

        categories = []

        for cat in categories:
            wiki_page += f"""[[Categoria:{cat}]]
"""
        print("===== Saving wikipage =====")
        wiki_page = merge_equal_refs(wiki_page)
        wiki_page = wiki_page.replace("\n\n", "\n")
        wiki_page = re.sub("^ ", "", wiki_page, flags=re.M)
        return wiki_page

    

def italicize_taxon_name(taxon_name, wiki_page):
    """ Turns taxon names into italic
    Args:
      taxon_name (str):  The target taxon name. \
      wiki_page(str): The wiki page string to modify.
    """
    wiki_page = re.sub(
        f"([^a-zA-ZÀ-ÿ'\[]]+){taxon_name}([^a-zA-ZÀ-ÿ']+)", f"\\1''{taxon_name}''\\2", wiki_page
    )

    return wiki_page


def open_related_urls(taxon_name):
    webbrowser.open(
        f"""https://scholar.google.com/scholar?q=%22{taxon_name.replace(" ", "+")}%22+scielo"""
    )
    webbrowser.open(f"""https://google.com/search?q=%22{taxon_name.replace(" ", "+")}%22""")


def create_wikipedia_page(taxon_name, wiki_page):
    print("===== Creating Wikipedia page =====")
    site = pywikibot.Site("pt", "wikipedia")
    newPage = pywikibot.Page(site, taxon_name)
    newPage.text = wiki_page
    newPage.save("Esboço criado com código de https://github.com/lubianat/taxon2wikipedia")


def set_sitelinks_on_wikidata(qid, taxon_name):
    print("===== Setting sitelinks on Wikidata =====")
    site = pywikibot.Site("wikidata", "wikidata")
    repo = site.data_repository()
    item = pywikibot.ItemPage(repo, qid)
    data = [{"site": "ptwiki", "title": taxon_name.replace(" ", "_")}]

    item.setSitelinks(data)
    return 0

@click.command(name="render")
@click.option("--qid")
@click.option("--taxon", is_flag=True, help="Ask for a taxon name.")
@click.option("--taxon_name", help="Provide a taxon name directly (and quoted)")
@click.option("--open_url", is_flag=True, default=False, help="Abrir ou não as páginas auxiliares")
@click.option("--show", is_flag=True, default=False, help="Print to screen only")
def main(qid: str, taxon: str, taxon_name: str, open_url: bool, show: bool):
    if taxon or taxon_name:
        qid = get_qid_from_name(taxon_name)


    new_qid = check_if_is_basionym(qid)

    if new_qid:
        print("This is a basionym. Do you want to proceed with the accepted name or your input?")
        print("Old QID: ", qid, "(https://www.wikidata.org/wiki/" + qid + ")")
        print("New QID: ", new_qid, "(https://www.wikidata.org/wiki/" + new_qid + ")")
        selection = input("Accepted name (a) or Basionym (b)?")
        if selection == "a":
            qid = new_qid
    
    print(qid)

    results_df = get_results_dataframe_from_wikidata(qid)
    taxon_name = results_df["taxon_name.value"][0]

    if open_url:
        open_related_urls(taxon_name)

    wiki_page = get_pt_wikipage_from_qid(qid)
    if show:
        print(wiki_page)
        quit()
    filepath = "wikipage.txt"

    with open(filepath, "w+") as f:
        f.write(wiki_page)

    print(f"The length of the current page will be {len(wiki_page.encode('utf-8'))}")
    create = input("Create page with pywikibot? (y/n)")
    if create == "y":
        create_wikipedia_page(taxon_name, wiki_page)
    else:
        print("quitting...")
        quit()
    set_sitelinks_on_wikidata(qid, taxon_name)

    webbrowser.open(
        f"""https://pt.wikipedia.org/wiki/{taxon_name.replace(" ", "_")}?veaction=edit"""
    )


if __name__ == "__main__":
    main()

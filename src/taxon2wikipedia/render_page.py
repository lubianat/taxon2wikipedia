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
from SPARQLWrapper import SPARQLWrapper, JSON


# Ensure backward compatibility with taxon2wikipedia <=0.0.14
def get_pt_wikipage_from_qid(qid):
    wiki_page = run_pipeline_for_wikipage(qid, "pt")
    return wiki_page


# -----------------------------------------------------------
# Basic helper functions for taxon names (as before)
# -----------------------------------------------------------
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
            class_name = ""
    return class_name


def get_kingdom_name(parent_taxon_df):
    print(parent_taxon_df)
    kingdom_name = parent_taxon_df["taxonName.value"][
        parent_taxon_df["taxonRank.value"] == "http://www.wikidata.org/entity/Q36732"
    ].item()
    return kingdom_name


def get_family_name(parent_taxon_df):
    family_name = parent_taxon_df["taxonName.value"][
        parent_taxon_df["taxonRank.value"] == "http://www.wikidata.org/entity/Q35409"
    ].item()
    return str(family_name)


def get_genus_name(parent_taxon_df):
    genus_name = parent_taxon_df["taxonName.value"][
        parent_taxon_df["taxonRank.value"] == "http://www.wikidata.org/entity/Q34740"
    ].item()
    return genus_name


def get_year_category(results_df, lang="pt"):
    if "description_year.value" not in results_df:
        return ""
    description_year = results_df["description_year.value"][0]
    cat_labels = {
        "pt": f"[[Categoria:Espécies descritas em {description_year}]]",
        "en": f"[[Category:Species described in {description_year}]]",
        "es": f"[[Categoría:Especies descritas en {description_year}]]",
        "fr": f"[[Catégorie:Espèces décrites en {description_year}]]",
    }
    return cat_labels.get(lang, cat_labels["pt"])


# External links: Biodiversity Heritage Library (BHL)
BHL_LINK = {
    "pt": "Documentos sobre",
    "en": "Documents about",
    "es": "Documentos sobre",
    "fr": "Documents sur",
}
BHL_SUFFIX = {
    "pt": "na Biodiversity Heritage Library",
    "en": "in the Biodiversity Heritage Library",
    "es": "en la Biodiversity Heritage Library",
    "fr": "dans la Biodiversity Heritage Library",
}


def render_bhl(taxon_name, lang="pt"):
    if check_bhl(taxon_name):
        prefix = BHL_LINK.get(lang, BHL_LINK["pt"])
        suffix = BHL_SUFFIX.get(lang, BHL_SUFFIX["pt"])
        return f"* [https://www.biodiversitylibrary.org/name/{quote(taxon_name)} {prefix} ''{taxon_name}'' {suffix}]"
    else:
        return ""


# External links: iNaturalist
INAT_LINK = {
    "pt": "Observações de",
    "en": "Observations of",
    "es": "Observaciones de",
    "fr": "Observations de",
}
INAT_SUFFIX = {
    "pt": "no iNaturalist",
    "en": "in iNaturalist",
    "es": "en iNaturalist",
    "fr": "sur iNaturalist",
}


def render_inaturalist(taxon_name, qid, lang="pt"):
    inat_id = get_inaturalist_id(qid)
    if inat_id:
        prefix = INAT_LINK.get(lang, INAT_LINK["pt"])
        suffix = INAT_SUFFIX.get(lang, INAT_SUFFIX["pt"])
        return f"* [https://www.inaturalist.org/taxa/{inat_id} {prefix} ''{taxon_name}'' {suffix}]"
    else:
        return ""


# -----------------------------------------------------------
# External links renderer (now accepts an external heading and language)
# -----------------------------------------------------------
def render_external_links(taxon_name, qid, bird_links, external_heading, lang="pt"):
    translations = {
        "pt": "=== Links externos para sinônimos ===",
        "en": "=== External links for synonyms ===",
        "es": "=== Enlaces externos para sinónimos ===",
        "fr": "=== Liens externes pour synonymes ===",
    }
    text = f"""
{external_heading}
{render_reflora_link(taxon_name, qid, lang)}
{render_ipni_link(taxon_name, qid, lang)}
{render_cnc_flora(taxon_name, lang)}
{render_bhl(taxon_name, lang)}
{render_inaturalist(taxon_name, qid, lang)}
{render_gbif(taxon_name, qid, lang)}
{bird_links}
    """
    basionym_qid = check_if_has_basionym(qid)
    if basionym_qid:
        basionym_name = get_results_dataframe_from_wikidata(basionym_qid)["taxon_name.value"][0]
        text += f"""
{translations.get(lang, translations["en"])}
{render_reflora_link(basionym_name, basionym_qid, lang)}
{render_bhl(basionym_name, lang)}
{render_inaturalist(basionym_name, basionym_qid, lang)}
{render_gbif(basionym_name, basionym_qid, lang)}
"""
    return text


# -----------------------------------------------------------
# Bird identifiers and links (now with language parameter)
# -----------------------------------------------------------
def get_bird_identifiers(qid, lang="pt"):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    query = f"""
    SELECT ?wiki_aves_bird_id ?ebird_taxon_id ?xeno_canto_species_id ?bird_label WHERE {{
      wd:{qid} wdt:P4664 ?wiki_aves_bird_id.
      wd:{qid} wdt:P3444 ?ebird_taxon_id.
      wd:{qid} wdt:P2426 ?xeno_canto_species_id.
      OPTIONAL {{
        wd:{qid} rdfs:label ?bird_label.
        FILTER (lang(?bird_label) = "{lang}").
      }}
    }}
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results["results"]["bindings"]


def get_bird_links(qid, lang="pt"):
    # Define language-specific strings for bird links.
    BIRD_LINK_STRINGS = {
        "pt": {
            "wikiaves": "Página do Wikiaves sobre a",
            "ebird": "Informações do eBird sobre a",
            "xeno": "Vocalizações de",
            "xeno_suffix": "no Xeno-canto",
        },
        "en": {
            "wikiaves": "Wikiaves page on",
            "ebird": "eBird information on",
            "xeno": "Vocalizations of",
            "xeno_suffix": "on Xeno-canto",
        },
        "es": {
            "wikiaves": "Página de Wikiaves sobre",
            "ebird": "Información de eBird sobre",
            "xeno": "Vocalizaciones de",
            "xeno_suffix": "en Xeno-canto",
        },
        "fr": {
            "wikiaves": "Page Wikiaves sur",
            "ebird": "Informations eBird sur",
            "xeno": "Vocalisations de",
            "xeno_suffix": "sur Xeno-canto",
        },
    }
    texts = BIRD_LINK_STRINGS.get(lang, BIRD_LINK_STRINGS["pt"])

    results = get_bird_identifiers(qid, lang)
    if len(results) > 0:
        res = results[0]
        wiki_aves_bird_id = res.get("wiki_aves_bird_id", {}).get("value")
        ebird_taxon_id = res.get("ebird_taxon_id", {}).get("value")
        xeno_canto_species_id = res.get("xeno_canto_species_id", {}).get("value")
        # Use the bird label if available; otherwise fallback to a default phrase.
        bird_label = res.get("bird_label", {}).get("value", "essa ave")
        bird_label = bird_label.lower()
        wikipedia_bird_links = f"""
* [https://www.wikiaves.com.br/wiki/{wiki_aves_bird_id} {texts['wikiaves']} {bird_label}]
* [https://ebird.org/species/{ebird_taxon_id} {texts['ebird']} {bird_label}]
* [https://www.xeno-canto.org/species/{xeno_canto_species_id} {texts['xeno']} {bird_label} {texts['xeno_suffix']}]"""
        return wikipedia_bird_links
    else:
        return ""


def get_wiki_page(qid, taxon_name, results_df, kingdom, class_name, family, genus, year_cat, lang):
    # Define language-specific settings (including extra keys for family, genus, and kingdom text)
    lang_settings = {
        "pt": {
            "title_format": "{{Título em itálico}}",
            "stub_template": "{{esboço-biologia}}",
            "references": "{{Referencias}}",
            "external_heading": "== Ligações externas ==",
            "authority": "{{Controle de autoridade}}",
            "description": "é uma espécie",
            "category_prefix": "[[Categoria:",
            "family_prefix": "da família",
            "genus_prefix": "do gênero",
            "kingdom_text": "de planta ",
        },
        "en": {
            "title_format": "{{Italic title}}",
            "stub_template": "{{Biology-stub}}",
            "references": "{{References}}",
            "external_heading": "== External links ==",
            "authority": "{{Authority control}}",
            "description": "is a species",
            "category_prefix": "[[Category:",
            "family_prefix": "of the family",
            "genus_prefix": "of the genus",
            "kingdom_text": "of plant",
        },
        "es": {
            "title_format": "",
            "stub_template": "",
            "references": """==Referencias==
{{listaref}}""",
            "external_heading": "== Enlaces externos ==",
            "authority": "{{Control de autoridad}}",
            "description": "es una especie",
            "category_prefix": "[[Categoría:",
            "family_prefix": "de la familia",
            "genus_prefix": "del género",
            "kingdom_text": "de planta",
        },
        "fr": {
            "title_format": "{{Titre en italique}}",
            "stub_template": "{{Bio-stub}}",
            "references": "{{Références}}",
            "external_heading": "== Liens externes ==",
            "authority": "{{Autorité de contrôle}}",
            "description": "est une espèce",
            "category_prefix": "[[Catégorie:",
            "family_prefix": "de la famille",
            "genus_prefix": "du genre",
            "kingdom_text": "de plante",
        },
    }
    settings = lang_settings.get(lang, lang_settings["pt"])

    # get_taxobox is assumed to accept a language parameter.
    taxobox = get_taxobox(qid, lang)

    if family is None:
        family_sentence = ""
    else:
        family_sentence = f" {settings['family_prefix']} [[{family}]]{LANG_STRINGS[lang]['e_join']}"

    if class_name == "Aves":
        bird_links = get_bird_links(qid, lang)
    else:
        bird_links = ""

    if kingdom == "Plantae":
        kingdom_text = settings["kingdom_text"]
    else:
        kingdom_text = ""

    external_links = render_external_links(
        taxon_name, qid, bird_links, settings["external_heading"], lang
    )

    wiki_page = f"""
{settings['title_format']}
{taxobox}
'''''{taxon_name}''''' {settings['description']} {kingdom_text}{family_sentence}{settings['genus_prefix']} ''[[{genus}]]''.  {get_gbif_ref(qid, lang)}
{render_taxonomy(results_df, qid, lang)}
{settings['references']}
{external_links}
{render_additional_reading(qid, lang)}
{settings['authority']}
{settings['stub_template']}
{settings['category_prefix']}{genus}]]{year_cat}"""

    categories = []
    for cat in categories:
        wiki_page += f"""{settings['category_prefix']}{cat}]]\n"""

    print("===== Saving wikipage =====")
    wiki_page = merge_equal_refs(wiki_page)
    wiki_page = wiki_page.replace("\n\n", "\n")
    wiki_page = re.sub("^ ", "", wiki_page, flags=re.M)
    return wiki_page


def italicize_taxon_name(taxon_name, wiki_page):
    """Turns taxon names into italic in the wiki page text."""
    wiki_page = re.sub(
        f"([^a-zA-ZÀ-ÿ'\[]]+){taxon_name}([^a-zA-ZÀ-ÿ']+)", f"\\1''{taxon_name}''\\2", wiki_page
    )
    return wiki_page


def open_related_urls(taxon_name):
    webbrowser.open(
        f"https://scholar.google.com/scholar?q=%22{taxon_name.replace(' ', '+')}%22+scielo"
    )
    webbrowser.open(f"https://google.com/search?q=%22{taxon_name.replace(' ', '+')}%22")


# -----------------------------------------------------------
# Functions to create pages and set sitelinks, now parameterized by language
# -----------------------------------------------------------
def create_wikipedia_page(taxon_name, wiki_page, lang):
    print("===== Creating Wikipedia page =====")
    site = pywikibot.Site(lang, "wikipedia")
    newPage = pywikibot.Page(site, taxon_name)
    newPage.text = wiki_page
    newPage.save("Stub created with code")


def set_sitelinks_on_wikidata(qid, taxon_name, lang):
    print("===== Setting sitelinks on Wikidata =====")
    site = pywikibot.Site("wikidata", "wikidata")
    repo = site.data_repository()
    item = pywikibot.ItemPage(repo, qid)
    data = [{"site": f"{lang}wiki", "title": taxon_name.replace(" ", "_")}]
    item.setSitelinks(data)
    return 0


def run_pipeline_for_wikipage(qid, language):
    new_qid = check_if_is_basionym(qid)
    if new_qid:
        print("This is a basionym. Do you want to proceed with the accepted name or your input?")
        print("Old QID: ", qid, "(https://www.wikidata.org/wiki/" + qid + ")")
        print("New QID: ", new_qid, "(https://www.wikidata.org/wiki/" + new_qid + ")")
        selection = input("Accepted name (a) or Basionym (b)?")
        if selection.lower() == "a":
            qid = new_qid

    results_df = get_results_dataframe_from_wikidata(qid)
    taxon_name = results_df["taxon_name.value"][0]

    parent_taxon_df = get_parent_taxon_df(qid, language)
    kingdom_name = get_kingdom_name(parent_taxon_df)
    family_name = get_family_name(parent_taxon_df)
    class_name = get_class_name(parent_taxon_df)
    genus_name = get_genus_name(parent_taxon_df)
    year_category = get_year_category(results_df, language)

    wiki_page = get_wiki_page(
        qid,
        taxon_name,
        results_df,
        kingdom_name,
        class_name,
        family_name,
        genus_name,
        year_category,
        language,
    )
    return wiki_page


# -----------------------------------------------------------
# Main command-line interface
# -----------------------------------------------------------
@click.command(name="render")
@click.option("--qid")
@click.option("--taxon", is_flag=True, help="Ask for a taxon name.")
@click.option("--taxon_name", help="Provide a taxon name directly (and quoted)")
@click.option("--open_url", is_flag=True, default=False, help="Open auxiliary pages")
@click.option("--show", is_flag=True, default=False, help="Print to screen only")
@click.option(
    "--language", default="pt", help="Language code for the generation (e.g., pt, en, es, fr)"
)
def main(qid: str, taxon: str, taxon_name: str, open_url: bool, show: bool, language: str):
    if taxon or taxon_name:
        qid = get_qid_from_name(taxon_name)
    results_df = get_results_dataframe_from_wikidata(qid)
    taxon_name = results_df["taxon_name.value"][0]

    if open_url:
        open_related_urls(taxon_name)

    wiki_page = run_pipeline_for_wikipage(qid, language)
    if show:
        print(f"--- {language} stub ---")
        print(wiki_page)
    else:
        filepath = f"wikipage_{language}.txt"
        with open(filepath, "w+") as f:
            f.write(wiki_page)
        print(f"The length of the {language} page is {len(wiki_page.encode('utf-8'))} bytes")
        create = input(f"Create {language} page with pywikibot? (y/n)")
        if create.lower() == "y":
            create_wikipedia_page(taxon_name, wiki_page, language)
        else:
            print("Skipping creation for", language)
        set_sitelinks_on_wikidata(qid, taxon_name, language)
        webbrowser.open(
            f"https://{language}.wikipedia.org/wiki/{taxon_name.replace(' ', '_')}?veaction=edit"
        )


if __name__ == "__main__":
    main()

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
from taxon2wikipedia.process_reflora import *


def get_kingdom_name(parent_taxon_df):
    genus_name = parent_taxon_df["taxonName.value"][
        parent_taxon_df["taxonRankLabel.value"] == "reino"
    ].item()
    return genus_name

# Functions
def get_family_name(parent_taxon_df):
    if "família" in parent_taxon_df["taxonRankLabel.value"]:
        family_name = parent_taxon_df["taxonName.value"][
            parent_taxon_df["taxonRankLabel.value"] == "família"
        ].item()
    else:
        family_name = None
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


def get_pt_wikipage_from_qid(qid, reflora_id=None, reflora_data=None):
    invasive_count = test_invasive_species(qid)

    if invasive_count:
        print(invasive_count)
    results_df = get_results_dataframe_from_wikidata(qid)

    parent_taxon_df = get_parent_taxon_df(qid)
    kingdom_name   = get_kingdom_name(parent_taxon_df)
    family_name = get_family_name(parent_taxon_df)
    genus_name = get_genus_name(parent_taxon_df)
    taxon_name = results_df["taxon_name.value"][0]

    year_category = get_year_category(results_df)

    wiki_page = get_wiki_page(
        qid,
        taxon_name,
        reflora_id,
        results_df,
        kingdom_name,
        family_name,
        genus_name,
        year_category,
        reflora_data,
    )

    return wiki_page


def render_external_links(reflora_id, taxon_name, qid):
    text = f"""
== Ligações externas ==
{render_reflora_link(taxon_name, qid)}
{render_cnc_flora(taxon_name)}
{render_bhl(taxon_name)}
{render_inaturalist(taxon_name, qid)}
  """
    return text


def get_wiki_page(qid, taxon_name, reflora_id, results_df,kingdom, family, genus, year_cat, reflora_data):
    if reflora_data is None:
        taxobox = get_taxobox(qid)

        if family is None:
            family_sentence = ""
        else:
            family_sentence = f" e da família [[{family}]]"

        if kingdom == "Plantae":
            kingdom_text = "de planta"
        else:
            kingdom_text = ""

        wiki_page = f"""
{{{{Título em itálico}}}}
{taxobox}
'''''{taxon_name}''''' é uma espécie {kingdom_text} do gênero ''[[{genus}]]''{family_sentence}.  {get_gbif_ref(qid)}
{render_taxonomy(reflora_data, results_df, qid)}
{{{{Referencias}}}}
{render_external_links(reflora_id, taxon_name,qid)}
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

    if "ehSinonimo" in reflora_data and "Nome correto" not in set(
        reflora_data["statusQualificador"]
    ):
        print("Synonym!")
        site, wiki_page = render_page_for_synonym(reflora_data)

        if not pywikibot.Page(site, taxon_name).exists():
            pass
        else:
            print("Page already exists. Quitting.")
            sys.exit()

    else:
        common_name_text = render_common_name(results_df, reflora_data)
        taxobox = get_taxobox(qid)

        free_description = render_free_description(reflora_data)
        comment = fix_description(render_comment(reflora_data))
        if free_description != "" or comment != "" or "descricaoCamposControlados" in reflora_data:
            notes = f"{get_cc_by_comment(reflora_data)}{get_ref_reflora(reflora_data)}"
            description_title = """
== Descrição =="""

        else:
            description_title = ""
            notes = ""

        notes = f"{get_cc_by_comment(reflora_data)}{get_ref_reflora(reflora_data)}"
        wiki_page = (
            f"""
{taxobox}
'''''{taxon_name}'''''{common_name_text} é uma espécie """
            f"""do gênero ''[[{genus}]]'' . {get_ref_reflora(reflora_data)}
{comment}"""
            f"""
{render_taxonomy(reflora_data, results_df, qid)}
{render_ecology(reflora_data)}
{description_title}
{render_free_description(reflora_data)}
{render_description_table(reflora_data)}
{render_distribution_from_reflora(reflora_data)}
{render_domains(reflora_data)}
{notes}
{{{{Referencias}}}}
{render_external_links(reflora_id, taxon_name,qid)}
{render_additional_reading(qid)}
{{{{Controle de autoridade}}}}
{{{{esboço-biologia}}}}
[[Categoria:{genus}]]{year_cat}"""
        )

        categories = [
            "Plantas",
            "Flora do Brasil",
        ]

        for cat in categories:
            wiki_page = (
                wiki_page
                + f"""[[Categoria:{cat}]]
"""
            )

        print("===== Saving wikipage =====")
        wiki_page = merge_equal_refs(wiki_page)
        wiki_page = wiki_page.replace("\n\n", "\n")
        wiki_page = re.sub("^ ", "", wiki_page, flags=re.M)
        wiki_page = italicize_taxon_name(taxon_name, wiki_page)

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


def get_and_save_reflora_data(reflora_id):
    try:
        reflora_data = get_reflora_data(reflora_id)
        HERE.joinpath("reflora.json").write_text(json.dumps(reflora_data, indent=4))
        return reflora_data
    except:
        return None


def add_vernacular_names_to_wikidata(reflora_data, qid):
    if len(reflora_data["nomesVernaculos"]) > 0:
        qs = print_qs_for_names(reflora_data, qid)
        webbrowser.open(render_qs_url(qs))


def create_wikipedia_page(taxon_name, wiki_page):
    print("===== Creating Wikipedia page =====")
    site = pywikibot.Site("pt", "wikipedia")
    newPage = pywikibot.Page(site, taxon_name)
    newPage.text = wiki_page
    newPage.save("Esboço criado com código de https://github.com/lubianat/taxon2wikipedia")


def set_sitelinks_on_wikidata(qid, taxon_name, reflora_data):
    print("===== Setting sitelinks on Wikidata =====")
    site = pywikibot.Site("wikidata", "wikidata")
    repo = site.data_repository()
    item = pywikibot.ItemPage(repo, qid)
    data = [{"site": "ptwiki", "title": taxon_name.replace(" ", "_")}]

    if reflora_data is None:
        item.setSitelinks(data)
        return 0

    if not "ehSinonimo" in reflora_data or "Nome correto" in set(
        reflora_data["statusQualificador"]
    ):
        item.setSitelinks(data)
        return 0


def add_reflora_id_to_wikidata(qid, reflora_id):
    print("===== Adding reflora ID to Wikidata =====")
    site = pywikibot.Site("wikidata", "wikidata")
    repo = site.data_repository()
    item = pywikibot.ItemPage(repo, qid)
    stringclaim = pywikibot.Claim(repo, "P10701")
    stringclaim.setTarget(f"FB{str(reflora_id)}")
    item.addClaim(stringclaim, summary="Adding a Reflora ID")


def add_endemic_status_to_wikidata(qid, reflora_id, reflora_data):
    if reflora_data["endemismo"] == "\u00e9 end\u00eamica do Brasil":
        print("===== Adding endemic status to Wikidata =====")
        site = pywikibot.Site("wikidata", "wikidata")
        repo = site.data_repository()
        item = pywikibot.ItemPage(repo, qid)
        claim = pywikibot.Claim(repo, "P183")
        target = pywikibot.ItemPage(repo, "Q155")
        claim.setTarget(target)
        item.addClaim(claim, summary="Adding endemic status")
        ref = pywikibot.Claim(repo, "P854")
        ref.setTarget(
            f"http://reflora.jbrj.gov.br/reflora/listaBrasil/FichaPublicaTaxonUC/FichaPublicaTaxonUC.do?id=FB{reflora_id}"
        )
        claim.addSources([ref], summary="Adding sources.")


@click.command(name="render")
@click.option("--qid")
@click.option("--taxon", is_flag=True, help="Ask for a taxon name.")
@click.option("--taxon_name", help="Provide a taxon name directly (and quoted)")
@click.option("--reflora-id", default="search", help="O número do taxon na base Reflora.")
@click.option("--open_url", is_flag=True, default=False, help="Abrir ou não as páginas auxiliares")
@click.option("--show", is_flag=True, default=False, help="Print to screen only")
def main(qid: str, taxon: str, taxon_name: str, reflora_id: str, open_url: bool, show: bool):
    if taxon or taxon_name:
        qid = get_qid_from_name(taxon_name)
    results_df = get_results_dataframe_from_wikidata(qid)
    taxon_name = results_df["taxon_name.value"][0]

    if open_url:
        open_related_urls(taxon_name)

    wiki_page = get_pt_wikipage_from_qid(qid, None, None)
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
    set_sitelinks_on_wikidata(qid, taxon_name, None)

    webbrowser.open(
        f"""https://pt.wikipedia.org/wiki/{taxon_name.replace(" ", "_")}?veaction=edit"""
    )


if __name__ == "__main__":
    main()

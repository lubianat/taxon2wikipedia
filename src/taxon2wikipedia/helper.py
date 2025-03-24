#!/usr/bin/env python3
import os
import webbrowser
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

# Global dictionary with language-specific strings
LANG_STRINGS = {
    "pt": {
        "taxonomia_header": "== Taxonomia ==",
        "info_taxonomia": "{{Info/Taxonomia",
        "ipni_link": "no Índice Internacional de Nomes de Plantas",
        "reflora_link": "no projeto Flora e Funga do Brasil",
        "bhl_link": "na Biodiversity Heritage Library",
        "gbif_link": "no GBIF",
        "inaturalist_link": "no iNaturalist",
        "cnc_flora_link": "no portal do Centro Nacional de Conservação da Flora (Brasil)",
        "leitura_adicional": "== Leitura adicional ==",
        "taxon_described": "O táxon foi descrito oficialmente em",
        "basionym_label": "basiônimo",
        "e_join": " e ",
    },
    "en": {
        "taxonomia_header": "== Taxonomy ==",
        "info_taxonomia": "{{Info/Taxonomy",
        "ipni_link": "in the International Plant Names Index",
        "reflora_link": "in the Flora and Funga of Brazil project",
        "bhl_link": "in the Biodiversity Heritage Library",
        "gbif_link": "in GBIF",
        "inaturalist_link": "in iNaturalist",
        "cnc_flora_link": "on the National Center for Plant Conservation portal",
        "leitura_adicional": "== Further reading ==",
        "taxon_described": "The taxon was officially described in",
        "basionym_label": "basionym",
        "e_join": " and ",
    },
    "es": {
        "taxonomia_header": "== Taxonomía ==",
        "info_taxonomia": "{{Ficha de taxón",
        "ipni_link": "en el Índice Internacional de Nombres de Plantas",
        "reflora_link": "en el proyecto Flora y Funga de Brasil",
        "bhl_link": "en la Biodiversity Heritage Library",
        "gbif_link": "en GBIF",
        "inaturalist_link": "en iNaturalist",
        "cnc_flora_link": "en el portal del Centro Nacional de Conservación de la Flora (Brasil)",
        "leitura_adicional": "== Lectura adicional ==",
        "taxon_described": "El taxón fue descrito oficialmente en",
        "basionym_label": "basónimo",
        "e_join": " y ",
    },
    "fr": {
        "taxonomia_header": "== Taxonomie ==",
        "info_taxonomia": "{{Taxobox",
        "ipni_link": "dans l'Index International des Noms de Plantes",
        "reflora_link": "dans le projet Flora et Funga du Brésil",
        "bhl_link": "dans la Biodiversity Heritage Library",
        "gbif_link": "dans GBIF",
        "inaturalist_link": "dans iNaturalist",
        "cnc_flora_link": "sur le portail du Centre National de Conservation de la Flore (Brésil)",
        "leitura_adicional": "== Lecture supplémentaire ==",
        "taxon_described": "Le taxon a été officiellement décrit en",
        "basionym_label": "basionym",
        "e_join": " et ",
    },
}


def check_if_is_basionym(qid):
    query = f"""
    SELECT * WHERE {{
        wd:{qid} wdt:P12766 ?current_name .
    }}  
    """
    df = get_rough_df_from_wikidata(query)
    if "current_name.value" not in df:
        return False
    return df["current_name.value"][0].split("/")[-1]


def check_if_has_basionym(qid):
    query = f"""
    SELECT * WHERE {{
        wd:{qid} wdt:P566 ?basionym .
    }}  
    """
    df = get_rough_df_from_wikidata(query)
    if "basionym.value" not in df:
        return False
    return df["basionym.value"][0].split("/")[-1]


def merge_equal_refs(wikipage):
    results = re.findall(f"(<ref>.*?</ref>)", wikipage)
    repeated_refs = [item for item, count in collections.Counter(results).items() if count > 1]
    for i, repeated_ref in enumerate(repeated_refs):
        parts = wikipage.partition(repeated_ref)
        print("========")
        wikipage = (
            parts[0]
            + re.sub(
                re.escape(repeated_ref),
                f'<ref name=":ref_{i}"> {repeated_ref.replace("<ref>", "")}',
                parts[1],
            )
            + re.sub(
                re.escape(repeated_ref),
                f'<ref name=":ref_{i}"/>',
                parts[2],
            )
        )
    return wikipage


def render_list_without_dict(list_of_names):
    text = ""
    for i, name in enumerate(list_of_names):
        if i == 0:
            text += name
        elif i == len(list_of_names) - 1:
            text += " e " + name
        else:
            text += ", " + name
    return text


def render_list(list_of_ids, dict_of_wikitexts):
    text = ""
    for i, entry in enumerate(list_of_ids):
        if i == 0:
            text += dict_of_wikitexts[entry]
        elif i == len(list_of_ids) - 1:
            text += " e " + dict_of_wikitexts[entry]
        else:
            text += ", " + dict_of_wikitexts[entry]
    return text


# Allow language parameter to be passed to the SPARQL query for labels.
def get_parent_taxon_df(qid, lang="pt"):
    query = (
        """
    SELECT 
      ?taxonRank
      ?taxonRankLabel
      ?taxonName
      ?taxon_range_map_image
    WHERE {
      VALUES ?taxon { wd:"""
        + qid
        + """} .
      ?taxon wdt:P171* ?parentTaxon.
      ?parentTaxon wdt:P105 ?taxonRank.
      ?parentTaxon wdt:P225 ?taxonName.
      SERVICE wikibase:label { bd:serviceParam wikibase:language \""""
        + lang
        + """\". }
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


def get_taxobox_from_df(parent_taxon_df, lang="pt"):
    field_mappings = {
        "es": {
            "reino": "regnum",
            "subdivisión": "unranked_divisio",
            "división": "divisio",
            "orden": "ordo",
            "familia": "familia",
            "infrarreino": "subregnum",
            "superdivisión": "superdivisio",
            "subfilo": "subphylum",
            "superdominio": "superregnum",
            "género": "genus",
            "subdominio": "subregnum",
            "subreino": "subregnum",
            "especie": "species",
        }
    }
    # Use the language-specific template for taxobox header.
    header = LANG_STRINGS.get(lang, LANG_STRINGS["pt"])["info_taxonomia"]
    result = header + "\n"
    result += "| imagem                = \n"
    for i, row in parent_taxon_df.iterrows():
        rank = row["taxonRankLabel.value"]
        name = row["taxonName.value"]
        # Exclude problematic taxa when "Aves" is present.
        if "Aves" in parent_taxon_df["taxonName.value"].values and name in {
            "Dinosauria",
            "Reptilia",
            "Saurischia",
            "Theropoda",
            "Maniraptora",
            "Maniraptoriformes",
            "Tetanurae",
            "Coelurosauria",
            "Neocoelurosauria",
            "Osteichthyes",
            "Elpistostegalia",
        }:
            continue
        if rank in ["super-reino", "subdivisão"]:
            continue
        n_space = 22 - len(rank)
        multiple_spaces = " " * max(n_space, 1)

        if lang == "es":
            mapped_rank = field_mappings.get(lang).get(rank, rank)
            to_append = f"| {mapped_rank}{multiple_spaces}= [[{name}]]\n"
        else:
            to_append = f"| {rank}{multiple_spaces}= [[{name}]]\n"
        result += to_append

    try:
        map_image = parent_taxon_df["taxon_range_map_image.value"].iloc[0]
        map_file = map_image.split("/")[-1].replace("%20", " ")
        result += f"| mapa = {map_file}\n"
    except (KeyError, IndexError):
        pass
    result += "}}"
    return result


def get_taxobox(qid, lang="pt"):
    df = get_parent_taxon_df(qid, lang)
    return get_taxobox_from_df(df, lang)


@click.command(name="taxobox")
@click.option("--qid")
@click.option("--taxon", is_flag=True, help="Ask for a taxon name.")
@click.option("--taxon_name", help="Provide a taxon name directly (and quoted)")
@click.option("--lang", default="pt", help="Language code for labels (e.g., pt, en, es, fr)")
def print_taxobox(qid: str, taxon: str, taxon_name: str, lang: str):
    if taxon or taxon_name:
        qid = get_qid_from_name(taxon_name)
    taxobox = get_taxobox(qid, lang)
    print(taxobox)


HERE = Path(__file__).parent.resolve()


def check_invasive_species(taxon_id):
    query = f"SELECT ?item WHERE {{ wd:{taxon_id} wdt:P5626 ?item }}"
    df = wikidata2df(query)
    if len(df) == 0:
        return False
    else:
        return df["item"][0]


def render_ipni_link(taxon_name, qid, lang="pt"):
    ipni_id = get_ipni_id(qid)
    if not ipni_id:
        return ""
    phrase = LANG_STRINGS.get(lang, LANG_STRINGS["pt"])["ipni_link"]
    return f"* [https://www.ipni.org/n/{ipni_id} ''{taxon_name}'' {phrase}.]"


def render_reflora_link(taxon_name, qid, lang="pt"):
    reflora_id = get_reflora_id(qid)
    if not reflora_id:
        return ""
    phrase = LANG_STRINGS.get(lang, LANG_STRINGS["pt"])["reflora_link"]
    return f"* [http://reflora.jbrj.gov.br/reflora/listaBrasil/FichaPublicaTaxonUC/FichaPublicaTaxonUC.do?id={reflora_id} ''{taxon_name}'' {phrase}]"


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
    if taxon_ok.lower() == "y":
        qid = taxon_result["id"]
    else:
        create_ok = input("Do you want to create the taxon? (y/n)")
        if create_ok.lower() == "y":
            os.system(f"taxon2wikipedia create --taxon_name '{taxon_name}'")
        print("quitting...")
        quit()
    return qid


def render_cnc_flora(taxon_name, lang="pt"):
    if check_cnc_flora(taxon_name):
        phrase = LANG_STRINGS.get(lang, LANG_STRINGS["pt"])["cnc_flora_link"]
        return f"* [http://cncflora.jbrj.gov.br/portal/pt-br/profile/{quote(taxon_name)} ''{taxon_name}'' {phrase}]"
    else:
        return ""


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


# External links: GBIF
GBIF_SUFFIX = {"pt": "no GBIF", "en": "in GBIF", "es": "en GBIF", "fr": "dans GBIF"}


def render_gbif(taxon_name, qid, lang="pt"):
    gbif_id = get_gbif_id(qid)
    if gbif_id:
        suffix = GBIF_SUFFIX.get(lang, GBIF_SUFFIX["pt"])
        return f"* [https://www.gbif.org/species/{gbif_id} ''{taxon_name}'' {suffix}]"
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
    return list(df["gbif_id.value"])[0]


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


def get_reflora_id(qid):
    query = f"""
    SELECT * WHERE {{ 
        wd:{qid} wdt:P10701 ?reflora_id .
    }}
    """
    df = get_rough_df_from_wikidata(query)
    if "reflora_id.value" not in df:
        return ""
    return list(df["reflora_id.value"])[0]


def get_inaturalist_id(qid):
    query = f"""
    SELECT * WHERE {{ 
        wd:{qid} wdt:P3151 ?inaturalist_id .
    }}
    """
    df = get_rough_df_from_wikidata(query)
    if "inaturalist_id.value" not in df:
        return ""
    return list(df["inaturalist_id.value"])[0]


def get_ipni_id(qid):
    query = f"""
    SELECT * WHERE {{ 
        wd:{qid} wdt:P961 ?ipni_id .
    }}
    """
    df = get_rough_df_from_wikidata(query)
    if "ipni_id.value" not in df:
        return ""
    return list(df["ipni_id.value"])[0]


def check_bhl(name):
    return True  # Placeholder


def check_cnc_flora(name):
    url = f"http://cncflora.jbrj.gov.br/portal/pt-br/profile/{name}"
    response = requests.get(url)
    return "Avaliador" in response.text


def render_additional_reading(qid, lang="pt"):
    query = f"""
    SELECT * WHERE {{ 
        ?article wdt:P921 wd:{qid} .
    }}
    """
    df = get_rough_df_from_wikidata(query)
    if "?article.value" not in df:
        return ""
    article_ids = list(df["article.value"])
    header = LANG_STRINGS.get(lang, LANG_STRINGS["pt"])["leitura_adicional"]
    additional_reading = header
    for id in article_ids:
        additional_reading += f"\n  * {{{{ Citar Q | {qid} }}}}"
    return additional_reading


def get_gbif_ref(qid, lang="pt"):
    query = f"""
    SELECT * WHERE {{ 
        wd:{qid} wdt:P846 ?gbif_id .
        wd:{qid} wdt:P225 ?taxon_name .
    }}
    """
    df = get_rough_df_from_wikidata(query)
    if "gbif_id.value" not in df:
        return ""
    gbif_id = list(df["gbif_id.value"])[0]
    taxon_name = list(df["taxon_name.value"])[0]
    if lang == "pt":
        ref = f"""<ref>{{{{Citar web|url=https://www.gbif.org/species/{gbif_id}|titulo={taxon_name}|acessodata=2022-04-18|website=www.gbif.org|lingua=en}}}}</ref>"""
    elif lang == "en":
        ref = f"""<ref>{{{{Cite web|url=https://www.gbif.org/species/{gbif_id}|title={taxon_name}|access-date=2022-04-18|website=www.gbif.org}}}}</ref>"""
    elif lang == "es":
        ref = f"""<ref>{{{{Citar web|url=https://www.gbif.org/species/{gbif_id}|título={taxon_name}|fechaacceso=2022-04-18|sitioweb=www.gbif.org}}}}</ref>"""
    elif lang == "fr":
        ref = f"""<ref>{{{{Citer web|url=https://www.gbif.org/species/{gbif_id}|titre={taxon_name}|consulté_le=2022-04-18|site=www.gbif.org
}}}}</ref>"""
    return ref


def render_taxonomy(results_df, qid, lang="pt"):
    strings = LANG_STRINGS.get(lang, LANG_STRINGS["pt"])
    if "taxon_authorLabel.value" not in results_df:
        description = ""
    else:
        taxon_author_labels = results_df["taxon_authorLabel.value"].values
        description_year = results_df["description_year.value"][0]
        taxon_author_labels = [f"[[{name}]]" for name in taxon_author_labels]
        description = f"{strings['taxon_described']} [[{description_year}]] por {render_list_without_dict(taxon_author_labels)}. {get_gbif_ref(qid, lang)}"
    text = f"\n{description}\n"
    qid_for_basionym = check_if_has_basionym(qid)
    if qid_for_basionym:
        basionym_results_df = get_results_dataframe_from_wikidata(qid_for_basionym)
        basionym_author_labels = basionym_results_df["taxon_authorLabel.value"].values
        basionym_year = basionym_results_df["description_year.value"][0]
        basionym_author_labels = [f"[[{name}]]" for name in basionym_author_labels]
        if lang == "pt":
            text += f"\nA espécie havia sido descrita anteriormente sob o [[{strings['basionym_label']}]] '''''{basionym_results_df['taxon_name.value'][0]}''''' (gênero ''[[{basionym_results_df['parent_taxonLabel.value'][0]}]]'') em {basionym_year} por {render_list_without_dict(basionym_author_labels)}. {get_gbif_ref(qid_for_basionym,lang)}\n"
        elif lang == "en":
            text += f"\nThe species had been previously described under the [[{strings['basionym_label']}]] '''''{basionym_results_df['taxon_name.value'][0]}''''' (genus ''[[{basionym_results_df['parent_taxonLabel.value'][0]}]]'') in {basionym_year} by {render_list_without_dict(basionym_author_labels)}. {get_gbif_ref(qid_for_basionym,lang)}\n"
        elif lang == "es":
            text += f"\nLa especie había sido descrita anteriormente bajo el [[{strings['basionym_label']}]] '''''{basionym_results_df['taxon_name.value'][0]}''''' (género ''[[{basionym_results_df['parent_taxonLabel.value'][0]}]]'') en {basionym_year} por {render_list_without_dict(basionym_author_labels)}. {get_gbif_ref(qid_for_basionym,lang)}\n"
        elif lang == "fr":
            text += f"\nL'espèce avait été décrite précédemment sous le [[{strings['basionym_label']}]] '''''{basionym_results_df['taxon_name.value'][0]}''''' (genre ''[[{basionym_results_df['parent_taxonLabel.value'][0]}]]'') en {basionym_year} par {render_list_without_dict(basionym_author_labels)}. {get_gbif_ref(qid_for_basionym,lang)}\n"

    if text.isspace():
        return ""
    else:
        header = strings["taxonomia_header"]
        return f"\n{header}\n{text}"


def render_common_name(results_df, lang="pt"):
    key = f"taxon_common_name_{lang}.value"
    try:
        common_names = results_df[key]
    except KeyError:
        try:
            common_names = results_df["taxon_common_name_pt.value"]
        except KeyError:
            return ""
    common_names = [f"'''{a}'''" for a in common_names]
    if len(common_names) == 0:
        return ""
    elif len(common_names) == 1:
        return f", também conhecido como {common_names[0]},"
    else:
        common_list = ", ".join(common_names[:-1])
        joiner = LANG_STRINGS.get(lang, LANG_STRINGS["pt"])["e_join"]
        return f", também conhecido como {common_list}{joiner}{common_names[-1]},"


# End of helper.py

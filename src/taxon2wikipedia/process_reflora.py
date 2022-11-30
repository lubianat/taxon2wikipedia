import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from taxon2wikipedia.cleanup import fix_description

HERE = Path(__file__).parent.resolve()
STATES_WIKI = json.loads(HERE.parent.joinpath("dicts/states_dict_pt.json").read_text())
VEGETATION_WIKI = json.loads(HERE.parent.joinpath("dicts/vegetation_wiki_pt.json").read_text())
DOMAINS_WIKI = json.loads(HERE.parent.joinpath("dicts/domain_wiki_pt.json").read_text())
ECOLOGY_WIKI = json.loads(HERE.parent.joinpath("dicts/ecology_wiki_pt.json").read_text())


def render_comment(data):

    try:
        if data["mostrarComentarioPublicoPT"] == True:
            text = f"""{data["comentarioPublicoPT"]} {get_ref_reflora(data)}"""
            return text
    except KeyError as e:
        return ""
    else:
        return ""


def render_free_description(data):
    try:
        if data["mostrarDescricaoLivrePT"] == True:
            text = f"""
{data["descricaoLivrePT"]}  {get_ref_reflora(data)}            
        """
            text = fix_description(text)
            text = text.replace("\n", " ")

            return text
    except KeyError as e:
        return ""
    else:
        return ""


def render_ecology(data):
    """
    Renders a session related to the ecology of the plant.
    """
    substrate = data["substrato"]
    life_form = data["formaVida"]
    substrate.extend(life_form)
    if len(substrate) == 0:
        return ""
    text = f"""
== Forma de vida ==
É uma espécie {render_list(substrate, ECOLOGY_WIKI)}. {get_ref_reflora(data)} """
    return text


def print_qs_for_names(data, qid):
    """
    Returns a string with Quickstatements commands to update common names.
    """
    names = get_common_names(data)
    qs = ""
    for name in names:

        qs += f'{qid}|P1843|pt:"{name}" \n'

    return qs


def get_common_names(data):
    """
    Gets the common names from Reflora in portuguese.
    """
    common_names = data["nomesVernaculos"]
    name_strings = []
    for name in common_names:
        if (
            name["lingua"].lower() == "portuguese"
            or name["lingua"] == "enum.label.NomesVernaculosLinguaEnum.PORTUGUES"
            or name["lingua"] == "Portugu\u00eas"
        ):
            name_strings.append(name["nome"])
    return name_strings


def get_cc_by_comment(data):
    text = data["citacao"].split("Jardim Bot")[0].replace("<i>", "''").replace("</i>", "''")
    wiki_text = f"""
== Notas ==
Contém texto em [[Licenças Creative Commons|CC-BY-SA 4.0]] de {text}"""
    return wiki_text


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


def render_description_table(data):
    if "descricaoCamposControlados" not in data:
        return ""
    else:
        controlled_fields = data["descricaoCamposControlados"]
        controlled_fields = controlled_fields.replace(r"(s)", "")
        controlled_fields = controlled_fields.replace(r"(ais)", "")
        controlled_fields = controlled_fields.replace(r"(es)", "")
        controlled_fields = controlled_fields.replace(r"(ns)", "")
        controlled_fields = controlled_fields.replace(r"(eis)", "")
        controlled_fields = controlled_fields.replace(r"(ções)", "")
        controlled_fields = controlled_fields.replace("<strong>", "")

        controlled_fields = controlled_fields.split(".")
        wikitable = f"""
        {{| class="wikitable" """
        for field in controlled_fields:

            try:
                title = field.split(":")[0].strip()
                content = field.split(":")[1]
                rows = content.split(";")
                wikitable += f"""
  |+
  ! colspan="2" |'''{title}'''<ref name=":ref_0" />"""

                for row in rows:
                    key = row.split("</strong>")[-2].strip()
                    value = row.split("</strong>")[-1].strip()
                    wikitable += f"""
  |-
  |'''{key}'''
  |{value}"""

            except Exception as e:
                pass
        wikitable += """
  |}"""
        wikitable = fix_description(wikitable)
        return wikitable


def render_domains(data):
    domains = data["dominioFitogeografico"]
    if len(domains) == 0:
        return ""
    elif len(domains) == 1:
        text = "Em termos ecológicos, é encontrada no [[Domínio morfoclimático e fitogeográfico|domínio fitogeográfico]] de "
    else:
        text = "Em termos ecológicos, é encontrada nos [[Domínio morfoclimático e fitogeográfico | domínios fitogeográficos]] de "
    text = text + render_list(domains, DOMAINS_WIKI)
    text = text + ","
    vegetations = data["tipoVegetacao"]
    text = text + " em regiões com vegetação de "
    text = text + render_list(vegetations, VEGETATION_WIKI)
    text = text + "."
    text = text + get_ref_reflora(data)

    return text


def get_ref_reflora(data):
    fb_id = data["id"].replace("FB", "")
    name = data["nomeStr"]
    ref = (
        "<ref>{{Citar web|url=https://floradobrasil2020.jbrj.gov.br/"
        f"FB{fb_id}|"
        f"titulo={name}|acessodata=2022-04-18|website=floradobrasil2020.jbrj.gov.br}}}}</ref> "
    )
    return ref


def render_category_by_state(data):
    # TODO
    pass


def render_distribution_from_reflora(data):

    if data["endemismo"] in [
        "endemicaBrasil.e.endemica.do.Brasil",
        "Is endemic from Brazil",
    ]:
        endemic_text = "[[endêmica]] do [[Brasil]] e "
    else:
        endemic_text = ""

    text = f"""

== Distribuição ==
A espécie é {endemic_text}"""

    states = get_states_from_reflora(data)
    if len(states) == 0:
        text + (".")
    elif len(states) == 1:
        text += "encontrada no estado brasileiro de "
    else:
        text += "encontrada nos estados brasileiros de "
    text += render_list(states, STATES_WIKI) + "."
    ref = get_ref_reflora(data)
    return text + ref


def get_reflora_data(fb_id):
    url = f"http://reflora.jbrj.gov.br/reflora/listaBrasil/ConsultaPublicaUC/ResultadoDaConsultaCarregaTaxonGrupo.do?&idDadosListaBrasil={fb_id}"
    r = requests.get(url)
    data = r.json()
    return data


def get_synonyms_from_reflora(data):
    if data is None:
        return ""

    name = data["nomeStr"]
    if "temComoSinonimo" not in data:
        return ""
    subspecies_html = data["temComoSinonimo"]
    soup = BeautifulSoup(subspecies_html, "lxml")
    species = []
    regex = '<div class="sinonimo">.*?<i>(.*?)<\/i>'
    regex_auth = '<div class="nomeAutorSinonimo">(.*?)<\/div>'
    mydivs = soup.find_all("a")
    for div in mydivs:
        try:
            results = re.findall(regex, str(div))
            author = re.findall(regex_auth, str(div))
            species.append("''" + " ".join(results) + "'' " + author[0])

        except:
            continue

    ref = get_ref_reflora(data)

    if len(species) == 1:
        text = f"O seguinte sinônimo já foi catalogado:  {ref}"

    else:
        text = f"Os seguintes sinônimos já foram catalogados:  {ref}"

    for i in species:

        text = (
            text
            + f"""
* {i} """
        )
    return text


def get_subspecies_from_reflora(data):
    if data is None:
        return ""
    name = data["nomeStr"]
    if "filhosSubspVar" not in data:
        return ""
    try:
        subspecies_html = data["filhosSubspVar"]
        soup = BeautifulSoup(subspecies_html)
        links = soup.find_all("a")
        species = []
        regex = '"nomeRank"> var\..*?"taxon".*?<i>(.*?)<\/i>'
        for link in links:
            results = re.search(regex, str(link))
            species.append(results.group(1))

        if len(species) == 0:
            return ""
        ref = get_ref_reflora(data)

        text = f"São conhecidas as seguintes subspécies de {name}:  {ref}"

        for i in species:

            text = (
                text
                + f"""
  * ''{name}'' var. ''{i}'' """
            )
        return text
    except Exception:
        return ""


def get_states_from_reflora(data):
    name = data["nomeStr"]

    states = data["estadosCerteza"]

    return states


if __name__ == "__main__":
    id = sys.argv[1]
    render_distribution_from_reflora(id)

from textwrap import indent
import requests
import sys
from pathlib import Path
import json
from bs4 import BeautifulSoup
import re

HERE = Path(__file__).parent.resolve()
STATES_WIKI = {
    "BA": "[[Bahia]]",
    "ES": "[[Espírito Santo (estado)|Espírito Santo]]",
    "AM": "[[Amazonas]]",
    "MT": "[[Mato Grosso]]",
    "PA": "[[Pará]]",
    "PB": "[[Paraíba]] ",
    "PE": "[[Pernambuco]]",
    "SE": "[[Sergipe]]",
    "AL": "[[Alagoas]]",
    "RJ": "[[Rio de Janeiro]]",
    "RR": "[[Roraima]]",
    "RN": "[[Rio Grande do Norte]]",
    "MG": "[[Minas Gerais]]",
    "SP": "[[São Paulo (estado)|São Paulo]]",
    "CE": "[[Ceará]]",
    "PI": "[[Piauí]]",
    "DF": "[[Distrito Federal]]",
    "GO": "[[Goiás]]",
    "PR": "[[Paraná]]",
    "RS": "[[Rio Grande do Sul]]",
    "SC": "[[Santa Catarina]]",
}

DOMAINS_WIKI = {
    "enum.label.DominiosFitogeograficosEnum.MATA_ATLANTICA": "[[Mata Atlântica]]",
    "enum.label.DominiosFitogeograficosEnum.CERRADO": "[[Cerrado]]",
    "enum.label.DominiosFitogeograficosEnum.PAMPA": "[[Pampa]]",
    "Central Brazilian Savanna": "[[Cerrado]]",
    "Atlantic Rainforest": "[[Mata Atlântica]]",
}

VEGETATION_WIKI = {
    "enum.label.DistribuicaoTipoVegetacaoEnum.FLORESTA_OMBROFILA": "[[Floresta húmida|floresta ombrófila pluvial]]",
    "enum.label.DistribuicaoTipoVegetacaoEnum.RESTINGA": "[[restinga]]",
    "enum.label.DistribuicaoTipoVegetacaoEnum.FLORESTA_CILIAR_GALERIA": "[[Vegetação ripária|mata ciliar]]",
    "enum.label.DistribuicaoTipoVegetacaoEnum.FLORESTA_ESTACIONAL_SEMIDECIDUAL": "[[floresta estacional decidual]]",
    "enum.label.DistribuicaoTipoVegetacaoEnum.FLORESTA_OMBROFILA_MISTA": "[[floresta ombrófila mista|mata de araucária]]",
    "enum.label.DistribuicaoTipoVegetacaoEnum.CAMPO_RUPESTRE": "[[campos rupestres]]",
    "Highland Rocky Field": "[[campos rupestres]]",
    "Riverine Forest and/or Gallery Forest": "[[Vegetação ripária|mata ciliar]]",
    "Ombrophyllous Forest (Tropical Rain Forest)": "[[Floresta húmida|floresta ombrófila pluvial]]",
    "Coastal Forest (Restinga)": "[[restinga]]",
}


def render_domains(data):
    domains = data["dominioFitogeografico"]

    if len(domains) == 0:
        return ""
    elif len(domains) == 1:
        text = "A espécie é encontrada no [[Domínio morfoclimático e fitogeográfico|domínio fitogeográfico]] de "
    else:
        text = "A espécie é encontrada nos [[Domínio morfoclimático e fitogeográfico | domínios fitogeográficos]] de "

    for i, domain in enumerate(domains):
        print(i)
        if i == 0:
            text = text + DOMAINS_WIKI[domain]
        elif i == len(domain) - 1:
            text = text + " e " + DOMAINS_WIKI[domain]
        else:
            text = text + ", " + DOMAINS_WIKI[domain]

    text = text + ","

    vegetations = data["tipoVegetacao"]

    text = text + " em regiões com vegetação de "

    for i, vegetation in enumerate(vegetations):
        print(i)
        if i == 0:
            text = text + VEGETATION_WIKI[vegetation]
        elif i == len(vegetation) - 1:
            text = text + " e " + VEGETATION_WIKI[vegetation]
        else:
            text = text + ", " + VEGETATION_WIKI[vegetation]
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


def render_distribution_from_reflora(data):

    if data["endemismo"] == "endemicaBrasil.e.endemica.do.Brasil":
        endemic_text = "[[endêmica]] do [[Brasil]] e "
    else:
        endemic_text = ""

    text = f"""
== Distribuição ==
A espécie é {endemic_text}encontrada nos estados brasileiros de """
    states = get_states_from_reflora(data)
    for i, state in enumerate(states):
        print(i)
        if i == 0:
            text = text + STATES_WIKI[state]
        elif i == len(states) - 1:
            text = text + " e " + STATES_WIKI[state] + ". "
        else:
            text = text + ", " + STATES_WIKI[state]
    ref = get_ref_reflora(data)
    return text + ref


def get_reflora_data(fb_id):
    url = (
        "https://floradobrasil2020.jbrj.gov.br/reflora/listaBrasil/"
        f"ConsultaPublicaUC/ResultadoDaConsultaCarregaTaxonGrupo.do?&idDadosListaBrasil={fb_id}"
    )
    r = requests.get(url)
    data = r.json()
    return data


def get_synonyms_from_reflora(data):
    name = data["nomeStr"]
    if "temComoSinonimo" not in data:
        return ""
    subspecies_html = data["temComoSinonimo"]
    soup = BeautifulSoup(subspecies_html)
    species = []
    regex = '<div class="sinonimo">.*?<i>(.*?)<\/i>'
    regex_auth = '<div class="nomeAutorSinonimo">(.*?)<\/div>'
    mydivs = soup.find_all("a")
    for div in mydivs:
        print(str(div))
        try:
            results = re.findall(regex, str(div))
            author = re.findall(regex_auth, str(div))

            species.append("''" + " ".join(results) + "'' " + author[0])
            print(results)

        except:
            continue

    ref = get_ref_reflora(data)

    text = f"Os seguintes sinônimos já foram catalogados:  {ref}"

    for i in species:

        text = (
            text
            + f"""
* {i} """
        )
    return text


def get_subspecies_from_reflora(data):
    name = data["nomeStr"]
    if "filhosSubspVar" not in data:
        return ""
    subspecies_html = data["filhosSubspVar"]
    soup = BeautifulSoup(subspecies_html)
    links = soup.find_all("a")
    species = []
    regex = '"nomeRank"> var\..*?"taxon".*?<i>(.*?)<\/i>'
    for link in links:
        print(str(link))
        results = re.search(regex, str(link))
        species.append(results.group(1))

    ref = get_ref_reflora(data)

    text = f"São conhecidas as seguintes subspécies de {name}:  {ref}"

    for i in species:

        text = (
            text
            + f"""
* ''{name}'' var. ''{i}'' """
        )
    return text


def get_states_from_reflora(data):
    name = data["nomeStr"]

    states = data["estadosCerteza"]
    HERE.joinpath("reflora.json").write_text(json.dumps(data, indent=4))

    return states


if __name__ == "__main__":
    id = sys.argv[1]
    render_distribution_from_reflora(id)

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
    "AP": "[[Amapá]]",
    "RO": "[[Rondônia]]",
    "RR": "[[Roraima]]",
    "MS": "[[Mato Grosso do Sul]]",
    "AC": "[[Acre]]",
    "MA": "[[Maranhão]]",
    "TO": "[[Tocantins]]",
}

DOMAINS_WIKI = {
    "enum.label.DominiosFitogeograficosEnum.MATA_ATLANTICA": "[[Mata Atlântica]]",
    "enum.label.DominiosFitogeograficosEnum.CERRADO": "[[Cerrado]]",
    "enum.label.DominiosFitogeograficosEnum.PAMPA": "[[Pampa]]",
    "Pampa": "[[Pampa]]",
    "Pantanal": "[[Pantanal]]",
    "Central Brazilian Savanna": "[[Cerrado]]",
    "Atlantic Rainforest": "[[Mata Atlântica]]",
    "Amazon Rainforest": "[[Floresta Amazônica]]",
    "Caatinga": "[[Caatinga]]",
}

VEGETATION_WIKI = {
    "enum.label.DistribuicaoTipoVegetacaoEnum.FLORESTA_OMBROFILA": "[[Floresta húmida|floresta ombrófila pluvial]]",
    "enum.label.DistribuicaoTipoVegetacaoEnum.RESTINGA": "[[restinga]]",
    "enum.label.DistribuicaoTipoVegetacaoEnum.FLORESTA_CILIAR_GALERIA": "[[Vegetação ripária|mata ciliar]]",
    "enum.label.DistribuicaoTipoVegetacaoEnum.FLORESTA_ESTACIONAL_SEMIDECIDUAL": "[[floresta estacional semidecidual]]",
    "enum.label.DistribuicaoTipoVegetacaoEnum.FLORESTA_OMBROFILA_MISTA": "[[floresta ombrófila mista|mata de araucária]]",
    "enum.label.DistribuicaoTipoVegetacaoEnum.CAMPO_RUPESTRE": "[[campos rupestres]]",
    "Highland Rocky Field": "[[campos rupestres]]",
    "Riverine Forest and/or Gallery Forest": "[[Vegetação ripária|mata ciliar]]",
    "Ombrophyllous Forest (Tropical Rain Forest)": "[[Floresta húmida|floresta ombrófila pluvial]]",
    "Coastal Forest (Restinga)": "[[restinga]]",
    "Rock outcrop vegetation": "vegetação sobre afloramentos rochosos",
    "Terra Firme Forest": "[[floresta de terra firme]]",
    "Inundated Forest (V\u00e1rzea)": "floresta de [[Planície de inundação|inundação]]",
    "Seasonally Semideciduous Forest": "[[floresta estacional semidecidual]]",
    "Inundated Forest (Igapó)": "[[mata de igapó]]",
    "Cerrado (lato sensu)": "[[cerrado]]",
    "Grassland": "[[pradaria]]",
}

ECOLOGY_WIKI = {
    "Epiphytic": "[[epífita]]",
    "Rupicolous": "[[rupícola]]",
    "Shrub": "[[arbustiva]]",
    "Herb": "[[herbácea]]",
    "Terrestrial": "[[terrícola]]",
    "Tree": "[[arbórea]]",
    "Saprophyte": "[[saprófita]]",
}


def render_ecology(data):
    substrate = data["substrato"]
    life_form = data["formaVida"]
    substrate.extend(life_form)
    text = f"""== Forma de vida ==
É uma espécie {render_list(substrate, ECOLOGY_WIKI)}. {get_ref_reflora(data)} 
    """
    return text


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


def render_domains(data):
    domains = data["dominioFitogeografico"]
    if len(domains) == 0:
        return ""
    elif len(domains) == 1:
        text = "A espécie é encontrada no [[Domínio morfoclimático e fitogeográfico|domínio fitogeográfico]] de "
    else:
        text = "A espécie é encontrada nos [[Domínio morfoclimático e fitogeográfico | domínios fitogeográficos]] de "
    text = text + render_list(domains, DOMAINS_WIKI)
    print("?????????")
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
    #TODO


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


def get_states_from_reflora(data):
    name = data["nomeStr"]

    states = data["estadosCerteza"]
    HERE.joinpath("reflora.json").write_text(json.dumps(data, indent=4))

    return states


if __name__ == "__main__":
    id = sys.argv[1]
    render_distribution_from_reflora(id)

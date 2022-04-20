from textwrap import indent
import requests
import sys
from pathlib import Path
import json
from bs4 import BeautifulSoup
import re

HERE = Path(__file__).parent.resolve()


def get_ref_reflora(fb_id):
    ref = (
        "<ref>{{Citar web|url=https://floradobrasil2020.jbrj.gov.br/"
        f"FB{fb_id}|"
        "titulo=Detalha Taxon Publico|acessodata=2022-04-18|website=floradobrasil2020.jbrj.gov.br}}</ref> "
    )
    return ref


def render_distribution_from_reflora(fb_id):
    text = """
== Distribuição ==

A espécie é encontrada nos estados brasileiros de """

    states = get_states_from_reflora(fb_id)

    for i, state in enumerate(states):
        print(i)
        if i == 0:
            text = text + STATES_WIKI[state]

        elif i == len(states) - 1:
            text = text + " e " + STATES_WIKI[state] + ". "
        else:
            text = text + ", " + STATES_WIKI[state]

    ref = get_ref_reflora(fb_id)
    return text + ref


def get_subspecies_from_reflora(fb_id):
    url = (
        "https://floradobrasil2020.jbrj.gov.br/reflora/listaBrasil/"
        f"ConsultaPublicaUC/ResultadoDaConsultaCarregaTaxonGrupo.do?&idDadosListaBrasil={fb_id}"
    )
    r = requests.get(url)
    data = r.json()
    name = data["nomeStr"]
    subspecies_html = data["filhosSubspVar"]
    soup = BeautifulSoup(subspecies_html)
    links = soup.find_all("a")
    species = []
    regex = '"nomeRank"> var\..*?"taxon".*?<i>(.*?)<\/i>'
    for link in links:
        print(str(link))
        results = re.search(regex, str(link))
        species.append(results.group(1))

    ref = get_ref_reflora(fb_id)

    text = f"The following subspecies of {name} are known: {ref}"

    for i in species:

        text = (
            text
            + f"""
* '''{name} {i}''' """
        )
    print(text)


def get_states_from_reflora(fb_id):
    url = (
        "https://floradobrasil2020.jbrj.gov.br/reflora/listaBrasil/"
        f"ConsultaPublicaUC/ResultadoDaConsultaCarregaTaxonGrupo.do?&idDadosListaBrasil={fb_id}"
    )
    r = requests.get(url)
    data = r.json()
    states = data["estadosCerteza"]
    HERE.joinpath("reflora.json").write_text(json.dumps(data, indent=4))

    return states


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
}


if __name__ == "__main__":
    id = sys.argv[1]
    render_distribution_from_reflora(id)

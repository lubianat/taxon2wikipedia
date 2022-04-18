import requests
import sys


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

    ref = (
        "<ref>{{Citar web|url=https://floradobrasil2020.jbrj.gov.br/"
        f"FB{fb_id}|"
        "titulo=Detalha Taxon Publico|acessodata=2022-04-18|website=floradobrasil2020.jbrj.gov.br}}</ref> "
    )
    return text + ref


def get_states_from_reflora(fb_id):
    url = (
        "https://floradobrasil2020.jbrj.gov.br/reflora/listaBrasil/"
        f"ConsultaPublicaUC/ResultadoDaConsultaCarregaTaxonGrupo.do?&idDadosListaBrasil={fb_id}"
    )
    r = requests.get(url)
    data = r.json()
    states = data["estadosCerteza"]

    return states


STATES_WIKI = {"BA": "[[Bahia]]", "ES": "[[Espírito Santo (estado)|Espírito Santo]]"}


if __name__ == "__main__":
    id = sys.argv[1]
    render_distribution_from_reflora(id)

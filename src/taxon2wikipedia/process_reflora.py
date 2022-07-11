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
    "enum.label.DominiosFitogeograficosEnum.AMAZONIA": "[[Floresta Amazônica]]",
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
    "enum.label.DistribuicaoTipoVegetacaoEnum.CAMPO_LIMPO": "campos limpos",
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
    "Caatinga (stricto sensu)": "[[caatinga]]",
    "Grassland": "[[pradaria]]",
    "High Altitude Grassland": "[[campos de altitude]]",
    "Anthropic area": "[[áreas antrópicas]]",
    "Mixed Ombrophyllous Forest": "[[floresta ombrófila mista|mata de araucária]]",
    "Seasonally Deciduous Forest": "floresta estacional decidual",
    "Amazonian Campinarana": "[[Campinarana]]",
    "Seasonal Evergreen Forest": "Floresta Estacional Perenifólia",
    "Amazonian Savanna": "savana amazônica",
    "Mangrove": "[[mangue]]",
    "Carrasco Vegetation": "[[vegetação de carrasco]]",
    "Palm Grove": "[[palmeiral]]",
}

ECOLOGY_WIKI = {
    "Epiphytic": "[[epífita]]",
    "Rupicolous": "[[rupícola]]",
    "Shrub": "[[arbustiva]]",
    "Subshrub": "[[subarbustiva]]",
    "Herb": "[[herbácea]]",
    "Terrestrial": "[[terrícola]]",
    "Tree": "[[arbórea]]",
    "Saprophyte": "[[saprófita]]",
    "Liana/scandent/vine": "[[trepadeira]]",
    "Corticicolous": "corticícola",
    "Hemiepiphytes": "[[hemiepífita]]",
    "Tufts": "presente em tufos",
    "Tuft": "presente em tufos",
    "Hemiparasites": "[[hemiparasitas]]",
    "Thallose": "talosa",
    "foliose": "folhosa",
    "Mat": "formadora de tapete",
    "Flabellate": "flabelada",
    "Epixilous": "epixila",
    "Weft": "formadora de tramas",
    "Palm Tree": "de [[palmeira]]",
    "Saxicolous": "[[litófita]]",
}

# New dicts created after source was changed to portuguese

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
            return text
    except KeyError as e:
        return ""
    else:
        return ""


def render_ecology(data):
    substrate = data["substrato"]
    life_form = data["formaVida"]
    substrate.extend(life_form)
    if len(substrate) == 0:
        return ""
    text = f"""== Forma de vida ==
É uma espécie {render_list(substrate, ECOLOGY_WIKI)}. {get_ref_reflora(data)} 
    """
    return text


def print_qs_for_names(data, qid):
    names = get_common_names(data)
    qs = ""
    for name in names:

        qs += f'{qid}|P1843|pt:"{name}" \n'

    return qs


def get_common_names(data):

    common_names = data["nomesVernaculos"]

    name_strings = []
    for name in common_names:
        if (
            name["lingua"].lower() == "portuguese"
            or name["lingua"] == "enum.label.NomesVernaculosLinguaEnum.PORTUGUES"
        ):
            name_strings.append(name["nome"])
    return name_strings


def get_cc_by_comment(data):
    text = data["citacao"].split("Jardim Bot")[0].replace("<i>", "''").replace("</i>", "''")
    wiki_text = f"""==Notas==
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
        return wikitable


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

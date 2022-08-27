#!/usr/bin/env python3

from .helper import *
from .process_reflora import *
from wdcuration import search_wikidata, render_qs_url
from jinja2 import Template
import os
import webbrowser
import pywikibot


@click.command(name="render")
@click.option("--qid")
@click.option("--taxon", is_flag=True, help="Pedir um nome de taxon")
@click.option("--taxon_name", help="O nome do taxon entre aspas.")
@click.option("--scope-name", default="planta", help="O escopo do táxon alvo.")
@click.option("--reflora-id", default="search", help="O número do taxon na base Reflora.")
@click.option("--open_url", default=False, help="Abrir ou não as páginas auxiliares")
def main(scope_name: str, qid: str, taxon: str, taxon_name: str, reflora_id: str, open_url: bool):

    if taxon or taxon_name:
        qid = get_qid_from_name(taxon_name)

    results_df = get_results_dataframe_from_wikidata(qid)

    parent_taxon_df = get_parent_taxon_df(qid)

    family = parent_taxon_df["taxonName.value"][
        parent_taxon_df["taxonRankLabel.value"] == "família"
    ].item()
    genus = parent_taxon_df["taxonName.value"][
        parent_taxon_df["taxonRankLabel.value"] == "género"
    ].item()
    taxon_name = results_df["taxon_name.value"][0]

    if "description_year.value" not in results_df:
        year_cat = ""
    else:
        description_year = results_df["description_year.value"][0]
        year_cat = f"[[Categoria:Plantas descritas em {description_year}]]"

    reflora_url = f"""http://servicos.jbrj.gov.br/flora/search/{taxon_name.replace(" ", "_")}"""

    if open_url:
        webbrowser.open(
            f"""https://scholar.google.com/scholar?q=%22{taxon_name.replace(" ", "+")}%22+scielo"""
        )
        webbrowser.open(f"""https://google.com/search?q=%22{taxon_name.replace(" ", "+")}%22""")

    if reflora_id == "search":
        r = requests.get(reflora_url, verify=False)
        webbrowser.open(reflora_url)
        reflora_id = r.url.split("FB")[-1]

    try:
        reflora_data = get_reflora_data(reflora_id)
        HERE.joinpath("reflora.json").write_text(json.dumps(reflora_data, indent=4))

        reflora_ok = True
    except:
        reflora_ok = False

    if len(reflora_data["nomesVernaculos"]) > 0:
        qs = print_qs_for_names(reflora_data, qid)
        webbrowser.open(render_qs_url(qs))

    if "ehSinonimo" in reflora_data and "Correct name" not in set(
        reflora_data["statusQualificador"]
    ):
        print("Synonym!")
        site = render_page_for_synonym(reflora_data)

        if not pywikibot.Page(site, taxon_name).exists():
            pass
        else:
            print("Page already exists. Quitting.")
            quit()

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
'''''{taxon_name}'''''{common_name_text} é uma espécie de """
            f"""[[{scope_name}]] do gênero ''[[{genus}]]'' e da família [[{family}]]. {get_ref_reflora(reflora_data)}
{comment}"""
            f"""
{render_taxonomy(reflora_data, results_df, qid)}
{render_ecology(reflora_data)}
{description_title}
{render_free_description(reflora_data)}
{render_description_table(reflora_data)}


== Conservação ==
A espécie faz parte da [[Lista Vermelha da IUCN|Lista Vermelha]] das espécies ameaçadas do estado do [[Espírito Santo (estado)|Espírito Santo]], no sudeste do [[Brasil]]. A lista foi publicada em 13 de junho de 2005 por intermédio do decreto estadual nº 1.499-R. <ref>{{{{Citar web|url=https://iema.es.gov.br/especies-ameacadas/fauna_ameacada|titulo=IEMA - Espécies Ameaçadas|acessodata=2022-04-12|website=iema.es.gov.br}}}}</ref>
{render_distribution_from_reflora(reflora_data)}
{render_domains(reflora_data)}


{notes}


{{{{Referencias}}}}


== Ligações externas ==
* [http://reflora.jbrj.gov.br/reflora/listaBrasil/FichaPublicaTaxonUC/FichaPublicaTaxonUC.do?id=FB{reflora_id} ''{taxon_name}'' no projeto Flora e Funga do Brasil]
{render_cnc_flora(taxon_name)}
{render_additional_reading(qid)}

{{{{Controle de autoridade}}}}

{{{{esboço-{scope_name}}}}}

[[Categoria:{family}]][[Categoria:{genus}]]{year_cat}"""
        )

        categories = [
            "Plantas",
            "Flora do Brasil",
            "Flora do Espírito Santo",
            "!Wikiconcurso Wiki Loves Espírito Santo (artigos)",
        ]

        for cat in categories:
            wiki_page = wiki_page + f"""[[Categoria:{cat}]]"""

        print("===== Saving wikipage =====")
        filepath = "wikipage.txt"
        wiki_page = merge_equal_refs(wiki_page)
        wiki_page = wiki_page.replace("\n\n", "\n")
        wiki_page = re.sub("^ ", "", wiki_page, flags=re.M)

        with open(filepath, "w+") as f:
            f.write(wiki_page)

        print(f"The length of the current page will be {len(wiki_page.encode('utf-8'))}")
        create = input("Create page with pywikibot? (y/n)")
        if create == "y":
            print("===== Creating Wikipedia page =====")
            site = pywikibot.Site("pt", "wikipedia")
            newPage = pywikibot.Page(site, taxon_name)
            newPage.text = wiki_page
            newPage.save("Esboço criado com código de https://github.com/lubianat/taxon2wikipedia")
        else:
            print("quitting...")
            quit()

        print("===== Setting sitelinks on Wikidata ===== ")
        site = pywikibot.Site("wikidata", "wikidata")
        repo = site.data_repository()
        item = pywikibot.ItemPage(repo, qid)
        if not "ehSinonimo" in reflora_data or "Correct name" in set(
            reflora_data["statusQualificador"]
        ):
            data = [{"site": "ptwiki", "title": taxon_name.replace(" ", "_")}]
            item.setSitelinks(data)

        webbrowser.open(
            f"""https://pt.wikipedia.org/wiki/{taxon_name.replace(" ", "_")}?veaction=edit"""
        )

        print("===== Adding reflora ID to Wikidata ===== ")
        stringclaim = pywikibot.Claim(repo, "P10701")
        stringclaim.setTarget(f"FB{str(reflora_id)}")
        item.addClaim(stringclaim, summary="Adding a Reflora ID")

        if reflora_data["endemismo"] == "\u00e9 end\u00eamica do Brasil":
            print("===== Adding endemic status to Wikidata =====")
            claim = pywikibot.Claim(repo, "P183")
            target = pywikibot.ItemPage(repo, "Q155")
            claim.setTarget(target)
            item.addClaim(claim, summary="Adding endemic status")
            ref = pywikibot.Claim(repo, "P854")
            ref.setTarget(
                f"http://reflora.jbrj.gov.br/reflora/listaBrasil/FichaPublicaTaxonUC/FichaPublicaTaxonUC.do?id=FB{reflora_id}"
            )
            claim.addSources([ref], summary="Adding sources.")


def render_page_for_synonym(reflora_data):
    synonym_name = reflora_data["ehSinonimo"]
    synonym_name = re.sub(
        '<a onclick=.*?taxon">(.*?)<\/div><div class="nomeAutorSinonimo">.*',
        "\\1",
        synonym_name,
    )
    synonym_name = synonym_name.replace("<span> <i>", "")
    synonym_name = synonym_name.replace("</i>", "")

    wiki_page = f"#REDIRECIONAMENTO[[{synonym_name}]]"

    site = pywikibot.Site("pt", "wikipedia")
    print(synonym_name)
    os.system(f'taxon2wikipedia render --taxon_name="{synonym_name}"')
    return site


def get_results_dataframe_from_wikidata(qid):
    template_path = Path(f"{HERE}/../data/full_query_taxon.rq.jinja")
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
    if taxon_ok == "y":
        qid = taxon_result["id"]
    else:
        create_ok = input("Do you want to create the taxon? (y/n)")
        if create_ok == "y":
            os.system(f"taxon2wikipedia create --taxon_name '{taxon_name}'")
        print("quitting...")
        quit()
    return qid


if __name__ == "__main__":
    main()

import re
from taxon2wikipedia.render_page import *

qid = "Q15514411"
language = "en"


def run_pipeline(qid, language):
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


# Test if Wikipage is a string


def test_wiki_page_is_string():
    assert isinstance(wiki_page, str)


def test_wikipage_in_portuguese():
    wiki_page = get_wiki_page(
        qid,
        taxon_name,
        results_df,
        kingdom_name,
        class_name,
        family_name,
        genus_name,
        year_category,
        "pt",
    )
    assert "pt.wikipedia.org" in wiki_page

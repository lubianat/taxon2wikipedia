from SPARQLWrapper import SPARQLWrapper, JSON


def get_identifiers(qid):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

    query = """
    SELECT ?wiki_aves_bird_id ?ebird_taxon_id ?xeno_canto_species_id ?bird_label WHERE {
      wd:%s wdt:P4664 ?wiki_aves_bird_id.
      wd:%s wdt:P3444 ?ebird_taxon_id.
      wd:%s wdt:P2426 ?xeno_canto_species_id.
      OPTIONAL {
        wd:%s rdfs:label ?bird_label.
        FILTER (lang(?bird_label) = "pt").
      }
    }
    """ % (
        qid,
        qid,
        qid,
        qid,
    )

    sparql.setQuery(query)

    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results["results"]["bindings"]


def format_links(qid):
    results = get_identifiers(qid)

    if len(results) > 0:
        res = results[0]
        wiki_aves_bird_id = res.get("wiki_aves_bird_id", {}).get("value")
        ebird_taxon_id = res.get("ebird_taxon_id", {}).get("value")
        xeno_canto_species_id = res.get("xeno_canto_species_id", {}).get("value")
        bird_label = res.get("bird_label", {}).get("value", "essa ave")
        bird_label = bird_label.lower()
        wikipedia_links = f"""== Ligações externas ==
* [https://www.wikiaves.com.br/wiki/{wiki_aves_bird_id} Página do Wikiaves sobre a  {bird_label}]
* [https://ebird.org/species/{ebird_taxon_id} Informações do eBird sobre a {bird_label}]
* [https://www.xeno-canto.org/species/{xeno_canto_species_id} Vocalizações de {bird_label} no Xeno-canto]"""

        return wikipedia_links
    else:
        return "No identifiers found."


# Example usage
print(format_links("Q1263946"))

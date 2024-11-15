#!/usr/bin/env python3

from urllib.parse import quote
import click
from jinja2 import Template
from wdcuration import render_qs_url, search_wikidata

from .helper import *


@click.command(name="create")
@click.option("--taxon_name", help="O nome do taxon entre aspas.")
def main(taxon_name: str):
    if not taxon_name:
        taxon_name = input("Nome científico do taxon:")
    genus_result = search_wikidata(taxon_name.split()[0])
    genus_ok = input(
        f'Wikidata found {genus_result["label"]} ({genus_result["description"]}). Is it correct (y/n)?'
    )
    if genus_ok == "y":
        genus_qid = genus_result["id"]
    else:
        print("quitting...")
        quit()
    qs = f"""
    CREATE
    LAST|Len|"{taxon_name}"
    LAST|Lpt|"{taxon_name}"
    LAST|Den|"species"
    LAST|Den|"espécie"
    LAST|P225|"{taxon_name}"
    LAST|P105|Q7432
    LAST|P171|{genus_qid}   
    """

    print(render_qs_url(qs))


if __name__ == "__main__":
    main()

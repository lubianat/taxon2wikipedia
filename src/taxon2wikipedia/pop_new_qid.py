from wikidata2df import wikidata2df

from pathlib import Path
import os
from random import randint
import click

HERE = Path(__file__).parent.resolve()


@click.command(name="pop")
def main():
    query = HERE.parent.joinpath("data").joinpath("plant_species_missing.rq").read_text()

    df = wikidata2df(query)

    index = randint(3, len(df))
    qid = df["item"][index]

    os.system(f"taxon2wikipedia render --qid {qid}")


if __name__ == "__main__":
    main()

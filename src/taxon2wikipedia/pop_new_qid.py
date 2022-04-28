from wikidata2df import wikidata2df

from pathlib import Path
import os
from random import randint

HERE = Path(__file__).parent.resolve()

query = HERE.parent.joinpath("data").joinpath("plant_species_missing.rq").read_text()

df = wikidata2df(query)

index = randint(3, len(df))
qid = df["item"][index]

os.system(f"python3 src/taxon2wikipedia/render_page_espirito_santo {qid}")

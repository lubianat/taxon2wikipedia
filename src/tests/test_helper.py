from taxon2wikipedia.helper import *


def test_gbif_taxobox():
    taxobox = get_taxobox_from_gbif("Q35694")
    print(taxobox)
    assert 1 == 1


if __name__ == "__main__":
    test_gbif_taxobox()

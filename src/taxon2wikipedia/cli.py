import click
from taxon2wikipedia import qid2taxobox
from . import pop_new_qid, render_page_espirito_santo, qid2taxobox


@click.group()
def cli():
    """Taxon2Wikipedia."""


cli.add_command(pop_new_qid.main)
cli.add_command(render_page_espirito_santo.main)
cli.add_command(qid2taxobox.print_taxobox)

if __name__ == "__main__":
    cli()

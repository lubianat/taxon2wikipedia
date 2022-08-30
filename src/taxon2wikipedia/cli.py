import click

from taxon2wikipedia import qid2taxobox

from . import create_taxon, qid2taxobox, render_page_espirito_santo


@click.group()
def cli():
    """Taxon2Wikipedia."""


cli.add_command(render_page_espirito_santo.main)
cli.add_command(create_taxon.main)
cli.add_command(qid2taxobox.print_taxobox)

if __name__ == "__main__":
    cli()

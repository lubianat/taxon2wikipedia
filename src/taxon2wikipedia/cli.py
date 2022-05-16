import click

from . import pop_new_qid, render_page_espirito_santo


@click.group()
def cli():
    """Taxon2Wikipedia."""


cli.add_command(pop_new_qid.main)
cli.add_command(render_page_espirito_santo.main)

if __name__ == "__main__":
    cli()

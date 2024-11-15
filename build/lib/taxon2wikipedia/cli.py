import click

from . import create_taxon, render_page, helper


@click.group()
def cli():
    """Taxon2Wikipedia."""


cli.add_command(render_page.main)
cli.add_command(create_taxon.main)
cli.add_command(helper.print_taxobox)

if __name__ == "__main__":
    cli()

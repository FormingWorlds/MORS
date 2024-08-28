import click

@click.group()
def cli():
    pass

@click.group()
def download():
    """Download data"""
    pass

@click.command()
def spada():
    """Download Spada evolution tracks."""
    from .data import DownloadEvolutionTracks
    DownloadEvolutionTracks("Spada")

@click.command()
def baraffe():
    """Download Baraffe evolution tracks."""
    from .data import DownloadEvolutionTracks
    DownloadEvolutionTracks("Baraffe")

@click.command()
def all():
    """Download all evolution tracks."""
    from .data import DownloadEvolutionTracks
    DownloadEvolutionTracks()

@click.command()
def env():
    """Show environment variables and locations"""
    from mors.data import FWL_DATA_DIR

    click.echo(f'FWL_DATA location: {FWL_DATA_DIR}')

cli.add_command(download)
download.add_command(spada)
download.add_command(baraffe)
download.add_command(all)
cli.add_command(env)

if __name__ == '__main__':
    cli()

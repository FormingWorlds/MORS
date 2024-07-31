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

cli.add_command(download)
download.add_command(spada)
download.add_command(baraffe)
download.add_command(all)

if __name__ == '__main__':
    cli()

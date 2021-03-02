"""Console script for mirror_up."""
import typer

import mirror_up.mirror_ace as mirror_ace  # type: ignore

from .main import app

app(prog_name="rick-portal-gun")
app = typer.Typer()
app.add_typer(mirror_ace.app, name="mirror_ace")

if __name__ == "__main__":
    app()

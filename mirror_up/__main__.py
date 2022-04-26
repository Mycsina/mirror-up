#!/usr/bin/python
"""Console script driver for mirror_up."""
import typer

import mirror_up.mirror_ace_cli as mirror_ace_cli

app = typer.Typer()
app.add_typer(mirror_ace_cli.app, name="mirror_ace")

if __name__ == "__main__":
    app()

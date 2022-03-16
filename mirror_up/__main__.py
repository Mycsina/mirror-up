#!/usr/bin/python
"""Console script for mirror_up."""
import mirror_up.mirror_ace as mirror_ace
import typer

app = typer.Typer()
app.add_typer(mirror_ace.app, name="mirror_ace")

if __name__ == "__main__":
    app()

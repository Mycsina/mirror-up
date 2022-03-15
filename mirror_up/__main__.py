"""Console script for mirror_up."""
import mirror_ace
import typer

if __name__ == "__main__":
    from mirror_ace import app
else:
    from .mirror_ace import app

app(prog_name="mirror_ace")
app = typer.Typer()
app.add_typer(mirror_ace.app, name="mirror_ace")

if __name__ == "__main__":
    app()

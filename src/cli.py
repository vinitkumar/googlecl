# -*- coding: utf-8 -*-

"""Console script for google_cl."""
import sys
import click
from src.authorize import Authorize

@click.group()
def cli():
    click.echo("Sunday Monday")

@cli.group()
def login():
    Authorize()

@cli.group()
def picasa():
    click.echo("This is a list")


@cli.group()
def contacts():
    click.echo("contacts placeholder")


@picasa.command()
def photolist():
    click.echo("This is coming from picasa list")

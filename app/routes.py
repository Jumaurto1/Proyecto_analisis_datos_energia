from flask import Blueprint, render_template
import nbformat
from nbconvert import HTMLExporter

main = Blueprint("main", __name__)

@main.route("/")
def index():
    # Cargar notebook
    notebook_filename = "notebooks/Proyecto_Bootcamp.ipynb"
    with open(notebook_filename) as f:
        nb = nbformat.read(f, as_version=4)

    # Convertir a HTML
    html_exporter = HTMLExporter()
    html_exporter.exclude_input = True  # opcional: oculta código
    notebook_html, _ = html_exporter.from_notebook_node(nb)

    return render_template("index.html", notebook_html=notebook_html)

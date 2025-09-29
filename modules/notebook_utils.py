import nbformat
from nbconvert import HTMLExporter
import dash_html_components as html
import plotly.io as pio
import plotly.graph_objects as go

def notebook_to_sections(notebook_path):
    """
    Convierte un notebook en secciones para Dash.
    Cada celda Markdown se vuelve un título o párrafo.
    Cada celda de código con salida gráfica se vuelve un dcc.Graph.
    """
    nb = nbformat.read(notebook_path, as_version=4)
    sections = []

    for cell in nb.cells:
        if cell.cell_type == "markdown":
            # Separar título y párrafo por tamaño
            if cell.source.startswith("# "):
                sections.append(html.H2(cell.source.replace("# ", "")))
            elif cell.source.startswith("## "):
                sections.append(html.H3(cell.source.replace("## ", "")))
            else:
                sections.append(html.P(cell.source))

        elif cell.cell_type == "code":
            # Si la celda tiene salida de tipo display_data o execute_result
            if cell.outputs:
                for output in cell.outputs:
                    if output.output_type in ["execute_result", "display_data"]:
                        if "image/png" in output.data:
                            # Puedes mostrar imágenes como html.Img
                            import base64
                            image = output.data["image/png"]
                            sections.append(html.Img(src=f"data:image/png;base64,{image}"))
                        elif "text/html" in output.data:
                            sections.append(html.Div([html.Div(output.data["text/html"])]))
                        elif "text/plain" in output.data:
                            sections.append(html.Pre(output.data["text/plain"]))
    return sections

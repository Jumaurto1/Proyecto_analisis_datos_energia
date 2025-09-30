# app.py
import pandas as pd
import dash
from dash import dcc, html, dash_table, Input, Output
import plotly.graph_objects as go
import plotly.express as px

# ==========================
# CARGA DE DATOS
# ==========================
# Si hay problemas de encoding prueba: pd.read_csv("mi_archivo.csv", encoding="latin-1")
df = pd.read_csv("mi_archivo.csv")

# Filtrar desde 2014
df = df[df["YEAR"] >= 2014]

# Asegurar que VALUE sea numérico
df["VALUE"] = pd.to_numeric(df["VALUE"], errors="coerce")

# Listas auxiliares
paises = sorted(df["COUNTRY"].unique())
min_YEAR = int(df["YEAR"].min())
max_YEAR = int(df["YEAR"].max())

# ==========================
# INICIALIZAR DASH APP
# ==========================
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# ==========================
# CALCULAR EMISIONES CO2
# ==========================
COEF_MAP = {
    'coal': 2.20,
    'oil': 2.10,
    'natural gas': 1.60,
    'natural': 1.60,
    'hydro': 0.0,
    'wind': 0.0,
    'solar': 0.0
}

def map_co2_coef(product):
    if pd.isna(product):
        return 0.0
    p = str(product).lower()
    for key, coef in COEF_MAP.items():
        if key in p:
            return coef
    return 0.0

df["COEF"] = df["PRODUCT"].apply(map_co2_coef)
df["CO2_PRODUCTION"] = df["VALUE"] * df["COEF"]


# ==========================
# ESTILO BANNER
# ==========================
BANNER_COLOR = "#003366"

banner = html.Div(
    style={
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
        "backgroundColor": BANNER_COLOR,
        "padding": "10px 30px",
    },
    children=[
        html.Img(src="/assets/TALENTO-TECH-EDUCACIO-TECNOLOGIA.png", style={"height": "60px"}),
        html.H1(
            "Factores claves para la transición energética en Colombia",
            style={"color": "white", "textAlign": "center", "flex": "1", "margin": "0"}
        ),
        html.Img(src="/assets/Logo.png", style={"height": "60px"}),
    ],
)

# ==========================
# FUNCIONES DE FIGURAS
# ==========================
def fig_matriz_area_colombia():
    df_col = df[df["COUNTRY"] == "Colombia"]
    df_col_matrx = df_col[df_col['PRODUCT'].isin(['Hydro', 'Solar', 'Wind', 'Natural gas', 'Oil', 'Coal'])]
    pivot = df_col_matrx.groupby(['YEAR', 'PRODUCT'], as_index=False)['VALUE'].sum()
    fig = px.area(
        pivot,
        x="YEAR",
        y="VALUE",
        color="PRODUCT",
        title="Matriz energética de Colombia por fuente",
        template="plotly_white"
    )
    fig.update_layout(
        legend_title="Fuente",
        title_x=0.5,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig

def fig_heatmap_colombia():
    df_col = df[df["COUNTRY"] == "Colombia"]
    products_order = ['Hydro', 'Solar', 'Wind', 'Natural gas', 'Oil', 'Coal']
    df_col_matrx = df_col[df_col['PRODUCT'].isin(products_order)].copy()

    # Preferir columna 'share' si existe y es numérica
    if 'share' in df_col_matrx.columns and pd.api.types.is_numeric_dtype(df_col_matrx['share']):
        df_col_matrx['share'] = pd.to_numeric(df_col_matrx['share'], errors='coerce')
    else:
        # Calcular share (%) por año
        df_col_matrx['share'] = df_col_matrx.groupby('YEAR')['VALUE'].transform(lambda x: x / x.sum() * 100)

    # Pivotear por PRODUCT x YEAR
    df_pivot = df_col_matrx.pivot_table(index='PRODUCT', columns='YEAR', values='share', aggfunc='mean')

    # Ordenar productos según la participación promedio (de mayor a menor)
    order = df_pivot.mean(axis=1).sort_values(ascending=False).index
    df_pivot = df_pivot.loc[order]

    # Round para presentación (4 decimales)
    df_pivot = df_pivot.round(4)

    if df_pivot.empty:
        fig = go.Figure()
        fig.update_layout(title="No hay datos disponibles para el heatmap (Colombia)")
        return fig

    # Construir heatmap
    fig = px.imshow(
        df_pivot.values,
        x=[str(y) for y in df_pivot.columns],
        y=df_pivot.index,
        text_auto=".4f",  # valores con 4 decimales
        color_continuous_scale="YlGnBu",
        aspect="auto",
        labels={'x': 'Año', 'y': 'Fuente energética', 'color': 'Participación (%)'},
        title=f"Participación promedio anual de cada fuente energética en Colombia ({min_YEAR}-{max_YEAR})"
    )

    # Hover con más precisión
    if fig.data:
        fig.data[0].hovertemplate = 'Fuente: %{y}<br>Año: %{x}<br>Share: %{z:.4f}%<extra></extra>'

    fig.update_layout(
        title_x=0.5,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis_title="Año",
        yaxis_title="Fuente energética",
        template="plotly_white"
    )
    return fig

def fig_solar_wind_line():
    df_col = df[df["COUNTRY"]=="Colombia"]
    df_sw = df_col[df_col["PRODUCT"].isin(["Solar", "Wind"])]
    pivot = df_sw.groupby(['YEAR','PRODUCT'], as_index=False)['VALUE'].sum()
    fig = px.line(
        pivot,
        x="YEAR",
        y="VALUE",
        color="PRODUCT",
        markers=True,
        title="Generación Solar vs Wind en Colombia",
        template="plotly_white"
    )
    fig.update_layout(title_x=0.5, margin=dict(l=40, r=40, t=60, b=40))
    return fig

def fig_co2_comparacion(paises_selec):
    if not paises_selec:
        return go.Figure()
    d = df[df["COUNTRY"].isin(paises_selec + ["Colombia"])].copy()
    if d.empty:
        return go.Figure()
    by = d.groupby(["YEAR", "COUNTRY"], as_index=False)["CO2_PRODUCTION"].sum()
    fig = px.line(
        by,
        x="YEAR",
        y="CO2_PRODUCTION",
        color="COUNTRY",
        markers=True,
        title="Comparación de emisiones de CO₂",
        template="plotly_white"
    )
    fig.update_layout(title_x=0.5, margin=dict(l=40, r=40, t=60, b=40))
    return fig
def fig_co2_pie(paises_selec):
    if not paises_selec:
        return go.Figure()
    d = df[df["COUNTRY"].isin(paises_selec)].copy()
    agg = d.groupby("COUNTRY", as_index=False)["CO2_PRODUCTION"].sum()
    if agg.empty:
        return go.Figure()
    fig = px.pie(agg, names="COUNTRY", values="CO2_PRODUCTION",
                 title="Proporción de CO₂ por país", template="plotly_white")
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(title_x=0.5)
    return fig

# ==========================
# FUNCIONES KPI
# ==========================
def kpi_cards():
    df_col = df[df["COUNTRY"] == "Colombia"]
    total_co2 = df_col[df_col["PRODUCT"].str.upper().isin(["CO2", "CO₂"])]["VALUE"].sum()
    total_generacion = df_col["VALUE"].sum()
    renovables = df_col[df_col["PRODUCT"].isin(["Solar", "Wind"])]["VALUE"].sum()
    porcentaje_renovables = (renovables / total_generacion * 100) if total_generacion > 0 else 0
    ano_max_gen = int(df_col.groupby("YEAR")["VALUE"].sum().idxmax()) if not df_col.empty else None

    style_card = {
        "border": "1px solid #ccc",
        "border-radius": "5px",
        "padding": "20px",
        "margin": "5px",
        "flex": "1",
        "background-color": "#f9f9f9",
        "textAlign": "center"
    }

    return html.Div([
        html.Div([html.H4("Total CO₂ Colombia"), html.H3(f"{total_co2:,.0f}")], style=style_card),
        html.Div([html.H4("% Energía Renovable"), html.H3(f"{porcentaje_renovables:.1f}%")], style=style_card),
        html.Div([html.H4("Año Mayor Generación"), html.H3(f"{ano_max_gen}")], style=style_card),
        html.Div([html.H4("Total Generación"), html.H3(f"{total_generacion:,.0f}")], style=style_card),
    ], style={"display": "flex", "justifyContent": "space-around", "margin-bottom": "20px"})

# ==========================
# TAB 1: EXPLORACIÓN
# ==========================
table_header_style = {
    "backgroundColor": BANNER_COLOR,
    "color": "white",
    "fontWeight": "bold",
    "textTransform": "uppercase"
}

exploracion_layout = html.Div([
    html.H3("Exploración del Dataset"),

    html.H4("Dataset completo"),
    dash_table.DataTable(
        id="tabla-completa",
        data=df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in df.columns],
        page_size=20,
        style_table={"overflowX": "auto"},
        style_header=table_header_style,
    ),

    html.H4("Dataset - Solo Colombia"),
    dash_table.DataTable(
        id="tabla-colombia",
        data=df[df["COUNTRY"] == "Colombia"].to_dict("records"),
        columns=[{"name": c, "id": c} for c in df.columns],
        page_size=20,
        style_table={"overflowX": "auto"},
        style_header=table_header_style,
    ),

    html.H4("Estadísticas de Colombia"),
    dash_table.DataTable(
        id="tabla-estadisticas",
        data=df[df["COUNTRY"] == "Colombia"].describe().reset_index().to_dict("records"),
        columns=[{"name": c, "id": c} for c in df[df["COUNTRY"] == "Colombia"].describe().reset_index().columns],
        page_size=20,
        style_table={"overflowX": "auto"},
        style_header=table_header_style,
    ),

    html.H4("Países disponibles en el Dataset"),
    html.Ul([html.Li(p) for p in paises])
])

# ==========================
# TAB 2: PROBLEMÁTICA 1
# ==========================
problem1_layout = html.Div([
    html.H3("Problemática 1: Emisiones y matriz energética en Colombia"),
    kpi_cards(),
    
    # Fila 1: Matriz y Heatmap
    html.Div([
        html.Div([dcc.Graph(figure=fig_matriz_area_colombia())], 
                 style={'width': '49%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(figure=fig_heatmap_colombia())], 
                 style={'width': '49%', 'display': 'inline-block'})
    ]),
    
    # Fila 2: Solar vs Wind + Texto explicativo
    html.Div([
        html.Div([dcc.Graph(figure=fig_solar_wind_line())], 
                 style={'width': '49%', 'display': 'inline-block'}),
        html.Div([
            html.H5("Análisis de la matriz energética en Colombia"),
            html.P("1. Matriz energética Colombia"),
            html.P("Esta gráfica apilada nos muestra que cada capa de energía contribuye al total de electricidad generada en Colombia."),
            html.Br(),
            html.P("2. Heatmap sobre aporte en Colombia"),
            html.P("Se observa que Colombia depende casi por completo de la energía hidroeléctrica. "
                   "La implementación de otras energías renovables es ínfima, lo que indica que esta matriz energética es vulnerable; "
                   "cualquier sequía fuerte (fenómeno del Niño) o inconvenientes técnicos puede comprometer la estabilidad energética "
                   "porque no hay respaldo suficiente en materia de energías solar/eólica.")
        ], style={'width': '40%', 'display': 'inline-block', 'verticalAlign': 'justify', 'padding': '50px'})
    ]),
    
    # Fila 3: Filtro único + Gráficos CO₂
    html.Div([
        html.H4("Análisis de CO₂ por país"),
        dcc.Dropdown(
            id="dropdown-paises-unico",
            options=[{"label": p, "value": p} for p in paises],
            value=["Colombia"],  
            multi=True,
            style={'width': '100%'}
        ),
        
        html.Div([
            html.Div([dcc.Graph(id="co2-comparacion")], 
                     style={'width': '49%', 'display': 'inline-block'}),
            html.Div([dcc.Graph(id="co2-pie-chart")], 
                     style={'width': '49%', 'display': 'inline-block'})
        ])
    ], style={'margin-top': '20px'})
])

# OTRAS TABS (sin modificar)
problem2_layout = html.Div([html.H3("Problemática 2")])
problem3_layout = html.Div([html.H3("Problemática 3")])
problem4_layout = html.Div([html.H3("Problemática 4")])

# ==========================
# LAYOUT PRINCIPAL
# ==========================
app.layout = html.Div([
    banner,
    dcc.Tabs(
        id="tabs",
        value="tab1",
        children=[
            dcc.Tab(label="Exploración", value="tab1"),
            dcc.Tab(label="Problemática 1", value="tab2"),
            dcc.Tab(label="Problemática 2", value="tab3"),
            dcc.Tab(label="Problemática 3", value="tab4"),
            dcc.Tab(label="Problemática 4", value="tab5"),
        ]
    ),
    html.Div(id="tabs-content")
])

# ==========================
# CALLBACKS DE NAVEGACIÓN
# ==========================
@app.callback(Output("tabs-content", "children"), Input("tabs", "value"))
def render_tab(tab):
    if tab == "tab1":
        return exploracion_layout
    elif tab == "tab2":
        return problem1_layout
    elif tab == "tab3":
        return problem2_layout
    elif tab == "tab4":
        return problem3_layout
    elif tab == "tab5":
        return problem4_layout

# ==========================
# CALLBACKS GRÁFICAS
# ==========================
@app.callback(
    [Output("co2-comparacion", "figure"),
     Output("co2-pie-chart", "figure")],
    [Input("dropdown-paises-unico", "value")]
)
def actualizar_graficas(paises_seleccionados):
    fig1 = fig_co2_comparacion(paises_seleccionados)
    fig2 = fig_co2_pie(paises_seleccionados)
    return fig1, fig2

# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    app.run_server(debug=True)

import pandas as pd
import dash
from dash import dcc, html, dash_table, Input, Output
import plotly.graph_objects as go
import plotly.express as px

# ==========================
# CARGA DE DATOS
# ==========================
df = pd.read_csv("mi_archivo.csv")

# Filtrar desde 2014
df = df[df["YEAR"] >= 2014]

# Asegurar que VALUE sea numérico
df["VALUE"] = pd.to_numeric(df["VALUE"], errors="coerce")

# Listas auxiliares
paises = sorted(df["COUNTRY"].unique())
max_YEAR = df["YEAR"].max()

# ==========================
# INICIALIZAR DASH APP
# ==========================
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# ==========================
# ESTILO BANNER
# ==========================
banner = html.Div(
    style={
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
        "backgroundColor": "#003366",
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
    df_col = df[df["COUNTRY"]=="Colombia"]
    df_col_matrx = df_col[df_col['PRODUCT'].isin(['Hydro', 'Solar', 'Wind', 'Natural gas', 'Oil', 'Coal'])]
    pivot = df_col_matrx.groupby(['YEAR','PRODUCT'], as_index=False)['VALUE'].sum()
    pivot2 = pivot.pivot(index='YEAR', columns='PRODUCT', values='VALUE').fillna(0)
    fig = go.Figure()
    for col in pivot2.columns:
        fig.add_trace(go.Scatter(
            x=pivot2.index,
            y=pivot2[col],
            stackgroup='one',
            name=col,
            line_shape='spline'
        ))
    fig.update_layout(
        title="Matriz energética de Colombia por fuente",
        xaxis_title="Año",
        yaxis_title="Generación",
        legend_title="Fuente",
        title_x=0.5,
        template="plotly_white"
    )
    return fig

def fig_heatmap_colombia():
    df_col = df[df["COUNTRY"]=="Colombia"]
    df_col_matrx = df_col[df_col['PRODUCT'].isin(['Hydro', 'Solar', 'Wind', 'Natural gas', 'Oil', 'Coal'])]
    
    # Calcular share %
    df_col_matrx = df_col_matrx.copy()
    df_col_matrx['share'] = df_col_matrx.groupby('YEAR')['VALUE'].transform(lambda x: x/x.sum()*100)
    
    # Usar pivot_table en vez de pivot
    df_pivot = df_col_matrx.pivot_table(
        index='PRODUCT',
        columns='YEAR',
        values='share',
        aggfunc='mean'  # <-- Esto evita el error
    )
    
    fig = px.imshow(
        df_pivot,
        text_auto=True,
        color_continuous_scale="Blues",
        aspect="auto",
        title=f"Participación anual por fuente energética (2014-{max_YEAR})"
    )
    fig.update_layout(
        title_x=0.5,
        xaxis_title="Año",
        yaxis_title="Fuente energética",
        template="plotly_white"
    )
    return fig


def fig_solar_wind_line():
    df_col = df[df["COUNTRY"]=="Colombia"]
    df_sw = df_col[df_col["PRODUCT"].isin(["Solar","Wind"])]
    pivot = df_sw.groupby(['YEAR','PRODUCT'], as_index=False)['VALUE'].sum()
    pivot2 = pivot.pivot(index='YEAR', columns='PRODUCT', values='VALUE').fillna(0)
    fig = go.Figure()
    for col in pivot2.columns:
        fig.add_trace(go.Scatter(
            x=pivot2.index,
            y=pivot2[col],
            mode='lines+markers',
            name=col,
            line_shape='spline'
        ))
    fig.update_layout(
        title="Generación Solar vs Wind en Colombia",
        xaxis_title="Año",
        yaxis_title="Generación",
        legend_title="Fuente",
        title_x=0.5,
        template="plotly_white"
    )
    return fig

def fig_co2_comparacion(paises_selec):
    if not paises_selec:
        return go.Figure()
    df_co2 = df[df["PRODUCT"].str.upper().isin(["CO2","CO₂"])]
    df_fil = df_co2[df_co2["COUNTRY"].isin(paises_selec+["Colombia"])]
    pivot = df_fil.groupby(['YEAR','COUNTRY'], as_index=False)['VALUE'].sum()
    pivot2 = pivot.pivot(index='YEAR', columns='COUNTRY', values='VALUE').fillna(0)
    fig = go.Figure()
    for col in pivot2.columns:
        fig.add_trace(go.Scatter(
            x=pivot2.index,
            y=pivot2[col],
            mode='lines+markers',
            name=col,
            line_shape='spline'
        ))
    fig.update_layout(
        title="Comparación de emisiones de CO₂",
        xaxis_title="Año",
        yaxis_title="Emisiones CO₂",
        legend_title="País",
        title_x=0.5,
        template="plotly_white"
    )
    return fig

def fig_co2_pie(paises_selec):
    if not paises_selec:
        return go.Figure()
    df_co2 = df[df["PRODUCT"].str.upper().isin(["CO2","CO₂"])]
    df_fil = df_co2[df_co2["COUNTRY"].isin(paises_selec)]
    df_sum = df_fil.groupby("COUNTRY")["VALUE"].sum().reset_index()
    fig = px.pie(df_sum, names="COUNTRY", values="VALUE", title="Proporción de CO₂ por país", template="plotly_white")
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(title_x=0.5)
    return fig

# ==========================
# FUNCIONES KPI
# ==========================
def kpi_cards():
    df_col = df[df["COUNTRY"]=="Colombia"]
    total_co2 = df_col[df_col["PRODUCT"].str.upper().isin(["CO2","CO₂"])]["VALUE"].sum()
    total_generacion = df_col["VALUE"].sum()
    renovables = df_col[df_col["PRODUCT"].isin(["Solar","Wind"])]["VALUE"].sum()
    porcentaje_renovables = (renovables/total_generacion*100) if total_generacion>0 else 0
    ano_max_gen = df_col.groupby("YEAR")["VALUE"].sum().idxmax()

    style_card = {
        "border":"1px solid #ccc",
        "border-radius":"5px",
        "padding":"20px",
        "margin":"5px",
        "flex":"1",
        "background-color":"#f9f9f9",
        "textAlign":"center"
    }

    return html.Div([
        html.Div([html.H4("Total CO₂ Colombia"), html.H3(f"{total_co2:,.0f}")], style=style_card),
        html.Div([html.H4("% Energía Renovable"), html.H3(f"{porcentaje_renovables:.1f}%")], style=style_card),
        html.Div([html.H4("Año Mayor Generación"), html.H3(f"{ano_max_gen}")], style=style_card),
        html.Div([html.H4("Total Generación"), html.H3(f"{total_generacion:,.0f}")], style=style_card),
    ], style={"display":"flex", "justifyContent":"space-around", "margin-bottom":"20px"})

# ==========================
# LAYOUTS
# ==========================
exploracion_layout = html.Div([
    html.H3("Exploración del Dataset"),
    dash_table.DataTable(
        id="tabla-completa",
        columns=[{"name":c,"id":c} for c in df.columns],
        data=df.head(50).to_dict("records"),
        page_size=20,
        style_table={"overflowX":"auto"}
    ),
])

problem1_layout = html.Div([
    html.H3("Problemática 1: Emisiones y matriz energética en Colombia"),
    kpi_cards(),
    html.Div([
        html.Div([dcc.Graph(figure=fig_matriz_area_colombia())], style={'width':'49%','display':'inline-block'}),
        html.Div([dcc.Graph(figure=fig_heatmap_colombia())], style={'width':'49%','display':'inline-block'})
    ]),
    html.Div([
        html.Div([dcc.Graph(figure=fig_solar_wind_line())], style={'width':'49%','display':'inline-block'}),
        html.Div([
            html.H4("Comparación CO₂ vs otros países"),
            dcc.Dropdown(
                id="dropdown-paises-co2",
                options=[{"label":p,"value":p} for p in paises if p!="Colombia"],
                multi=True,
                placeholder="Seleccione países"
            ),
            dcc.Graph(id="co2-comparacion")
        ], style={'width':'49%','display':'inline-block'})
    ]),
    html.Div([
        html.H4("Distribución CO₂ por país"),
        dcc.Dropdown(
            id="dropdown-paises-pastel",
            options=[{"label":p,"value":p} for p in paises],
            multi=True,
            placeholder="Seleccione países"
        ),
        dcc.Graph(id="co2-pie-chart")
    ])
])

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
    if tab=="tab1":
        return exploracion_layout
    elif tab=="tab2":
        return problem1_layout
    elif tab=="tab3":
        return problem2_layout
    elif tab=="tab4":
        return problem3_layout
    elif tab=="tab5":
        return problem4_layout

# ==========================
# CALLBACKS GRÁFICAS
# ==========================
@app.callback(
    Output("co2-comparacion", "figure"),
    Input("dropdown-paises-co2", "value")
)
def actualizar_co2(paises_selec):
    return fig_co2_comparacion(paises_selec)

@app.callback(
    Output("co2-pie-chart", "figure"),
    Input("dropdown-paises-pastel", "value")
)
def actualizar_pie(paises_selec):
    return fig_co2_pie(paises_selec)

# ==========================
# MAIN
# ==========================
if __name__=="__main__":
    app.run_server(debug=True)

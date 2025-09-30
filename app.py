# app.py
import pandas as pd
import dash
from dash import dcc, html, dash_table, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

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
    'coal': 0.99790,
    'oil': 0.95254,
    'natural gas': 0.40823,
    'hydro': 0.04536,
    'wind': 0.01361,
    'solar': 0.05670
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
        html.Img(src="/assets/Talento_Tech_Logo.png", style={"height": "60px"}),
        html.H1(
            "Colombia en transición: Retos y oportunidades de la matriz energética (2014-2022)",
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
    # Filtrar datos de Colombia y solo los productos relevantes
    productos_validos = ["Hydro", "Solar", "Wind", "Natural gas", "Oil", "Coal"]
    df_col = df[(df["COUNTRY"] == "Colombia") & (df["PRODUCT"].isin(productos_validos))]

    # Crear matriz: productos vs años con % (share * 100)
    df_pivot_share = df_col.pivot_table(
        index="PRODUCT",
        columns="YEAR",
        values="share",
        aggfunc="mean"
    ) * 100  # <-- convertir a porcentaje

    # Crear heatmap
    fig = px.imshow(
        df_pivot_share,
        labels=dict(x="Año", y="Fuente energética", color="Participación (%)"),
        x=df_pivot_share.columns,
        y=df_pivot_share.index,
        text_auto=".1f",  # Mostrar valores con un decimal
        aspect="auto",
        color_continuous_scale="YlGnBu"
    )

    # Mejorar layout
    fig.update_layout(
        title="Matriz energética anual en Colombia por fuente (2014-2050)",
        title_x=0.5,
        margin=dict(l=40, r=40, t=60, b=40),
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
# Pestaña 3: Problemática 2
# ==========================


def fig_line_matriz():
    # Filtrar solo Colombia
    df_col = df[df["COUNTRY"] == "Colombia"].copy()

    # Filtrar productos energéticos seleccionados
    productos_energia = ["Hydro", "Solar", "Wind", "Natural gas", "Oil", "Coal"]
    df_col_matrx = df_col[df_col["PRODUCT"].isin(productos_energia)]

    # Agrupar por año, mes y producto
    df_col_matrx = df_col_matrx.groupby(["YEAR", "MONTH", "PRODUCT"], as_index=False)["VALUE"].sum()

    # Crear columna TIME para el label del eje X
    df_col_matrx["TIME"] = pd.to_datetime(df_col_matrx[["YEAR", "MONTH"]].assign(day=1))
    df_col_matrx = df_col_matrx.sort_values(["TIME", "PRODUCT"])

    # Convertir TIME a formato legible para el eje X
    df_col_matrx["TIME_LABEL"] = df_col_matrx["TIME"].dt.strftime("%B %Y")  # Ej: "January 2014"

    # Crear gráfica de líneas
    fig = px.line(
        df_col_matrx,
        x="TIME_LABEL",
        y="VALUE",
        color="PRODUCT",
        markers=True,
        title="Generación por Fuente a lo largo de los Meses (Colombia)"
    )

    fig.update_layout(
        xaxis_title="Mes",
        yaxis_title="Generación (GWh)",
        legend_title="Fuente Energética",
        template="plotly_white",
        height=500
    )

    # Rotar etiquetas del eje X
    fig.update_xaxes(tickangle=90)

    return fig



def fig_generacion_fuentes_colombia():
    df_col = df[df["COUNTRY"] == "Colombia"]
    df_col_matrx = df_col[df_col["PRODUCT"].isin(['Hydro', 'Solar', 'Wind', 'Natural gas', 'Oil', 'Coal'])]

    pivot = df_col_matrx.groupby(['YEAR', 'PRODUCT'], as_index=False)['VALUE'].sum()

    fig = px.line(
        pivot,
        x="YEAR",
        y="VALUE",
        color="PRODUCT",
        markers=True,
        title="Generación por Fuente a lo largo de los Años (Colombia)"
    )

    fig.update_layout(
        xaxis_title="Año",
        yaxis_title="Generación (GWh)",
        template="plotly_white",
        height=500
    )
    return fig

def fig_hydro_share_comparacion(paises_sel):
    if not paises_sel:
        return go.Figure()

    df_sel = df[df["COUNTRY"].isin(paises_sel)]
    df_hydro = df_sel[df_sel["PRODUCT"] == "Hydro"].copy()

    if "share" not in df_hydro.columns:
        # Calcular participación (%) si no existe
        df_sel["total"] = df_sel.groupby(["COUNTRY", "YEAR"])["VALUE"].transform("sum")
        df_hydro["share"] = df_hydro["VALUE"] / df_hydro["total"] * 100

    df_combined_share = df_hydro.groupby(["COUNTRY", "YEAR"], as_index=False)["share"].sum()

    fig = px.line(
        df_combined_share,
        x="YEAR",
        y="share",
        color="COUNTRY",
        markers=True,
        title="Participación de energía Hidroeléctrica en la matriz energética",
        template="plotly_white"
    )

    fig.update_layout(
        xaxis_title="Año",
        yaxis_title="Participación (%)",
        template="plotly_white",
        height=500
    )
    return fig

# ==========================
# Pestaña 4: Problemática 3
# ==========================
def fig_co2_total_colombia():
    df_col_matrx = df[df["COUNTRY"] == "Colombia"]
    df_totprod_CO2 = df_col_matrx.groupby(['YEAR','COUNTRY'])['CO2_PRODUCTION'].sum().reset_index()

    fig = px.line(
        df_totprod_CO2,
        x="YEAR",
        y="CO2_PRODUCTION",
        markers=True,
        title="Producción total de CO₂ en Colombia por año",
        template="plotly_white"
    )
    fig.update_layout(
        xaxis_title="Año",
        yaxis_title="Toneladas de CO₂",
        title_x=0.5,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig

# headmap co2 colombia
def fig_heatmap_co2_colombia():
    df_col = df[df["COUNTRY"] == "Colombia"]
    products_order = ['Hydro', 'Solar', 'Wind', 'Natural gas', 'Oil', 'Coal']
    
    heatmap_co2 = (
        df_col[df_col["PRODUCT"].isin(products_order)]
        .groupby(['YEAR', 'PRODUCT'])['CO2_PRODUCTION']
        .sum()
        .reset_index()
    )
    
    pivot_co2 = heatmap_co2.pivot(index='PRODUCT', columns='YEAR', values='CO2_PRODUCTION')
    pivot_co2 = pivot_co2.loc[products_order]  # ordenamos las filas
    
    fig = px.imshow(
        pivot_co2.values,
        x=[str(c) for c in pivot_co2.columns],
        y=pivot_co2.index,
        text_auto=".0f",
        color_continuous_scale="Reds",
        aspect="auto",
        labels={"x": "Año", "y": "Fuente energética", "color": "Emisiones de CO₂ (ton)"},
        title="Emisiones anuales de CO₂ por fuente energética en Colombia (2014-2022)"
    )
    
    fig.update_layout(
        title_x=0.5,
        margin=dict(l=40, r=40, t=60, b=40),
        template="plotly_white"
    )
    
    return fig

# ==========================
# FUNCION DE SIMULACION (y figuras relacionadas)
# ==========================
def simular_reduccion_emisiones(aumento_pct=20):
    df_col = df[df["COUNTRY"] == "Colombia"].copy()

    # Filtrar solo desde 2015
    df_col = df_col[df_col["YEAR"] >= 2015]

    # Agrupar por año total emisiones CO2
    base = df_col.groupby("YEAR", as_index=False)["CO2_PRODUCTION"].sum()
    base.rename(columns={"CO2_PRODUCTION": "CO2_base"}, inplace=True)

    # Proyección simple hasta 2050 (crecimiento promedio anual)
    tasa_crec = (base["CO2_base"].iloc[-1] / base["CO2_base"].iloc[0])**(1/(len(base)-1)) - 1
    años_futuros = pd.DataFrame({"YEAR": list(range(base["YEAR"].max()+1, 2051))})
    años_futuros["CO2_base"] = base["CO2_base"].iloc[-1] * ((1+tasa_crec) ** (años_futuros["YEAR"]-base["YEAR"].max()))
    base = pd.concat([base, años_futuros], ignore_index=True)

    # Escenario simulado (solo esta línea)
    base["CO2_sim"] = base["CO2_base"] * (1 - aumento_pct/100)

    return base

def fig_simulacion():
    df_sim = simular_reduccion_emisiones(20)  # fijo en +20%
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_sim["YEAR"], y=df_sim["CO2_sim"],
        mode="lines+markers", name="Escenario Simulado"
    ))

    fig.update_layout(
        title="Proyección de emisiones CO₂ en Colombia (2015–2050) con +20% Solar/Eólica",
        xaxis_title="Año",
        yaxis_title="Emisiones CO₂ (ton)",
        template="plotly_white",
        title_x=0.5
    )
    return fig

def simular_impacto_co2_colombia(df, porcentaje_extra=0.2):
    """
    Simula el impacto de aumentar solar y eólica en Colombia en un porcentaje dado.
    porcentaje_extra: fracción a trasladar desde fósiles hacia solar/wind (ej. 0.2 = 20%)
    """
    df_col = df[df["COUNTRY"] == "Colombia"].copy()
    df_col = df_col[df_col["YEAR"].between(2014, 2022)]

    # ======================
    # Escenario real
    # ======================
    df_col["CO2_REAL"] = df_col.apply(
        lambda row: row["VALUE"] * COEF_MAP.get(row["PRODUCT"].lower(), 0), axis=1
    )
    real = df_col.groupby("YEAR")["CO2_REAL"].sum().reset_index()
    real["Escenario"] = "Real"

    # ======================
    # Escenario simulado
    # ======================
    simulado = df_col.copy()

    for year in simulado["YEAR"].unique():
        # Energía total fósil de ese año
        mask_fosil = simulado["PRODUCT"].isin(["Coal", "Oil", "Natural gas"])
        energia_fosil = simulado[(simulado["YEAR"] == year) & mask_fosil]["VALUE"].sum()

        # Extra que pasamos a renovables
        extra = energia_fosil * porcentaje_extra  

        # Reducir fósiles proporcionalmente
        for prod in ["Coal", "Oil", "Natural gas"]:
            mask = (simulado["YEAR"] == year) & (simulado["PRODUCT"] == prod)
            valor_actual = simulado.loc[mask, "VALUE"]
            if not valor_actual.empty:
                reduccion = valor_actual.values[0] * porcentaje_extra
                simulado.loc[mask, "VALUE"] -= reduccion

        # Aumentar solar y wind
        for prod in ["Solar", "Wind"]:
            mask = (simulado["YEAR"] == year) & (simulado["PRODUCT"] == prod)
            if not simulado[mask].empty:
                simulado.loc[mask, "VALUE"] += extra / 2
            else:
                simulado = pd.concat([
                    simulado,
                    pd.DataFrame([{
                        "COUNTRY": "Colombia",
                        "YEAR": year,
                        "PRODUCT": prod,
                        "VALUE": extra/2,
                        "CO2_PRODUCTION": 0
                    }])
                ])

    # Recalcular emisiones con COEF_MAP
    simulado["CO2_SIM"] = simulado.apply(
        lambda row: row["VALUE"] * COEF_MAP.get(row["PRODUCT"].lower(), 0), axis=1
    )

    sim = simulado.groupby("YEAR")["CO2_SIM"].sum().reset_index()
    sim["Escenario"] = "Simulado"

    # ======================
    # Comparar real vs simulado
    # ======================
    df_comp = pd.concat([
        real.rename(columns={"CO2_REAL": "CO2"}),
        sim.rename(columns={"CO2_SIM": "CO2"})
    ])
    return df_comp

def fig_impacto_co2_colombia(df, porcentaje_extra):
    df_comp = simular_impacto_co2_colombia(df, porcentaje_extra)

    fig = px.line(
        df_comp,
        x="YEAR",
        y="CO2",
        color="Escenario",
        markers=True,
        title=f"Impacto en CO₂ si Colombia aumentara Solar/Eólica en {int(porcentaje_extra*100)}%",
        template="plotly_white"
    )

    fig.update_layout(
        xaxis_title="Año",
        yaxis_title="Emisiones CO₂ (Ton)",
        title_x=0.5
    )
    return fig

def fig_heatmap_matriz():
    df_col = df[df["COUNTRY"] == "Colombia"].copy()
    df_col = df_col[df_col["PRODUCT"].isin(['Hydro', 'Solar', 'Wind', 'Natural gas', 'Oil', 'Coal'])]

    # Histórico
    heatmap_data = df_col.groupby(['YEAR', 'PRODUCT'], as_index=False)['share'].mean()

    # Años futuros
    años_futuros = range(heatmap_data["YEAR"].max()+1, 2051)
    proyecciones = []
    for prod in ['Hydro', 'Solar', 'Wind', 'Natural gas', 'Oil', 'Coal']:
        # último valor conocido de cada producto
        ultimo_valor = heatmap_data.loc[heatmap_data["PRODUCT"] == prod, "share"].iloc[-1]
        for año in años_futuros:
            proyecciones.append({"YEAR": año, "PRODUCT": prod, "share": ultimo_valor})

    df_futuro = pd.DataFrame(proyecciones)

    # Concatenar histórico + proyección
    df_hypothetical = pd.concat([heatmap_data, df_futuro], ignore_index=True)

    # Pivotear
    pivot_data = df_hypothetical.pivot(index='PRODUCT', columns='YEAR', values='share')

    # Heatmap con plotly
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale="YlGnBu",
        text=np.round(pivot_data.values, 4),
        texttemplate="%{text}",
        colorbar=dict(title="Producción (GWh)")
    ))

    fig.update_layout(
        title="Matriz energética anual en Colombia por fuente (2014–2050)",
        xaxis_title="Año",
        yaxis_title="Fuente energética",
        xaxis=dict(type="category"),
        title_x=0.5,
        template="plotly_white",
        height=500
    )
    return fig

# ==========================
# Pestaña 5: Problemática 4
# ==========================
def fig_renovables_comparacion(paises_sel):
    # Filtrar el dataframe por los países seleccionados en el dropdown
    df_selected = df[df['COUNTRY'].isin(paises_sel)]

    # Solo energías renovables
    df_selected = df_selected[df_selected['PRODUCT'].isin(['Hydro','Wind','Solar','Geothermal'])]

    # Calcular el aporte combinado de renovables
    df_combined_share = df_selected.groupby(['COUNTRY','YEAR'], as_index=False)['share'].sum()

    # Gráfica
    fig = px.line(
        df_combined_share,
        x="YEAR",
        y="share",
        color="COUNTRY",
        markers=True,
        title="Participación de energías renovables en la Matriz Energética por País",
        template="plotly_white"
    )

    fig.update_layout(
        xaxis_title="Año",
        yaxis_title="Participación (%)",
        title_x=0.5,
        margin=dict(l=40, r=40, t=60, b=40),
    )

    return fig


# ==========================
# FUNCIONES KPI 
# ==========================
def kpi_cards1():
    df_col = df[df["COUNTRY"] == "Colombia"].copy()

    # Filtrar solo productos energéticos
    productos_energia = ["Hydro", "Wind", "Solar", "Geothermal", "Natural gas", "Oil", "Coal"]
    renovables = ["Hydro", "Wind", "Solar", "Geothermal"]
    df_energia = df_col[df_col["PRODUCT"].isin(productos_energia)]

    # Agregar energía por año y producto (para evitar duplicados por mes)
    df_year_prod = df_energia.groupby(["YEAR", "PRODUCT"], as_index=False)["VALUE"].sum()

    # Total de energía producida (2014-2022)
    total_generacion = df_year_prod.groupby("YEAR")["VALUE"].sum().sum()

    # Total de renovables (Hydro, Wind, Solar, Geothermal)
    total_renovables = df_year_prod[df_year_prod["PRODUCT"].isin(renovables)]["VALUE"].sum()

    # Porcentaje renovables
    pct_renovables = (total_renovables / total_generacion * 100) if total_generacion > 0 else 0

    # Año de mayor y menor generación renovables (suma de todas las renovables por año)
    renovables_by_year = df_year_prod[df_year_prod["PRODUCT"].isin(renovables)].groupby("YEAR")["VALUE"].sum()

    año_max_renov = int(renovables_by_year.idxmax()) if not renovables_by_year.empty else "N/A"
    año_min_renov = int(renovables_by_year.idxmin()) if not renovables_by_year.empty else "N/A"

    return html.Div([
        html.Div([html.H4("Total Energía Producida (2014–2022)"), 
                  html.H3(f"{total_generacion:,.0f} GWh")], className="card"),
        
        html.Div([html.H4("Producción Total Renovables (2014–2022)"), 
                  html.H3(f"{total_renovables:,.0f} GWh")], className="card"),
        
        html.Div([html.H4("Participación Renovables en la Matriz"), 
                  html.H3(f"{pct_renovables:.1f}%")], className="card"),
        
        html.Div([html.H4("Año de Mayor Generación Renovables"), 
                  html.H3(f"{año_max_renov}")], className="card"),
        
        html.Div([html.H4("Año de Menor Generación Renovables"), 
                  html.H3(f"{año_min_renov}")], className="card"),
    ], className="row", style={"marginBottom": "20px"})

def kpi_cards2():
    df_col = df[df["COUNTRY"] == "Colombia"].copy()

    # Filtrar solo productos energéticos
    productos_energia = ["Hydro", "Wind", "Solar", "Geothermal", "Natural gas", "Oil", "Coal"]
    df_energia = df_col[df_col["PRODUCT"].isin(productos_energia)]

    # Agregar energía por año y producto (para evitar duplicados por mes)
    df_year_prod = df_energia.groupby(["YEAR", "PRODUCT"], as_index=False)["VALUE"].sum()

    # Total de energía producida (2014-2022)
    total_generacion = df_year_prod.groupby("YEAR")["VALUE"].sum().sum()

    # Total Hydro
    total_hydro = df_year_prod[df_year_prod["PRODUCT"] == "Hydro"]["VALUE"].sum()

    # Porcentaje Hydro
    pct_hydro = (total_hydro / total_generacion * 100) if total_generacion > 0 else 0

    # Año de mayor y menor generación Hydro
    hydro_by_year = df_year_prod[df_year_prod["PRODUCT"] == "Hydro"].set_index("YEAR")["VALUE"]
    año_max_hydro = int(hydro_by_year.idxmax()) if not hydro_by_year.empty else "N/A"
    año_min_hydro = int(hydro_by_year.idxmin()) if not hydro_by_year.empty else "N/A"

    return html.Div([
        html.Div([html.H4("Total Energía Producida (2014–2022)"), 
                  html.H3(f"{total_generacion:,.0f} GWh")], className="card"),
        
        html.Div([html.H4("Producción Total Hydro (2014–2022)"), 
                  html.H3(f"{total_hydro:,.0f} GWh")], className="card"),
        
        html.Div([html.H4("Participación Hydro en la Matriz"), 
                  html.H3(f"{pct_hydro:.1f}%")], className="card"),
        
        html.Div([html.H4("Año de Mayor Generación Hydro"), 
                  html.H3(f"{año_max_hydro}")], className="card"),
        
        html.Div([html.H4("Año de Menor Generación Hydro"), 
                  html.H3(f"{año_min_hydro}")], className="card"),
    ], className="row", style={"marginBottom": "20px"})

# ==========================
# COMMON STYLE CONSTANTS
# ==========================
table_header_style = {
    "backgroundColor": BANNER_COLOR,
    "color": "white",
    "fontWeight": "bold",
    "textTransform": "uppercase"
}

card_style = {
    "padding": "20px",
    "marginBottom": "20px",
    "boxSizing": "border-box"
}

flex_row_style = {
    "display": "flex",
    "gap": "20px",
    "marginBottom": "30px",
    "flexWrap": "wrap",
    "alignItems": "stretch"
}

full_width_card_style = {
    "width": "100%",
    "marginBottom": "30px",
    "padding": "10px"
}

# columnas que vamos a eliminar en la tabla de Colombia
cols_drop = ["CODE_TIME", "TIME", "DISPLAY_ORDER", "previousYearToDate", "yearToDate", "COEF"]
df_colombia = df[df["COUNTRY"] == "Colombia"].drop(columns=cols_drop, errors="ignore")

exploracion_layout = html.Div([
    html.H3("Motivo del proyecto:", style={"textAlign": "center", "marginBottom": "10px"}),     
    html.P(
        "Seleccionamos esta base de datos con el propósito de identificar la evolución y la participación relativa "
        "de las fuentes de energía (carbón, petróleo y gas natural) para Colombia entre los años 2014 y 2022, "
        "con el fin de reconocer tendencias, fortalezas y desafíos hacia una transición energética equilibrada "
        "para Colombia y compararlos en relación a otros países.",
        style={"textAlign": "justify", "marginBottom": "20px"}
    ),

    html.H3("Exploración del Dataset", style={"textAlign": "center", "marginBottom": "10px"}),

    # Dataset completo
    html.Div([
        html.H4("Dataset completo"),
        dash_table.DataTable(
            id="tabla-completa",
            data=df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in df.columns],
            page_size=10,
            style_table={"overflowX": "auto"},
            style_header=table_header_style,
            style_data_conditional=[{
                "if": {"row_index": "odd"},
                "backgroundColor": "#f9f9f9"
            }]
        )
    ], className="card"),
    # Estadísticas del dataset completo
    html.Div([
        html.H4("Estadísticas - Dataset completo"),
        dash_table.DataTable(
            id="tabla-estadisticas-completo",
            data=df.describe().reset_index().to_dict("records"),
            columns=[{"name": c, "id": c} for c in df.describe().reset_index().columns],
            page_size=20,
            style_table={"overflowX": "auto"},
            style_header=table_header_style,
        )
    ], className="card"),

    # Dataset Colombia (sin columnas irrelevantes)
    html.Div([
        html.H4("Dataset - Solo Colombia"),
        dash_table.DataTable(
            id="tabla-colombia",
            data=df_colombia.to_dict("records"),
            columns=[{"name": c, "id": c} for c in df_colombia.columns],
            page_size=10,
            style_table={"overflowX": "auto"},
            style_header=table_header_style,
        )
    ], className="card"),

    # Estadísticas de Colombia
    html.Div([
        html.H4("Estadísticas de Colombia"),
        dash_table.DataTable(
            id="tabla-estadisticas-colombia",
            data=df_colombia.describe().reset_index().to_dict("records"),
            columns=[{"name": c, "id": c} for c in df_colombia.describe().reset_index().columns],
            page_size=20,
            style_table={"overflowX": "auto"},
            style_header=table_header_style,
        )
    ], className="card"),
], style={"gap": "20px", "display": "flex", "flexDirection": "column"})


# ==========================
# TAB 2: PROBLEMÁTICA 1 (estilizada)
# ==========================
problem1_layout = html.Div([
    html.H3("¿Cómo ha evolucionado la matriz energética colombiana en los últimos 10 años y qué tan rezagada está en la adopción de energías limpias?",
            style={"textAlign": "center", "marginBottom": "20px"}),

    kpi_cards1(),

    # Fila 1: Matriz y Heatmap
    html.Div([
        html.Div([dcc.Graph(figure=fig_matriz_area_colombia())], className="card", style={"flex": "1"}),
        html.Div([dcc.Graph(figure=fig_heatmap_colombia())], className="card", style={"flex": "1"})
    ], style={"display": "flex", "gap": "20px", "marginBottom": "30px"}),

    # Fila 2: Solar vs Wind + Texto explicativo
    html.Div([
        html.Div([dcc.Graph(figure=fig_solar_wind_line())], className="card", style={"flex": "1"}),
        html.Div([
            html.H4("Conclusiones de la matriz energética en Colombia"),
            html.H5("1. Matriz energética Colombia 2014-2022"),
            html.P("Entre 2014 y 2022, la matriz energética colombiana se mantuvo fuertemente concentrada en la energía hidroeléctrica (60–70%) " \
            "y en combustibles fósiles (carbón, petróleo y gas natural). A pesar del incremento reciente de la energía solar, su aporte, junto con " \
            "el de la eólica, continúa siendo marginal frente al total."),
            html.H5("2. Vulnerabilidad frente al cambio climático"),
            html.P("La alta participación de la hidroeléctrica convierte al sistema en vulnerable a fenómenos como El Niño, que provocan caídas " \
            "significativas en la generación. En estos periodos, la dependencia de fuentes fósiles aumenta, lo que no solo reduce la seguridad " \
            "energética, sino que incrementa las emisiones de CO₂."),
            html.H4("Recomendaciones de la matriz energética en Colombia"),
            html.H5("1. Matriz energética Colombia 2014-2022"),
            html.P("Entre 2014 y 2022, la matriz energética colombiana se mantuvo fuertemente concentrada en la energía hidroeléctrica (60–70%) " \
            "y en combustibles fósiles (carbón, petróleo y gas natural). A pesar del incremento reciente de la energía solar, su aporte, junto con " \
            "el de la eólica, continúa siendo marginal frente al total."),
            html.H5("2. Vulnerabilidad frente al cambio climático"),
            html.P("La alta participación de la hidroeléctrica convierte al sistema en vulnerable a fenómenos como El Niño, que provocan caídas " \
            "significativas en la generación. En estos periodos, la dependencia de fuentes fósiles aumenta, lo que no solo reduce la seguridad " \
            "energética, sino que incrementa las emisiones de CO₂.")
        ], className="card", style={"flex": "1", "textAlign": "justify", "padding": "20px"}),
    ], style={"display": "flex", "gap": "20px"})
])

# ==========================
# TAB 3: PROBLEMÁTICA 2 (estilizada)
# ==========================
problem2_layout = html.Div([
    # Título principal
    html.H3(
        "¿Qué tan riesgosa es la sobredependencia de hidro comparada con otros países y qué alternativas energéticas se han explorado?",
        style={"textAlign": "center", "marginBottom": "20px"}
    ),

    # KPIs
    kpi_cards2(),

    # Gráfica de línea matriz energética
    html.Div([dcc.Graph(figure=fig_line_matriz())],
             className="card",
             style=full_width_card_style),
    html.Div([  # Primera gráfica
            html.H3("Generación años por fuente en Colombia (2014-2022)"),
            dcc.Graph(figure=fig_generacion_fuentes_colombia())
        ], className="card", style={"flex": "1"}),
    html.Div([  # Segunda gráfica
            html.H3("Comparación participación hidroeléctrica", style={"marginTop": "0px"}),
            dcc.Dropdown(
                id="dropdown-hydro-paises",
                options=[{"label": p, "value": p} for p in paises],
                value=["Colombia", "Argentina", "Brazil", "Chile"],
                multi=True,
                style={'width': '95%', 'margin': '10px auto', 'maxWidth': '400px'}
            ),
            dcc.Graph(id="hydro-share-comparacion")
        ], className="card", style={"flex": "1"}),
    # Conclusiones y Recomendaciones
    html.Div([
        html.Div([  # Conclusiones
            html.H4("Conclusiones Problemática 2"),
            html.H5("Energías renovables no convencionales con avances desiguales"),
            html.P(
                "La energía solar mostró un crecimiento acelerado desde 2018, superando en pocos años los 450 GWh. "
                "En contraste, la eólica se mantuvo estancada por limitaciones estructurales y logísticas, "
                "a pesar del alto potencial en regiones como La Guajira. Esto refleja una asimetría en el desarrollo "
                "de energías renovables no convencionales en el país."
            ),
        ], className="card", style={"flex": "1", "textAlign": "justify", "padding": "20px"}),

        html.Div([  # Recomendaciones
            html.H4("Recomendaciones Problemática 2"),
            html.H5("1. Alianzas regionales e internacionales"),
            html.P(
                "Aprovechar experiencias exitosas de países como Chile, Dinamarca o Costa Rica para adaptar buenas prácticas "
                "regulatorias y tecnológicas que aceleren la transición energética en Colombia."
            ),
            html.H5("2. Impulso a proyectos eólicos en regiones estratégicas"),
            html.P(
                "Superar barreras sociales, logísticas y ambientales en zonas de alto potencial, como La Guajira, "
                "mediante procesos de concertación con comunidades locales, infraestructura adecuada y marcos normativos claros."
            )
        ], className="card", style={"flex": "1", "textAlign": "justify", "padding": "20px"}),
    ],
        style={"display": "flex", "gap": "20px", "marginBottom": "20px"}
    )
],
    style={"display": "flex", "flexDirection": "column", "gap": "15px"}
)


# ==========================
# TAB 4: PROBLEMÁTICA 3 (estilizada)
# ==========================
problem3_layout = html.Div([
    html.H3("¿Cuál sería el impacto en reducción de emisiones si Colombia aumenta su participación solar/eólica en un 20%?", style={"textAlign": "center", "marginBottom": "20px"}),

    html.Div([
        html.Div([
            html.H4("1. Conclusiones Problemática 3"),
            html.H5("Impacto en emisiones de CO₂"),
            html.P("Aunque Colombia presenta menores niveles de emisiones en comparación con otros países de la región, los picos de CO₂ coinciden con caídas en la generación hidroeléctrica " \
            "y mayor uso de fósiles. Las simulaciones sugieren que un aumento sostenido en la participación de solar y eólica reduciría significativamente las emisiones y mejoraría la resiliencia " \
            "de la matriz, esto va muy en concordancia con los planes de la transición energética justa que plantea el actual gobierno."),
            html.H4("2. Recomendaciones Problemática 3"),
            html.H5("Investigación, desarrollo e innovación (I+D+i)"),
            html.P("Fomentar proyectos de investigación en energías renovables, almacenamiento y tecnologías emergentes (como geotermia e hidrógeno verde), con participación de universidades, " \
            "centros de investigación y el sector privado.")
            ], className="card", style={"flex": "1",  "textAlign": "justify", "padding": "20px"}
        ),
        html.Div([dcc.Graph(figure=fig_heatmap_co2_colombia())], className="card", style={"flex": "1"})
    ], style={"display": "flex", "gap": "20px", "marginBottom": "20px"}),
    html.Div([
        html.H3("Análisis de CO₂ por país"),
        dcc.Dropdown(
            id="dropdown-paises-unico",
            options=[{"label": p, "value": p} for p in paises],
            value=["Colombia"],
            multi=True,
            style={'width': '60%', 'margin': '10px auto'}
        ),
        html.Div([
            html.Div([dcc.Graph(id="co2-comparacion")], className="card", style={"flex": "1"}),
            html.Div([dcc.Graph(id="co2-pie-chart")], className="card", style={"flex": "1"})
        ], style={"display": "flex", "gap": "20px"})
    ], className="card"),

    
    html.Div([
        html.H3("Simulación de reducción de emisiones", style={"marginTop": "30px"}),
        dcc.Graph(figure=fig_simulacion())], className="card"),

    
    html.Div([
        html.H3("Matriz energética anual en Colombia (2014–2050)", style={"marginTop": "30px"}),
        dcc.Graph(figure=fig_heatmap_matriz())], className="card"),

], style={"display": "flex", "flexDirection": "column", "gap": "15px"})

# ==========================
# TAB 5: PROBLEMÁTICA 4 
# ==========================
problem4_layout = html.Div([
    html.H3(
        "¿Dónde se ubica Colombia en la transición energética regional y qué factores explican su rezago o avance?",
        style={"textAlign": "center", "marginBottom": "20px"}
    ),
    
    # Dropdown y gráfica principal
    html.Div([
        html.Div([
            html.Label("Selecciona los países:"),
            html.Div(
                dcc.Dropdown(
                    id="dropdown-renovables-paises",
                    options=[{"label": p, "value": p} for p in sorted(df["COUNTRY"].unique())],
                    value=["Colombia", 'Argentina', 'Brazil', 'Canada', 'Chile',
                        'Costa Rica', 'Mexico', 'United States'],
                    multi=True,
                    style={'minWidth': '300px'}
                ),
                style={
                    "display": "flex",       # cambia inline-flex a flex
                    "flexWrap": "wrap",      # permite que los tags vayan a la siguiente línea
                    "justifyContent": "center",
                    "width": "80%",
                    "margin": "10px auto"
                }
            ),
            dcc.Graph(id="graph-renovables-comparacion")
        ], className="card", style={"padding": "20px", "marginBottom": "20px"})
    ]),

    
    # Conclusiones y recomendaciones
    html.Div([
        html.Div([
            html.H4("Conclusiones Problemática 4"),
            html.H5("Oportunidades hacia la transición energética"),
            html.P(
                "El país tiene un potencial considerable para expandir el uso de fuentes renovables no convencionales, "
                "lo cual permitiría reducir riesgos climáticos, diversificar la oferta, garantizar mayor seguridad energética "
                "y contribuir a las metas de descarbonización. Sin embargo, el avance depende de superar barreras regulatorias, "
                "logísticas y de inversión que actualmente limitan su desarrollo."
            )
        ], className="card", style={"flex": "1", "textAlign": "justify", "padding": "20px"}),

        html.Div([
            html.H4("Recomendaciones Problemática 4"),
            html.H5("Revisión de datos más actuales"),
            html.P(
                "Es importante corroborar los datos de esta entidad internacional con los que posee el gobierno, para "
                "corroborar que no haya información faltante y además completar con datos de 2023 a 2025 para ver cómo se "
                "está llevando a cabo la transición. Continuar alimentando esta base de datos para poder tomar decisiones "
                "sobre la marcha en la implementación de energías renovables no convencionales en la transición justa y "
                "camino a la descarbonización."
            )
        ], className="card", style={"flex": "1", "textAlign": "justify", "padding": "20px"})
    ], style={"display": "flex", "gap": "20px", "marginBottom": "20px"})
], style={"display": "flex", "flexDirection": "column", "gap": "15px"})


# ==========================
# FOOTER
# ==========================
# ==========================
# FOOTER
# ==========================
footer = html.Div(
    style={
        "backgroundColor": "white",
        "marginTop": "30px",
        "padding": "0",
        "borderTop": f"4px solid {BANNER_COLOR}",
        "boxShadow": "0 -2px 6px rgba(0,0,0,0.1)",
    },
    children=[
        # Encabezado con fondo azul
        html.Div(
            "Autores",
            style={
                "backgroundColor": BANNER_COLOR,
                "color": "white",
                "padding": "10px",
                "fontWeight": "bold",
                "fontSize": "18px",
                "textAlign": "center",
            },
        ),

        # Sección blanca con contenido
        html.Div(
            children=[
                html.H1(
                    "Juan Manuel Urbano Torres | Juan Miguel Elejalde García | Yicely Díaz Tapias",
                    style={"color": "black", "textAlign": "center", "flex": "1", "margin": "0"}
                ),
                html.Div(
                    [
                        html.Img(src="/assets/UTraining.png", style={"height": "60px", "margin": "0 20px"}),
                        html.Img(src="/assets/udea.png", style={"height": "60px", "margin": "0 20px"}),
                        html.Img(src="/assets/udecaldas.png", style={"height": "100px", "margin": "0 20px"}),
                        html.Img(src="/assets/ubicua.png", style={"height": "90px", "margin": "0 20px"}),
                    ],
                    style={"display": "flex", "justifyContent": "center", "alignItems": "center"},
                ),
            ],
            style={"padding": "20px", "textAlign": "center"},
        ),
    ],
)


# ==========================
# LAYOUT PRINCIPAL 
# ==========================
app.layout = html.Div([
    banner,
    html.Div(
        dcc.Tabs(
            id="tabs",
            value="tab1",
            children=[
                dcc.Tab(label="Exploración", value="tab1", className="tab", selected_className="tab--selected"),
                dcc.Tab(label="Problemática 1", value="tab2", className="tab", selected_className="tab--selected"),
                dcc.Tab(label="Problemática 2", value="tab3", className="tab", selected_className="tab--selected"),
                dcc.Tab(label="Problemática 3", value="tab4", className="tab", selected_className="tab--selected"),
                dcc.Tab(label="Problemática 4", value="tab5", className="tab", selected_className="tab--selected"),
            ]
        ),
        style={"width": "95%", "margin": "20px auto"}
    ),
    html.Div(id="tabs-content", style={"width": "95%", "margin": "0 auto 60px auto"}),
    footer
])

# ==========================
# CALLBACKS DE NAVEGACIÓN (igual que antes)
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
# CALLBACKS GRÁFICAS (sin cambios)
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

@app.callback(
    Output("hydro-share-comparacion", "figure"),
    Input("dropdown-hydro-paises", "value")
)
def actualizar_hydro_share(paises_sel):
    return fig_hydro_share_comparacion(paises_sel)

# ==========================
# CALLBACK DE SIMULACION
# ==========================
@app.callback(
    Output("grafico-impacto-co2", "figure"),
    Input("slider-renovables", "value")
)
def actualizar_simulacion(porcentaje_extra):
    return fig_impacto_co2_colombia(df, porcentaje_extra)

@app.callback(
    Output("graph-renovables-comparacion", "figure"),
    Input("dropdown-renovables-paises", "value")
)
def actualizar_grafico_renovables(paises_sel):
    return fig_renovables_comparacion(paises_sel)

# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    app.run_server(debug=True)

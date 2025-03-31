import streamlit as st
import pandas as pd
import plotly.express as px
import geopandas as gpd
import glob
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# ---------------------------
# Cargar datos
# ---------------------------
@st.cache_data
def cargar_datos():
    return pd.read_excel("bbdd/base_total_homologada.xlsx")

@st.cache_data
def cargar_geojson_regiones():
    geojson_files = glob.glob("comunas_geojson/R*.geojson")
    comunas = gpd.GeoDataFrame(pd.concat(
        [gpd.read_file(f) for f in geojson_files], ignore_index=True
    ))
    comunas["REGION"] = comunas["REGION"].astype(str).str.zfill(2)
    regiones = comunas.dissolve(by="REGION", as_index=False)
    return regiones

base_total = cargar_datos()
regiones = cargar_geojson_regiones()

# ---------------------------
# Limpieza de datos base
# ---------------------------
base_total["ANIO"] = pd.to_numeric(base_total["ANIO"], errors="coerce")
base_total["ANIO"] = base_total["ANIO"].fillna(0).astype(int)
base_total = base_total[base_total["ANIO"].isin([2023, 2024, 2025])].copy()
base_total["CODIGO_REGION"] = pd.to_numeric(base_total["CODIGO_REGION"], errors="coerce").astype("Int64")

# ---------------------------
# Logo superior
# ---------------------------
st.image("assets/logo_udec.png", width=250)

# ---------------------------
# Sidebar
# ---------------------------
st.sidebar.title("🎓 Filtros")

carreras_disponibles = sorted(base_total["CARRERA"].dropna().unique())
carreras_seleccionadas = st.sidebar.multiselect(
    "Selecciona carreras para comparar (afecta todos los gráficos)",
    options=carreras_disponibles,
    default=["Sociología", "Medicina", "Derecho"]
)

regiones_disponibles = sorted(base_total["CODIGO_REGION"].dropna().unique())
region_seleccionada = st.sidebar.selectbox("Selecciona una región", regiones_disponibles)

waffle_carreras = carreras_seleccionadas

# ---------------------------
# Tabs del dashboard
# ---------------------------
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📘 Introducción",
    "📈 Puntaje por Carrera",
    "🗺️ Estudiantes por Región (2025)",
    "📊 Sexo",
    "🎟️ Ingreso",
    "🏫 Establecimiento"
])


# ---------------------------
# Tab 0: Introducción
# ---------------------------
with tab0:
    st.title("📘 Introducción")
    st.markdown("""
    Bienvenido/a al **Dashboard PAES – Universidad de Concepción**.
    
    Este panel permite explorar información sobre:
    
    - Evolución del puntaje ponderado promedio por carrera.
    - Distribución de estudiantes por región (Año 2025).
    - Diferencias por sexo, dependencia e ingreso.
    - Origen escolar de estudiantes (por región).
    
    Los datos corresponden a las admisiones **2023, 2024 y 2025**.
    """)

# ---------------------------
# Tab 1: Puntaje por carrera
# ---------------------------
with tab1:
    st.header("Tendencia del Puntaje Promedio PAES por Carrera")
    df_puntaje = base_total[base_total["CARRERA"].isin(carreras_seleccionadas)].copy()
    df_linea = df_puntaje.groupby(["ANIO", "CARRERA"])["PTJE_PONDERADO"].mean().reset_index()

    fig_linea = px.line(
        df_linea,
        x="ANIO", y="PTJE_PONDERADO", color="CARRERA",
        markers=True,
        labels={"PTJE_PONDERADO": "Puntaje Promedio", "ANIO": "Año"},
        title="Tendencia Puntaje Promedio por Carrera"
    )
    fig_linea.update_layout(yaxis=dict(range=[500, 1000]))
    st.plotly_chart(fig_linea, use_container_width=True)

    st.subheader("Promedio de Puntaje por Sexo y Año")
    df_barras = base_total.groupby(["ANIO", "SEXO"])["PTJE_PONDERADO"].mean().reset_index()
    fig_barras = px.bar(
        df_barras,
        x="ANIO", y="PTJE_PONDERADO", color="SEXO",
        barmode="group", text_auto=".1f",
        title="Promedio Puntaje Ponderado PAES por Sexo"
    )
    fig_barras.update_layout(yaxis=dict(range=[500, 1000]))
    st.plotly_chart(fig_barras, use_container_width=True)

# ---------------------------
# Tab 2: Mapa por región (2025)
# ---------------------------
with tab2:
    st.header("Estudiantes por Región (2025)")
    base_2025 = base_total[base_total["ANIO"] == 2025].copy()
    base_2025["CODIGO_REGION"] = base_2025["CODIGO_REGION"].astype(str).str.zfill(2)
    base_2025["n"] = 1

    region_count = base_2025.groupby("CODIGO_REGION")["n"].sum().reset_index(name="N_ESTUDIANTES")
    gdf_regiones = regiones.merge(region_count, left_on="REGION", right_on="CODIGO_REGION", how="left")
    gdf_regiones["N_ESTUDIANTES"] = gdf_regiones["N_ESTUDIANTES"].fillna(0)
    geojson_regiones = gdf_regiones.__geo_interface__

    fig_mapa = px.choropleth_mapbox(
        gdf_regiones,
        geojson=geojson_regiones,
        locations=gdf_regiones.index,
        color="N_ESTUDIANTES",
        mapbox_style="carto-positron",
        zoom=4,
        center={"lat": -35.5, "lon": -71.5},
        color_continuous_scale="Blues",
        title="Estudiantes por Región – Año 2025"
    )
    fig_mapa.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
    st.plotly_chart(fig_mapa, use_container_width=True)

# ---------------------------
# Tab 3: Sexo (con waffle)
# ---------------------------
with tab3:
    st.header("Proporción de Postulantes por Sexo")
    df_sexo = base_total[base_total["CARRERA"].isin(carreras_seleccionadas)].copy()
    df_n = df_sexo.groupby(["ANIO", "SEXO", "CARRERA"]).size().reset_index(name="N")
    df_n["TOTAL"] = df_n.groupby(["ANIO", "CARRERA"])["N"].transform("sum")
    df_n["PROPORCION"] = df_n["N"] / df_n["TOTAL"]

    fig_facet = px.line(
        df_n,
        x="ANIO", y="PROPORCION", color="SEXO",
        facet_col="CARRERA", facet_col_wrap=2,
        markers=True
    )
    fig_facet.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig_facet, use_container_width=True)

    st.subheader("Distribución tipo Waffle")
    df_filtrado = base_total[base_total["CARRERA"].isin(waffle_carreras)].copy()
    df_filtrado["ANIO"] = df_filtrado["ANIO"].astype(str)
    df_n = df_filtrado.groupby(["ANIO", "SEXO", "CARRERA"]).size().reset_index(name="N")
    df_n["TOTAL"] = df_n.groupby(["ANIO", "CARRERA"])["N"].transform("sum")
    df_n["PROPORCION"] = df_n["N"] / df_n["TOTAL"]

    waffle_data = []
    rows, cols = 5, 20
    for (anio, carrera), group in df_n.groupby(["ANIO", "CARRERA"]):
        blocks = []
        for _, row in group.iterrows():
            count = int(round(row["PROPORCION"] * rows * cols))
            blocks.extend([str(row["SEXO"]) for _ in range(count)])
        blocks = blocks[:rows * cols]
        x = [i % cols for i in range(len(blocks))]
        y = [-(i // cols) for i in range(len(blocks))]
        waffle_df = pd.DataFrame({"x": x, "y": y, "SEXO": blocks})
        waffle_df["ANIO"] = anio
        waffle_df["CARRERA"] = carrera
        waffle_data.append(waffle_df)

    df_waffle = pd.concat(waffle_data, ignore_index=True)
    fig = px.scatter(df_waffle, x="x", y="y", color="SEXO", facet_col="ANIO", facet_col_wrap=2)
    fig.update_traces(marker=dict(size=12))
    fig.update_layout(showlegend=True, height=400)
    fig.for_each_xaxis(lambda ax: ax.update(showticklabels=False))
    fig.for_each_yaxis(lambda ax: ax.update(showticklabels=False))
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Tab 4: Ingreso (dependencia + ingreso)
# ---------------------------
with tab4:
    st.header("Matrícula por Grupo de Dependencia e Ingreso")
    df_dep = base_total.groupby(["ANIO", "GRUPO_DEPENDENCIA_EST"]).size().reset_index(name="N_ESTUDIANTES")
    fig_dep = px.line(df_dep, x="ANIO", y="N_ESTUDIANTES", color="GRUPO_DEPENDENCIA_EST", markers=True)
    st.plotly_chart(fig_dep, use_container_width=True)

    st.subheader("Distribución por Tipo de Ingreso (2025)")
    base_2025 = base_total[base_total["ANIO"] == 2025].copy()
    fig_torta = px.pie(base_2025, names="INGRESO", hole=0.3)
    fig_torta.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_torta, use_container_width=True)

# ---------------------------
# Tab 5: Establecimiento
# ---------------------------
with tab5:
    st.header("Colegios de Egreso por Región")
    region_data = base_total[base_total["CODIGO_REGION"] == region_seleccionada].copy()

    top_colegios = (
        region_data["NOMBRE_COLEGIO_EGRESO"].value_counts().head(30).reset_index()
    )
    top_colegios.columns = ["NOMBRE_COLEGIO_EGRESO", "N_ESTUDIANTES"]

    fig_bar = px.bar(
        top_colegios,
        x="N_ESTUDIANTES",
        y="NOMBRE_COLEGIO_EGRESO",
        orientation="h"
    )
    fig_bar.update_layout(yaxis=dict(categoryorder='total ascending'))
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Nube de Palabras de Colegios")
    texto = " ".join(region_data["NOMBRE_COLEGIO_EGRESO"].dropna().astype(str))
    wordcloud = WordCloud(width=1000, height=500, background_color="white").generate(texto)
    fig_wc, ax = plt.subplots(figsize=(15, 7))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig_wc)


#streamlit run app.py
# return pd.read_excel("bbdd/base_total_homologada.xlsx")
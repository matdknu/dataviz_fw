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

@st.cache_data
def cargar_datos():
    return pd.read_excel("bbdd/base_total_homologada.xlsx")

base_total = cargar_datos()

# ---------------------------
# Limpieza y transformación inicial
# ---------------------------
base_total["ANIO"] = pd.to_numeric(base_total["ANIO"], errors="coerce").fillna(0).astype(int)
base_total = base_total[base_total["ANIO"].isin([2023, 2024, 2025])].copy()
base_total["CODIGO_REGION"] = pd.to_numeric(base_total["CODIGO_REGION"], errors="coerce").astype("Int64")

# ---------------------------
# Definición de base_2025 (una sola vez para todo el dashboard)
# ---------------------------
base_2025 = base_total[base_total["ANIO"] == 2025].copy()

# Diccionario: código → nombre oficial de región
diccionario_regiones = {
    "01": "Tarapacá",
    "02": "Antofagasta",
    "03": "Atacama",
    "04": "Coquimbo",
    "05": "Valparaíso",
    "06": "O'Higgins",
    "07": "Maule",
    "08": "Biobío",
    "09": "La Araucanía",
    "10": "Los Lagos",
    "11": "Aysén",
    "12": "Magallanes",
    "13": "Metropolitana",
    "14": "Los Ríos",
    "15": "Arica y Parinacota",
    "16": "Ñuble",
    "17": "Los Andes"
}



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

# Establecer 8 como región seleccionada por defecto
if 8 in regiones_disponibles:
    default_index = regiones_disponibles.index(8)
else:
    default_index = 0  # por si no está la 8, usar la primera

region_seleccionada = st.sidebar.selectbox(
    "Selecciona una región",
    opciones := regiones_disponibles,
    index=default_index
)


# ---------------------------
# Tabs del dashboard
# ---------------------------

tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📘 Introducción",
    "📈 Puntaje por Carrera",
    "🗺️ Estudiantes por Región (2025)",
    "📊 Sexo",
    "🎟️ Grupo dependencia",
    "🧪 Tipo de ingreso ",
    "🏫 Establecimiento"
])



# --------------------------
# Tab 0: Introducción
# ---------------------------

with tab0:

    # Título y GIF
    st.markdown("""
    <div style='text-align: center;'>
        <h1 style='font-size: 2.5em;'>📘 Bienvenido/a al Dashboard PAES</h1>
        <h3 style='color: #004fa3;'>Universidad de Concepción</h3>
        <img src='https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExY2VoNDZ0a2JmeGt4em1sbHpjcnNudXBvdXY0OHE3ZWs5c3NsNWoxcCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/hZE5xoaM0Oxw4xiqH7/giphy.gif' 
             width='500' style='margin-top: 10px; border-radius: 12px;'>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <br>
    <div style='font-size: 1.1em; line-height: 1.6;'>
        Este panel interactivo permite explorar información sobre:
        <ul>
            <li>📈 Evolución del <strong>puntaje ponderado promedio</strong> por carrera.</li>
            <li>🗺️ Distribución de estudiantes por <strong>región</strong> (Año 2025).</li>
            <li>⚧️ Diferencias por <strong>sexo</strong>, <strong>tipo de dependencia</strong> e <strong>ingreso</strong>.</li>
            <li>🏫 Origen escolar de estudiantes (por región).</li>
        </ul>
        <p>Los datos corresponden a las admisiones <strong>2023, 2024 y 2025</strong>.</p>
    </div>
    """, unsafe_allow_html=True)

    # Equipo técnico
    st.markdown("""---""")
    st.markdown("""
    **Equipo técnico:**
    - 👩‍💻 [Javiera Baeza – Ingeniera Civil Biomédica](https://www.linkedin.com/in/javiera-baeza-acuña-378458216/)
    - 🧑‍💼 [Matías Deneken – Sociólogo](https://www.linkedin.com/in/deneken/)
    - 👩‍💼 [Florencia Pampaloni – Ingeniera Comercial](https://www.linkedin.com/in/florencia-pampaloni-benítez/)
    """)

    # Código abierto
    st.markdown("""---""")
    st.markdown(
        """
        <div style="text-align: center; font-size: 0.9em; margin-top: 30px;">
            🛠️ Este dashboard es <strong>código abierto</strong>.<br>
            <a href="https://github.com/matdknu/dataviz_fw" target="_blank" style="text-decoration: none;">
                <img src="https://cdn-icons-png.flaticon.com/512/25/25231.png" alt="GitHub" width="20" style="vertical-align: middle; margin-right: 5px;">
                Ver repositorio en GitHub
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )



# ---------------------------
# Tab 1: Puntaje por carrera
# ---------------------------
with tab1:
    st.header("Tendencia del Puntaje Promedio PAES por Carrera") 
    st.markdown("""
    Este gráfico muestra el **puntaje promedio PAES por carrera** de los dos test obligatorios:  
    - **Matemáticas 1**  
    - **Comprensión Lectora**
    """)

    df_puntaje = base_total[base_total["CARRERA"].isin(carreras_seleccionadas)].copy()
    df_linea = df_puntaje.groupby(["ANIO", "CARRERA"])["PTJE_PONDERADO"].mean().reset_index()

    fig_linea = px.line(
        df_linea,
        x="ANIO", y="PTJE_PONDERADO", color="CARRERA",
        markers=True,
        labels={"PTJE_PONDERADO": "Puntaje Promedio", "ANIO": "Año"},
        title="Tendencia Puntaje Promedio por Carrera"
    )
    fig_linea.update_layout(
        yaxis=dict(range=[500, 1000]),
        xaxis=dict(tickmode='array', tickvals=[2023, 2024, 2025])
    )
    st.plotly_chart(fig_linea, use_container_width=True)

    # ---------------------------
    # Segundo gráfico: promedio por sexo
    # ---------------------------
    st.subheader("Promedio de Puntaje por Sexo y Año")
    st.markdown("""
    Este gráfico muestra la **tendencia del puntaje ponderado PAES** de hombres y mujeres en el periodo 2023 a 2025.  
    En general, no se constatan diferencias significativas entre los promedios de ambos grupos.
    """)

    df_barras = base_total.groupby(["ANIO", "SEXO"])["PTJE_PONDERADO"].mean().reset_index()

    # Asegurar orden de categorías
    df_barras["SEXO"] = pd.Categorical(df_barras["SEXO"], categories=["MASCULINO", "FEMENINO"], ordered=True)

    fig_barras = px.bar(
        df_barras,
        x="ANIO", y="PTJE_PONDERADO", color="SEXO",
        barmode="group", text_auto=".1f",
        title="Promedio Puntaje Ponderado PAES por Sexo",
        color_discrete_map={
            "MASCULINO": "#2C8DC5",
            "FEMENINO": "#A040AC"
        },
        labels={
            "ANIO": "Año",
            "PTJE_PONDERADO": "Puntaje Promedio",
            "SEXO": "Sexo"
        }
    )

    fig_barras.update_layout(
        yaxis=dict(range=[500, 1000]),
        xaxis=dict(tickmode='array', tickvals=[2023, 2024, 2025]),
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center")  # leyenda abajo
    )

    st.plotly_chart(fig_barras, use_container_width=True)


# ---------------------------
# Tab 2: Mapa y barras por región (2025)
# ---------------------------
with tab2:
    st.header("Estudiantes por Región (2025)")

    base_2025_map = base_total[base_total["ANIO"] == 2025].copy()
    base_2025_map["CODIGO_REGION"] = base_2025_map["CODIGO_REGION"].astype(str).str.zfill(2)
    base_2025_map["n"] = 1

    region_count = base_2025_map.groupby("CODIGO_REGION")["n"].sum().reset_index(name="N_ESTUDIANTES")
    region_count["NOMBRE_REGION"] = region_count["CODIGO_REGION"].map(diccionario_regiones).fillna(region_count["CODIGO_REGION"])

    gdf_regiones = regiones.merge(region_count, left_on="REGION", right_on="CODIGO_REGION", how="left")
    gdf_regiones["N_ESTUDIANTES"] = gdf_regiones["N_ESTUDIANTES"].fillna(0)
    gdf_regiones["NOMBRE_REGION"] = gdf_regiones["CODIGO_REGION"].map(diccionario_regiones).fillna(gdf_regiones["CODIGO_REGION"])

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
    fig_mapa.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
    st.plotly_chart(fig_mapa, use_container_width=True)

    # ---------------------------
    # Gráfico de barras por región
    # ---------------------------
    st.subheader("Distribución de Estudiantes por Región (2025)")

    region_count_sorted = region_count.sort_values("N_ESTUDIANTES", ascending=False)

    fig_barras_region = px.bar(
        region_count_sorted,
        x="NOMBRE_REGION",
        y="N_ESTUDIANTES",
        text_auto=True,
        labels={"NOMBRE_REGION": "Región", "N_ESTUDIANTES": "Cantidad de Estudiantes"},
        title="Cantidad de Estudiantes por Región (2025)"
    )

    fig_barras_region.update_layout(
        xaxis_title="Región",
        yaxis_title="Cantidad de Estudiantes",
        margin=dict(t=40, b=20),
        template="simple_white"
    )

    st.plotly_chart(fig_barras_region, use_container_width=True)


# ---------------------------
# Tab 3: Sexo (stacked bar + boxplot)
# ---------------------------
with tab3:
    st.header("📊 Proporción de Postulantes por Sexo")

    st.markdown("""
    Este panel permite analizar las **diferencias por sexo** entre los postulantes a distintas carreras durante los años 2023, 2024 y 2025.

    ### 📘 Gráfico 1: Proporción de estudiantes por sexo (stacked)
    Cada barra representa el 100% de postulantes a una carrera en un año específico.  
    
    El objetivo es visualizar la distribución relativa por sexo en cada caso.

    ---
    """)

    # Base común
    df_sexo = base_total[base_total["CARRERA"].isin(carreras_seleccionadas)].copy()

    # ==============================
    # Gráfico 1: Stacked bar por proporción
    # ==============================
    df_n = df_sexo.groupby(["ANIO", "SEXO", "CARRERA"]).size().reset_index(name="N")
    df_n["TOTAL"] = df_n.groupby(["ANIO", "CARRERA"])["N"].transform("sum")
    df_n["PROPORCION"] = df_n["N"] / df_n["TOTAL"]
    df_n["TEXTO"] = (df_n["PROPORCION"] * 100).round(1).astype(str) + "%"

    # Orden personalizado: Masculino abajo
    df_n["SEXO"] = pd.Categorical(df_n["SEXO"], categories=["MASCULINO", "FEMENINO"], ordered=True)
    df_n = df_n.sort_values(["ANIO", "CARRERA", "SEXO"])

    fig_stacked = px.bar(
        df_n,
        x="ANIO",
        y="PROPORCION",
        color="SEXO",
        text="TEXTO",
        facet_col="CARRERA",
        facet_col_wrap=2,
        title="Proporción de Postulantes por Sexo (Stacked)",
        labels={"PROPORCION": "Proporción", "ANIO": "Año", "SEXO": "Sexo"},
        color_discrete_map={
            "MASCULINO": "#2C8DC5",  # azul fuerte
            "FEMENINO": "#A040AC"    # morado
        }
    )

    fig_stacked.update_layout(
        barmode="stack",
        uniformtext_minsize=8,
        uniformtext_mode='show',
        yaxis=dict(tickformat=".0%", range=[0, 1]),
        xaxis=dict(tickmode="array", tickvals=[2023, 2024, 2025]),
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center")  # leyenda abajo
    )

    st.plotly_chart(fig_stacked, use_container_width=True)

    # ==============================
    # Gráfico 2: Boxplot por puntaje PAES
    # ==============================
    st.subheader("📈 Distribución de Puntajes por Sexo y Carrera")
    st.markdown("""
    Este gráfico compara los **puntajes ponderados PAES** de hombres y mujeres por carrera.  
    - Las **cajas** muestran el **rango intercuartílico** (del 25% al 75%) y la mediana.  
    - Los **puntos individuales** reflejan la dispersión del puntaje.  
    Es útil para observar si existen diferencias sistemáticas en el rendimiento por sexo.

    ---
    """)

    df_box = df_sexo[
        df_sexo["PTJE_PONDERADO"].notna() &
        df_sexo["SEXO"].notna()
    ].copy()

    # Asegurar orden también en boxplot
    df_box["SEXO"] = pd.Categorical(df_box["SEXO"], categories=["MASCULINO", "FEMENINO"], ordered=True)

    fig_box = px.box(
        df_box,
        x="CARRERA",
        y="PTJE_PONDERADO",
        color="SEXO",
        points="all",
        title="Distribución de Puntajes Ponderados por Sexo y Carrera",
        labels={
            "PTJE_PONDERADO": "Puntaje Ponderado",
            "CARRERA": "Carrera",
            "SEXO": "Sexo"
        },
        color_discrete_map={
            "MASCULINO": "#2C8DC5",
            "FEMENINO": "#A040AC"
        }
    )

    fig_box.update_layout(
        boxmode="group",
        xaxis_title="Carrera",
        yaxis_title="Puntaje Ponderado",
        yaxis=dict(range=[500, 1000]),
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center")  # leyenda abajo
    )

    st.plotly_chart(fig_box, use_container_width=True)


# ---------------------------
# Tab 4: Dependencia
# ---------------------------
with tab4:
    st.header("📊 Matrícula por Grupo de Dependencia e Ingreso")

    df_dep = base_total.groupby(["ANIO", "GRUPO_DEPENDENCIA_EST"]).size().reset_index(name="N_ESTUDIANTES")
    fig_dep = px.line(
        df_dep,
        x="ANIO", y="N_ESTUDIANTES", color="GRUPO_DEPENDENCIA_EST", markers=True,
        labels={"N_ESTUDIANTES": "Cantidad de Estudiantes", "ANIO": "Año", "GRUPO_DEPENDENCIA_EST": "Dependencia"},
        title="Evolución de la matrícula por dependencia del establecimiento"
    )
    st.plotly_chart(fig_dep, use_container_width=True, key="fig_dep")



    st.subheader("🎯 Distribución de Puntajes por Grupo de Dependencia (2025)")
    carreras_filtradas = st.multiselect(
        "Selecciona una o más carreras para visualizar su distribución de puntajes",
        options=carreras_disponibles,
        default=["Sociología"]
    )

    df_densidad = base_total[
        (base_total["ANIO"] == 2025) &
        (base_total["CARRERA"].isin(carreras_filtradas)) &
        (base_total["PTJE_PONDERADO"].notna()) &
        (base_total["GRUPO_DEPENDENCIA_EST"] != "SIN INFORMACIÓN")
    ].copy()

    fig_violin = px.violin(
        df_densidad,
        x="PTJE_PONDERADO",
        color="GRUPO_DEPENDENCIA_EST",
        facet_row="CARRERA",
        box=True,
        points="all",
        orientation="h",
        labels={
            "PTJE_PONDERADO": "Puntaje Ponderado",
            "GRUPO_DEPENDENCIA_EST": "Dependencia"
        },
        title="Distribución del Puntaje Ponderado por Carrera y Dependencia (2025)"
    )

    fig_violin.update_layout(
        height=400 + 200 * len(carreras_filtradas),
        margin=dict(t=60, b=40, l=40, r=40),
        template="simple_white"
    )
    st.plotly_chart(fig_violin, use_container_width=True, key="fig_violin")


# ---------------------------
# Tab 5: Ingreso
# ---------------------------
with tab5:
    st.subheader("📈 Distribución por Tipo de Ingreso (2025)")

    fig_torta_tab4 = px.pie(
        base_2025, names="INGRESO", hole=0.3,
        title="Distribución de estudiantes por tipo de ingreso (2025)"
    )
    fig_torta_tab4.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_torta_tab4, use_container_width=True, key="fig_torta_tab4")

    # ---------------------------
    # Sankey embellecido por ingreso y carrera
    # ---------------------------
    st.subheader("Flujo entre Tipo de Ingreso y Carrera (2025)")

    tipos_ingreso = sorted(base_2025["INGRESO"].dropna().unique())
    ingreso_seleccionado = st.selectbox("Selecciona un tipo de ingreso", tipos_ingreso)

    df_sankey = base_2025[
        (base_2025["INGRESO"] == ingreso_seleccionado) &
        base_2025["CARRERA"].notna()
    ].copy()

    df_grouped = df_sankey.groupby(["INGRESO", "CARRERA"]).size().reset_index(name="count")

    all_labels = list(pd.unique(df_grouped["INGRESO"].tolist() + df_grouped["CARRERA"].tolist()))
    label_to_index = {label: i for i, label in enumerate(all_labels)}

    source = df_grouped["INGRESO"].map(label_to_index)
    target = df_grouped["CARRERA"].map(label_to_index)
    value = df_grouped["count"]

    x_pos = []
    y_pos = []
    step_y = 1.0 / (len(all_labels) + 1)

    for i, label in enumerate(all_labels):
        if label == ingreso_seleccionado:
            x_pos.append(0.01)
            y_pos.append(0.5)
        else:
            x_pos.append(0.9)
            y_pos.append(i * step_y)

    import plotly.graph_objects as go

    fig_sankey = go.Figure(data=[
        go.Sankey(
            arrangement="snap",
            node=dict(
                pad=20,
                thickness=20,
                line=dict(color="black", width=0.3),
                label=all_labels,
                color="rgba(255,255,255,0.9)",
                x=x_pos,
                y=y_pos,
                hovertemplate='%{label}<extra></extra>'
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
                color="rgba(255, 102, 102, 0.5)"
            )
        )
    ])

    fig_sankey.update_layout(
        title_text=f"Relación entre Ingreso '{ingreso_seleccionado}' y Carrera (2025)",
        font=dict(size=13, color="black", family="Verdana"),
        height=max(600, 30 * len(all_labels)),
        width=1100,
        margin=dict(l=30, r=30, t=60, b=20)
    )

    st.plotly_chart(fig_sankey, use_container_width=False, key="fig_sankey_final")


# ---------------------------
# Tab 6: Establecimiento
# ---------------------------
with tab6:
    st.header("Colegios con más estudiantes (Región seleccionada)")


    region_filtrada = base_total[base_total["CODIGO_REGION"] == region_seleccionada].copy()

    top_colegios = (
        region_filtrada["NOMBRE_COLEGIO_EGRESO"]
        .astype(str)
        .value_counts()
        .head(30)
        .reset_index()
    )
    top_colegios.columns = ["NOMBRE_COLEGIO_EGRESO", "N_ESTUDIANTES"]

    fig_bar = px.bar(
        top_colegios,
        x="N_ESTUDIANTES",
        y="NOMBRE_COLEGIO_EGRESO",
        orientation="h",
        title=f"Colegios con más estudiantes (Región {region_seleccionada})",
        labels={"NOMBRE_COLEGIO_EGRESO": "Nombre del Colegio", "N_ESTUDIANTES": "Cantidad de Estudiantes"}
    )
    fig_bar.update_layout(yaxis=dict(categoryorder='total ascending'))
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Nube de Palabras de Colegios")
    texto = " ".join(region_filtrada["NOMBRE_COLEGIO_EGRESO"].dropna().astype(str))
    if texto.strip():
        wordcloud = WordCloud(width=1000, height=500, background_color="white").generate(texto)
        fig_wc, ax = plt.subplots(figsize=(15, 7))
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig_wc)
    else:
        st.info("⚠️ No hay datos suficientes para mostrar una nube de palabras en esta región.")





#streamlit run app.py
# return pd.read_excel("bbdd/base_total_homologada.xlsx")
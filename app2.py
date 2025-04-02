import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

# Cargar base de datos
base_total = pd.read_csv("bbdd/base_total_filtrada.csv")
base_total['PTJE_PONDERADO_TOTAL'] = base_total['PTJE_PONDERADO'].fillna(base_total['PTJE_PONDERADO_PACE'])

# Inicializar app con Bootstrap
app2 = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app2.title = "UdeC | Storytelling Admisión"

# Layout
app2.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Img(src="/assets/logo_udec.png", height="70px"), width="auto"),
        dbc.Col(html.H2("Camino a la Universidad: Trayectorias de Admisión UdeC"), className="d-flex align-items-center")
    ], className="my-3"),

    dbc.Tabs([
        # Sección 1: ¿Quiénes postulan?
        dbc.Tab(label="¿Quiénes postulan?", children=[
            html.Label("Selecciona una carrera para ver la trayectoria de puntajes ponderados en el tiempo:"),
            dcc.Dropdown(
                id='dropdown-carrera-linea',
                options=[{'label': c, 'value': c} for c in sorted(base_total['CARRERA_LIMPIA'].dropna().unique())],
                value=base_total['CARRERA_LIMPIA'].dropna().unique()[0],
                className="mb-4"
            ),
            dcc.Graph(id='grafico-trayectoria-puntajes'),

            html.Hr(),
            html.Label("Brechas por género en la elección de carreras (por año):"),
            dcc.Graph(id='grafico-brecha-genero',
                      figure=px.histogram(base_total, x="ANIO", color="SEXO", barmode="group",
                                         title="Distribución de estudiantes por sexo a lo largo de los años"))
        ]),

        # Sección 2: ¿Cómo postulan?
        dbc.Tab(label="¿Cómo postulan?", children=[
            html.Label("Selecciona una carrera:"),
            dcc.Dropdown(
                id='dropdown-carrera',
                options=[{'label': c, 'value': c} for c in sorted(base_total['CARRERA_LIMPIA'].dropna().unique())],
                value=base_total['CARRERA_LIMPIA'].dropna().unique()[0],
                className="mb-3"
            ),
            dbc.Row([
                dbc.Col(dcc.Graph(id='grafico-puntaje'), md=6),
                dbc.Col(dcc.Graph(id='grafico-puntaje-sexo'), md=6)
            ])
        ]),

        # Sección 3: ¿Qué carreras eligen?
        dbc.Tab(label="¿Qué carreras eligen?", children=[
            dbc.Row([
                dbc.Col(dcc.Graph(
                    figure=px.histogram(base_total, x="CARRERA_LIMPIA", color="SEXO", barmode="group",
                                         title="Distribución por carrera y sexo")
                ))
            ])
        ]),

        # Sección 4: Tabla completa
        dbc.Tab(label="📋 Tabla de estudiantes", children=[
            dag.AgGrid(
                id="tabla", 
                columnDefs=[{"field": c} for c in base_total.columns],
                rowData=base_total.to_dict("records"),
                defaultColDef={"filter": True, "sortable": True, "resizable": True},
                style={"height": 600, "width": "100%"}
            )
        ])
    ])
], fluid=True)

# Callbacks
@app2.callback(
    [Output('grafico-puntaje', 'figure'),
     Output('grafico-puntaje-sexo', 'figure')],
    [Input('dropdown-carrera', 'value')]
)
def actualizar_graficos(carrera):
    df = base_total[base_total['CARRERA_LIMPIA'] == carrera]

    fig1 = px.histogram(df, x="PTJE_PONDERADO_TOTAL", nbins=20, title="Distribución del puntaje ponderado total")
    fig2 = px.box(df, y="PTJE_PONDERADO_TOTAL", color="SEXO", title="Puntaje ponderado total por sexo")

    return fig1, fig2

@app2.callback(
    Output('grafico-trayectoria-puntajes', 'figure'),
    Input('dropdown-carrera-linea', 'value')
)
def actualizar_trayectoria(carrera):
    df = base_total[base_total['CARRERA_LIMPIA'] == carrera]
    df_prom = df.groupby('ANIO')['PTJE_PONDERADO_TOTAL'].mean().reset_index()
    fig = px.line(df_prom, x='ANIO', y='PTJE_PONDERADO_TOTAL', markers=True,
                  title=f"Trayectoria de puntajes ponderados para {carrera}",
                  labels={'PTJE_PONDERADO_TOTAL': 'Promedio Puntaje Ponderado'})
    return fig

# Correr app
if __name__ == '__main__':
    app2.run(debug=True, port=8051)

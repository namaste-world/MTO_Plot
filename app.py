import pandas as pd
import json
import math
from dash import Dash, dcc, html, Input, Output, ctx
import plotly.graph_objects as go

# --- Load data ---
nodes_df = pd.read_json('public/nodes.json')
nodes_df['date'] = pd.to_datetime(nodes_df['date'], format='%Y-%m-%d', errors='coerce')
nodes_df = nodes_df.dropna(subset=['date'])
nodes_df['y'] = pd.to_numeric(nodes_df['yPx'], errors='coerce').fillna(0)

edge_types = ["semantic", "sharedref", "lineage"]
edges = {et: json.load(open(f'public/{et}_edges.json')) for et in edge_types}

edge_colors = {
    'semantic':  'rgba(78,121,167,0.6)',
    'sharedref': 'rgba(227,119,194,0.6)',
    'lineage':   'rgba(214,39,40,0.6)'
}

app = Dash(__name__)
app.layout = html.Div(style={'display':'flex','height':'100vh'}, children=[

    html.Div(style={'width':'20%','padding':'10px','borderRight':'1px solid #ccc'}, children=[
        html.H4("Edge Type"),
        dcc.RadioItems(
            id='edge-type',
            options=[{'label': et, 'value': et} for et in edge_types],
            value=edge_types[0],
            labelStyle={'display':'block','marginBottom':'6px'}
        ),
        html.H4("Search"),
        dcc.Input(
            id='search-box', type='text',
            placeholder='Title or author…',
            style={'width':'100%','marginBottom':'10px'}
        ),
        html.Button("Reset View",    id='reset-button',   n_clicks=0, style={'marginRight':'8px'}),
        html.Button("Show All",      id='showall-button', n_clicks=0),
    ]),

    html.Div(style={'flex':'1','position':'relative','overflowX':'auto','overflowY':'auto'}, children=[
        dcc.Graph(
            id='graph',
            config={'displayModeBar': True, 'scrollZoom': True},
            style={'minWidth':'3000px','minHeight':'2000px'}
        ),
        html.Div(id='node-info', style={
            "position": "absolute",
            "top": "10px",
            "right": "10px",
            "background": "white",
            "padding": "8px",
            "border": "1px solid #ccc",
            "boxShadow": "2px 2px 5px rgba(0,0,0,0.2)",
            "zIndex": "1000"
        })
    ])
])


@app.callback(
    Output('graph', 'figure'),
    Input('graph',         'clickData'),
    Input('edge-type',     'value'),
    Input('search-box',    'value'),
    Input('reset-button',  'n_clicks'),
    Input('showall-button','n_clicks'),
)
def update_graph(clickData, selected_type, search_term, reset_clicks, showall_clicks):
    trigger = ctx.triggered_id

    if trigger == 'reset-button':
        curr_edges, plot_df = [], nodes_df
    elif trigger == 'showall-button':
        curr_edges, plot_df = edges[selected_type], nodes_df
    elif trigger == 'graph' and clickData:
        cid = clickData['points'][0].get('customdata')
        if cid:
            filtered = [e for e in edges[selected_type]
                        if cid in (e['source'], e['target'])]
            curr_edges = filtered
            plot_df = (nodes_df[nodes_df['id'].isin(
                {n for e in filtered for n in (e['source'], e['target'])}
            )] if filtered else nodes_df)
        else:
            curr_edges, plot_df = [], nodes_df
    else:
        curr_edges, plot_df = [], nodes_df

    # build fig…
    fig = go.Figure()
    fig.update_layout(
        dragmode="zoom",
        xaxis=dict(
            rangeslider=dict(visible=True, thickness=0.05),
            type="date", tickformat="%Y", title="Publication Date"
        ),
        yaxis=dict(visible=False, range=[-20, nodes_df['y'].max()+20]),
        height=800, hovermode="closest", showlegend=False,
        margin=dict(l=40,r=40,t=80,b=40)
    )

    # draw edges
    for e in curr_edges:
        et    = e['type'].lower()
        width = (e.get('weight',1)*5) if et=="semantic" else \
                (math.sqrt(e.get('weight',1)) if et=="sharedref" else 1)
        dash  = 'solid' if et=="semantic" else ('dot' if et=="sharedref" else 'dash')
        color = edge_colors.get(et, 'rgba(0,0,0,0.6)')
        src   = nodes_df.loc[nodes_df['id']==e['source']].iloc[0]
        tgt   = nodes_df.loc[nodes_df['id']==e['target']].iloc[0]
        fig.add_trace(go.Scatter(
            x=[src['date'], tgt['date']],
            y=[src['y'],   tgt['y']],
            mode='lines',
            line=dict(width=width, color=color, dash=dash),
            hoverinfo='none'
        ))

    # color nodes
    term = (search_term or '').lower()
    colors = [
        'orange' if term and term in (row.title.lower()+" "+ " ".join(row.authors).lower())
        else 'blue'
        for row in plot_df.itertuples()
    ]

    # draw nodes with hover enabled
    hover_texts = [f"{row.title}<br>{', '.join(row.authors)}"
                   for row in plot_df.itertuples()]
    fig.add_trace(go.Scattergl(
        x=plot_df['date'],
        y=plot_df['y'],
        customdata=plot_df['id'],
        mode='markers',
        marker=dict(size=12, color=colors, opacity=0.8),
        hoverinfo='text',
        hovertext=hover_texts,
        hovertemplate="%{hovertext}<extra></extra>"
    ))

    return fig


@app.callback(
    Output('node-info', 'children'),
    Input('graph',          'hoverData'),
    Input('reset-button',   'n_clicks'),
    Input('showall-button','n_clicks'),
)
def show_hover(hoverData, _r, _s):
    trig = ctx.triggered_id
    if trig in ('reset-button','showall-button'):
        return ""
    if not hoverData or 'points' not in hoverData:
        return ""
    nid = hoverData['points'][0].get('customdata')
    if not nid:
        return ""
    row = nodes_df[nodes_df['id']==nid].iloc[0]
    return html.Div([
        html.B(row['title']),
        html.Div(f"Authors: {', '.join(row['authors'])}")
    ])


if __name__ == '__main__':
    app.run(debug=True)
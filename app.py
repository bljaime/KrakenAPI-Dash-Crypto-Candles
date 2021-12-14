
import krakenex
from pykrakenapi import KrakenAPI
import currencies
import dash
from dash import dcc
from dash import html
from dash.dependencies import Output, Input
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Kraken instances
api_g = krakenex.API()
k_g = KrakenAPI(api_g)


#####################
#     VARIABLES     #
#####################

# A list of pairs of currencies to select from in the menu
pair_selection = ['BTC/EUR', 'BTC/USD', 'ETH/EUR', 'ETH/USD', 'SOL/EUR', 'SOL/USD', 'LTC/EUR', 'LTC/USD']

# Granularities as a global variable to choose from and its equivalence in seconds
g_dict = {'1m': 60, '5m': 300, '15m': 900, '30m': 1800}

# Historical depth as a global variable to choose from and its equivalence in minutes
d_dict = {'1 hour': 60, '2 hours': 120, '3 hours': 180, '5 hours': 300, '12 hours': 720, '1 day': 1440}

# First call pair used
current_pair = 'BTC/USD'

# Retrieve 60 minutes of trades of the currency pair. Higher the depth, longer the waiting time
min_info = 60

# Initial retrieval
obj = currencies.Pair(current_pair, '1m', min_info, api_g)
obj.retrieve_minutes_depth()
obj.get_ohlc()
# obj.print_info()


#####################
#       DASH        #
#####################

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Currency Pairs"
server = app.server

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.P(children="💸🚀🌒", className="header-emoji"),
                html.H1(
                    children="Candlestick Charts Analysis", className="header-title",

                ),
                html.P(
                    children="Look up candlestick charts and patterns for a pair of currencies.  "
                             "🚀🚀 “If you don't believe it or don't get it, I don't have the time"
                             " to try to convince you, sorry.” – Satoshi Nakamoto. 🚀🚀",
                    className="header-description",
                ),

                html.Div(
                    children='Author: Jaime Blanco Linares. Contact: jblancolina@alumni.unav.es',
                    className="header-description-sub",
                ),

            ],
            className="header",
        ),
        html.Div(
            className="menu", children=[
                html.Div(className='text-box', children=[
                    html.Label(['New data retrieval takes a few secs. to complete.', html.Br(),
                                ' Please wait until the data is available.'],
                               style={'color': 'rgb(3,160,98)', "text-align": "center"}
                               ),
                ], style=dict(width='28%')),
                html.Div(className='currency-pair', children=[
                    html.Label(['Pair: '], style={'color': 'rgb(3,160,98)', "text-align": "center"}),
                    dcc.Dropdown(
                        id="filter-curr-pair",
                        options=[{"label": pair, "value": pair} for pair in pair_selection],
                        value="BTC/USD",  # default value
                        clearable=False,
                        style={'color': 'rgb(3,160,98)'}
                    )], style=dict(width='16%')),
                html.Div(className='granul', children=[
                    html.Label(['Granularity: ', html.Br()], style={'color': 'rgb(3,160,98)', "text-align": "center"}),
                    dcc.RadioItems(
                        id="filter-granularity",
                        options=[{"label": gr, "value": gr} for gr in list(g_dict.keys())],
                        value="1m",  # default value
                        labelStyle={'color': 'rgb(3,160,98)'}
                    )], style=dict(width='21%')),
                html.Div(className='hist-depth', children=[
                    html.Label(['Graph depth (≥5h. may take long): '],
                               style={'color': 'rgb(3,160,98)', "text-align": "center"}),
                    dcc.Dropdown(
                        id="historical-depth",
                        options=[{"label": de, "value": de} for de in list(d_dict.keys())],
                        clearable=False,
                        value='1 hour',  # default value
                        style={'color': 'rgb(3,160,98)'}
                    )], style=dict(width='16%')),
            ],
        ),
        dcc.Graph(
            id='graph',
        )
    ]
)


@app.callback(
    Output("graph", "figure"),
    [
        Input("filter-curr-pair", "value"),
        Input("filter-granularity", "value"),
        Input("historical-depth", "value"),
    ],
)
def update_charts(pair, gra, depth):
    """
    Interacts with the application and triggers actions to be taken following a
    change in currency pair, granularity or historical depth.
    """

    global obj
    global current_pair
    global min_info

    # Generate interesting fields such as coin or currency, and the pair in the query format to the API
    ticker, curr = pair.split('/')[0], pair.split('/')[1]
    pair_query = pair.replace('/', '')

    # Associated currency symbol
    curr = '$' if curr == 'USD' else '€'

    # If the pair has not changed, i.e., it is only intended to change the granularity, it is
    # not necessary to download new trades. If the pair has changed, it is necessary to do so
    if pair == current_pair:
        obj.gran_desc = gra
        obj.gran_s = g_dict[gra]
        # obj.print_info()
    else:
        current_pair = pair
        obj = currencies.Pair(pair_query, gra, min_info, api_g)
        # obj.print_info()
        obj.retrieve_minutes_depth()
        obj.get_ohlc()

    # If the depth in minutes has not changed, no further retrievals are necessary
    if d_dict[depth] != min_info:
        min_info = d_dict[depth]
        obj.minutes = d_dict[depth]
        # obj.print_info()
        # New retrieval with a depth of 'depth'
        obj.retrieve_minutes_depth()

    # The necessary update of OHCL data is common to all callbacks
    obj.get_ohlc()

    # Initialize subplots
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Create candlestick graph
    fig.add_trace(go.Candlestick(x=obj.ohlc.index,
                                 open=obj.ohlc.open,
                                 high=obj.ohlc.high,
                                 low=obj.ohlc.low,
                                 close=obj.ohlc.close,
                                 name="Candlestick", ), )

    # Include line graph for Price
    fig.add_trace(go.Scatter(mode='lines',
                             x=obj.trades.index,
                             y=obj.trades.price,
                             marker=dict(
                                 color='rgb(255,255,188)',
                                 line=dict(
                                     color='rgb(255,255,188)',
                                     width=0.5
                                 )
                             ),
                             name="Price",
                             textfont=dict(color='rgb(255,255,188)'),
                             showlegend=True)
                  )

    # Include line graph for VWAP
    fig.add_trace(go.Scatter(mode='lines+markers',
                             x=obj.ohlc.index,
                             y=obj.ohlc.vwap,
                             marker=dict(
                                 color='rgb(69,93,247)',
                                 size=2,
                                 line=dict(
                                     color='rgb(69,93,247)',
                                     width=2
                                 )
                             ),
                             name="VWAP",
                             textfont=dict(color='rgb(3,160,98)'),
                             showlegend=True)
                  )

    # Include bar graph for Volume
    fig.add_trace(go.Bar(x=obj.ohlc.index,
                         y=obj.ohlc.volume,
                         marker=dict(color='rgba(221,218,212,0.2)', ),
                         name="Volume"), secondary_y=True)

    # Don't show grid for secondary 'y' axe
    fig.layout.yaxis2.showgrid = False

    fig.update_layout(font_family="Lato",
                      font_color="rgb(3,160,98)",
                      title_font_family="Lato",
                      title_font_color="rgb(3,160,98)",
                      legend_title_font_color="rgb(3,160,98)",
                      title={
                          'text': pair + " Candlestick Chart",
                          'y': 0.9,
                          'x': 0.46,
                          'xanchor': 'center',
                          'yanchor': 'top'},
                      yaxis_title=ticker + ' price',
                      yaxis2_title='Volume (' + ticker + ')',
                      xaxis={"color": 'rgb(3,160,98)'},
                      yaxis={"tickprefix": curr,
                             "color": 'rgb(3,160,98)'},
                      height=750,
                      bargap=0.7,
                      plot_bgcolor='rgb(15,15,15)',
                      paper_bgcolor='rgb(15,15,15)',
                      separators='.')

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)

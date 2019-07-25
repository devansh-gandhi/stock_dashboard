#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output
import dash_table
import json

from elasticsearch import Elasticsearch

app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True


es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])

if 'DYNO' in os.environ:
    app_name = os.environ['DASH_APP_NAME']
else:
    app_name = 'stock-timeseriesplot'


# returns modal (hidden by default)

def modal():
    return html.Div(
        html.Div(
            [
                html.Div(
                    [
                        # modal header
                        html.Div(
                            [
                                html.Span(
                                    "New Opportunity",
                                    style={
                                        "color": "#506784",
                                        "fontWeight": "bold",
                                        "fontSize": "20",
                                    },
                                ),
                                html.Span(
                                    "×",
                                    id="opportunities_modal_close",
                                    n_clicks=0,
                                    style={
                                        "float": "right",
                                        "cursor": "pointer",
                                        "marginTop": "0",
                                        "marginBottom": "17",
                                    },
                                ),
                            ],
                            className="row",
                            style={"borderBottom": "1px solid #C8D4E3"},
                        ),
                        # modal form
                        html.Div(
                            [
                                html.P(id='row_no'),
                            ],
                            className="row",
                            style={"paddingTop": "2%"},
                        ),
                        # submit button

                        html.Span(
                            "Submit",
                            id="submit_new_opportunity",
                            n_clicks=0,
                            className="button button--primary add",
                        ),
                    ],
                    className="modal-content",
                    style={"textAlign": "center"},
                )
            ],
            className="modal",
        ),
        id="opportunities_modal",
        style={"display": "none"},
    )









app.layout = html.Div([

    html.Div([

        html.H1("Stock Dashboard",style={'textAlign': 'center', 'margin': '0px', 'font-size':'20px', 'background-color': '#333333', 'color': '#fff', 'padding': '10px'  }),


        dcc.Tabs(id="tabs", children=[
            dcc.Tab(label='Overview',children=[
                html.Div([

                    dcc.RadioItems(id='radio-div',
                        options=[
                            {'label': ' Company Name', 'value': 'CN'},
                            {'label': ' Extract', 'value': 'EX'},
                        ],
                        value='MTL',
                        labelStyle={'display': 'inline-block'}
                    ),

                    dcc.Dropdown(id='my-dropdown',
                            options=[{'label': 'Microsoft', 'value': 'MSFT'}, {'label': 'Apple', 'value': 'AAPL'},
                                 {'label': 'Google', 'value': 'GOOG'}], value='MSFT',),

                ], id='my-dropdown-div'),


            ]),

            dcc.Tab(label='Technical Analysis',  children=[

                html.H3('Stock Price',style={'textAlign': 'center','margin':'0px auto', 'margin-top': '5px' }),
                dcc.Graph(id='my-graph', config={'displayModeBar': False}, ),

                html.H3('Technical Indicators',style={'textAlign': 'center','margin':'0px auto', 'margin-top': '5px', 'margin-top': '10px' }),

                html.Div([

                    dcc.Graph(className='indicators',id='indicators-graph', config={'displayModeBar': False}, ),
                    dcc.Graph(className='indicators',id='indicators-ema-graph', config={'displayModeBar': False}, ),
                    dcc.Graph(className='indicators',id='indicators-rsi-graph', config={'displayModeBar': False}, ),

                ], id='sub_tab', )]),

            dcc.Tab(label='Market Sentiment Analysis', children=[

                html.Div([
                    html.Div([ html.H3('Sentiment Chart'), ], className='div-30'),
                    html.Div([html.H3('Word Cloud'), ], className='div-70'),


                ], className='sentiment_div', ),

                html.Div([
                    html.Div([html.Div([dcc.Graph(id='pie-chart', config={'displayModeBar': False}, ), ], className='pie-chart-div') ], className='div-30'),
                    html.Div([html.Div([html.H5('Placeholder for word cloud')], className='pie-chart-div', id='word-cloud',  ) ], className='div-70' ),

                ], className='sentiment_div', ),



                html.Div([
                    html.Div([html.H3('News Analysis') ], className='div-50'),
                    html.Div([html.H3('Twitter feed Analysis') ], className='div-50'),
                ], className='sentiment_div', id='tp'),

                html.Div([
                    html.Div([
                        dash_table.DataTable(
                                id='news_table_data',
                                columns=[{"name":'Title',"id":'title'}, {'name':'Sentiment',"id":'sentiment'}],
                                row_selectable='single',
                                style_cell={
                                    'minWidth': '0px', 'maxWidth': '80%',
                                    'whiteSpace': 'normal',
                                    'textAlign': 'left',

                                },
                                css=[{
                                    'selector': '.dash-cell div.dash-cell-value',
                                    'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
                                }],
                        )

                    ],id='news_table', className='div-50'),

                    html.Div([dash_table.DataTable(
                        id='tweet_table_data',
                        columns=[{"name":'Tweet Description',"id":'message'}, {'name':'Sentiment',"id":'label'}],
                        row_selectable='single',
                        style_cell={
                            'minWidth': '0px', 'maxWidth': '85%',
                            'whiteSpace': 'normal',
                            'textAlign': 'left',
                        },
                        css=[{
                                'selector': '.dash-cell div.dash-cell-value',
                                'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
                             }],

                        ) ], id = 'tweet_table', className='div-50'),
                ], className='sentiment_div', ),

            ]),

            dcc.Tab(label='Earnings Call Analysis', children=[

             ]),
        ]),

    ], className='right-container'),
    modal(),
    ], className="container")



app.scripts.append_script({"external_url": ['https://code.jquery.com/jquery-3.2.1.min.js',]})



@app.callback(Output('my-graph', 'figure'),
              [Input('my-dropdown', 'value')])
def update_graph(selected_dropdown_value):
    dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google", }
    trace1 = []
    trace2 = []

    data_dict = es.search(index='stock_data', body={"size": 50, "query": {"match": {"stock-symbol": selected_dropdown_value}}})
    initial_df = pd.DataFrame.from_dict(data_dict['hits']['hits'])
    stock_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)],axis=1)

    stock_data_df['timestamp'] = pd.to_datetime(stock_data_df.timestamp, infer_datetime_format=True)

    trace1.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"], y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["open"],mode='lines',
        opacity=0.7, name=f'Open', textposition='bottom center'))
    trace2.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"], y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["close"],mode='lines',
        opacity=0.6 , name=f'Close',textposition='bottom center'))



    traces = [trace1, trace2]
    data = [val for sublist in traces for val in sublist]
    figure = {'data': data,
        'layout': go.Layout(colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],
            height=250,title=f"Opening and Closing Prices for " + dropdown[selected_dropdown_value],
            xaxis={'type': 'date'},yaxis={"title":"Price (USD)"},
            margin = go.layout.Margin(l=60, r=10, b=40, t=50, ),)}
    return figure

@app.callback(Output('indicators-graph', 'figure'),
              [Input('my-dropdown', 'value')])
def update_indicator_graph(selected_dropdown_value):
    dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google", }
    trace1 = []
    trace2 = []

    data_dict = es.search(index='stock_data', body={"size": 50, "query": {"match": {"stock-symbol": selected_dropdown_value}}})
    initial_df = pd.DataFrame.from_dict(data_dict['hits']['hits'])
    stock_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)],axis=1)

    stock_data_df['timestamp'] = pd.to_datetime(stock_data_df.timestamp, infer_datetime_format=True)

    trace1.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"], y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["close"],mode='lines',
        opacity=0.7, name=f'Close', textposition='bottom center'))
    trace2.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"], y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["close"].rolling(window=10).mean(),mode='lines',
        opacity=0.6 , name=f'SMA',textposition='bottom center'))

    traces = [trace1, trace2]
    data = [val for sublist in traces for val in sublist]
    figure = {'data': data,
        'layout': go.Layout(colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],
            height=250,title=f" Simple Moving Average (SMA)", legend_orientation="h", margin=go.layout.Margin(l=60, r=10, b=0, t=50,),
            xaxis={'type': 'date'},yaxis={"title":"Price (USD)"})}
    return figure

@app.callback(Output('indicators-ema-graph', 'figure'),
              [Input('my-dropdown', 'value')])
def update_indicator_ema_graph(selected_dropdown_value):
    dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google", }
    trace1 = []
    trace2 = []

    data_dict = es.search(index='stock_data', body={"size": 50, "query": {"match": {"stock-symbol": selected_dropdown_value}}})
    initial_df = pd.DataFrame.from_dict(data_dict['hits']['hits'])
    stock_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)],axis=1)

    stock_data_df['timestamp'] = pd.to_datetime(stock_data_df.timestamp, infer_datetime_format=True)

    trace1.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"], y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["close"],mode='lines',
        opacity=0.7, name=f'Close', textposition='bottom center'))
    trace2.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"],y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["close"].ewm(span=10, adjust=False).mean(), mode='lines',
        opacity=0.7, name=f'EMA', textposition='bottom center'))


    traces = [trace1, trace2]
    data = [val for sublist in traces for val in sublist]
    figure = {'data': data,
        'layout': go.Layout(colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],
            height=250,title=f" Exponential Moving Average (EMA)", legend_orientation="h", margin=go.layout.Margin(l=60, r=10, b=0, t=50,),
            xaxis={'type': 'date'},yaxis={"title":"Price (USD)"})}
    return figure


@app.callback(Output('indicators-rsi-graph', 'figure'),
              [Input('my-dropdown', 'value')])
def update_indicator_rsi_graph(selected_dropdown_value):
    trace1 = []
    trace2 = []

    data_dict = es.search(index='stock_data',
                          body={"size": 50, "query": {"match": {"stock-symbol": selected_dropdown_value}}})
    initial_df = pd.DataFrame.from_dict(data_dict['hits']['hits'])
    stock_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)

    stock_data_df['timestamp'] = pd.to_datetime(stock_data_df.timestamp, infer_datetime_format=True)

    close = stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["close"]

    window_length = 10
    delta = close.astype(float).diff()
    delta = delta[1:]

    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0

    roll_up1 = up.ewm(window_length).mean()
    roll_down1 = down.ewm(window_length).mean().abs()

    RS1 = roll_up1 / roll_down1
    RSI1 = 100.0 - (100.0 / (1.0 + RS1))

    roll_up2 = up.rolling(window_length).mean()
    roll_down2 = down.rolling(window_length).mean().abs()

    RS2 = roll_up2 / roll_down2
    RSI2 = 100.0 - (100.0 / (1.0 + RS2))

    trace1.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"],
                             y=RSI1,
                             mode='lines',
                             opacity=0.7, name=f'RSI based on EMA', textposition='bottom center'))
    trace2.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"],
                             y= RSI2, mode='lines',
                             opacity=0.7, name=f'RSI based on SMA', textposition='bottom center'))

    traces = [trace1, trace2]
    data = [val for sublist in traces for val in sublist]
    figure = {'data': data,
              'layout': go.Layout(colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],
                                  height=250, title=f" Relative Strength Index (RSI) ", legend_orientation="h",
                                  margin=go.layout.Margin(l=60, r=10, b=0, t=50, ),
                                  xaxis={'type': 'date'}, yaxis={"title": "Price (USD)"})}
    return figure


@app.callback(Output('pie-chart', 'figure'),
              [Input('my-dropdown', 'value')])
def update_piechart(selected_dropdown_value):
    dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google", "FB": 'Facebook'}

    label_data_dict = es.search(index='tweets_data', body={"size": 100, "query": {"match": {"company_name": dropdown[selected_dropdown_value]}}})
    initial_df = pd.DataFrame.from_dict(label_data_dict['hits']['hits'])
    label_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)

    news_data_dict = es.search(index='news_data', body={"size": 100, "query": {"match": {"company_name": dropdown[selected_dropdown_value]}}})
    initial_df = pd.DataFrame.from_dict(news_data_dict['hits']['hits'])
    news_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)


    negative = label_data_df.loc[label_data_df.label == 'Negative', 'label'].count() + news_data_df.loc[news_data_df.sentiment == 'Negative', 'sentiment'].count()
    positive = label_data_df.loc[label_data_df.label == 'Positive', 'label'].count() + news_data_df.loc[news_data_df.sentiment == 'Positive', 'sentiment'].count()

    data = [go.Pie(values=[positive.item(),negative.item()], labels=['Positive','Negative'])]

    figure = {
        'data':data,
        'layout': go.Layout(
            #paper_bgcolor='rgba(0,0,0,0)',
            #plot_bgcolor='rgba(0,0,0,0)'
            height=250,legend=dict(orientation='h',yanchor='bottom',xanchor='center',y=1.2, x=0.5, ), margin=go.layout.Margin(l=10, r=10, b=10, t=10, ),
    ),
    }

    return figure


@app.callback(Output('news_table_data', 'data'),
              [Input('my-dropdown', 'value'),
               Input('pie-chart', 'clickData'),])
def update_news_feed(selected_dropdown_value,clickData):
    dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google", }
    news_data_dict = es.search(index='news_data', body={"size": 20, "query": {"match": {"company_name": dropdown[selected_dropdown_value] }}})
    initial_df = pd.DataFrame.from_dict(news_data_dict['hits']['hits'])
    news_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)

    if clickData:
        sentiment = clickData['points'][0]['label']
        news_data_df = news_data_df.loc[news_data_df['sentiment'] == sentiment]

    news_data_df = news_data_df.loc[:, ['title', 'sentiment']]

    return news_data_df.to_dict('records')



@app.callback(Output('tweet_table_data', 'data'),
              [Input('my-dropdown', 'value'),
               Input('pie-chart', 'clickData'), ])

def update_tweet_feed(selected_dropdown_value,clickData ):
    dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google", "FB":'Facebook' }
    tweet_data_dict = es.search(index='tweets_data', body={"size": 20, "query": {"match": {"company_name": dropdown[selected_dropdown_value] }}})
    initial_df = pd.DataFrame.from_dict(tweet_data_dict['hits']['hits'])
    tweet_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)

    if clickData:
        sentiment = clickData['points'][0]['label']
        tweet_data_df = tweet_data_df.loc[tweet_data_df['label'] == sentiment]


    tweet_data_df = tweet_data_df.loc[:,['message','label']]

    #{'name':'Tweet Description'}, {'name':'Sentiment'}
    return tweet_data_df.to_dict('records')










if __name__ == '__main__':
    app.run_server(debug=False)
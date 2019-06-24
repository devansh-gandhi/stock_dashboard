#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output

from elasticsearch import Elasticsearch

app = dash.Dash(__name__)


es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])

if 'DYNO' in os.environ:
    app_name = os.environ['DASH_APP_NAME']
else:
    app_name = 'stock-timeseriesplot'


app.layout = html.Div([

    html.H1("Stock Prices", style={'textAlign': 'center', 'margin': '0px', }),

    html.Div([
        dcc.Dropdown(id='my-dropdown',
                options=[{'label': 'Microsoft', 'value': 'MSFT'}, {'label': 'Apple', 'value': 'AAPL'},
                         {'label': 'Google', 'value': 'GOOG'}], value='MSFT',),
        ], id='my-dropdown-div'),

    dcc.Graph(id='my-graph', config={'displayModeBar': False},),


    html.Table([
            html.Tr([
                html.Td(html.H3('News Analysis'), style={'width': '50%'}),
                html.Td(html.H3('Twitter feed Analysis'), style={'width': '50%'}),
            ]),

            html.Tr([
                html.Td(id='news_table'),

            ],),


        ],
        style={'textAlign': 'center', 'align': 'center', 'width': '90%', 'margin': '0px auto'}
    ),

    ], className="container")


@app.callback(Output('my-graph', 'figure'),
              [Input('my-dropdown', 'value')])
def update_graph(selected_dropdown_value):
    dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google", }
    trace1 = []
    trace2 = []

    data_dict = es.search(index='stock_data', body={"size": 100, "query": {"match": {"stock-symbol": selected_dropdown_value}}})
    initial_df = pd.DataFrame.from_dict(data_dict['hits']['hits'])
    stock_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)],axis=1)

    stock_data_df['timestamp'] = pd.to_datetime(stock_data_df.timestamp, infer_datetime_format=True)

    trace1.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"], y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["open"],mode='lines',
        opacity=0.7, name=f'Open {dropdown[selected_dropdown_value]}', textposition='bottom center'))
    trace2.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"], y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["close"],mode='lines',
        opacity=0.6 , name=f'Close {dropdown[selected_dropdown_value]}',textposition='bottom center'))



    traces = [trace1, trace2]
    data = [val for sublist in traces for val in sublist]
    figure = {'data': data,
        'layout': go.Layout(colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],
            height=300,title=f"Opening and Closing Prices for " + dropdown[selected_dropdown_value] + " Over Time",
            xaxis={"title":"Date",
                    'type': 'date'},yaxis={"title":"Price (USD)"})}
    return figure



@app.callback(Output('news_table', 'children'),
              [Input('my-dropdown', 'value')])
def update_news_feed(selected_dropdown_value):
    dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google", }
    news_data_dict = es.search(index='news_data', body={"size": 5, "query": {"match": {"company_name": dropdown[selected_dropdown_value] }}})
    initial_df = pd.DataFrame.from_dict(news_data_dict['hits']['hits'])
    news_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)

    #print(news_data_df.head() )
    return html.Table(

        [html.Tr([html.Td(html.Th('Title'),), html.Td(html.Th('Sentiment'), style={'width': '27%', })],
            style={'width': '100%', 'text-align': 'center', })] +

        [html.Tr([html.Td([news_data_df.loc[i]['title']], ), html.Td([news_data_df.loc[i]['sentiment']], style={'width': '30%',})], style={'width': '100%',}) for i in range(len(news_data_df))],

    style={'width': '100%', 'display': 'block', 'text-align': 'left', }, id='news_table_data')

if __name__ == '__main__':
    app.run_server(debug=False)
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
                                    "Tweet",
                                    style={"color": "#000080","fontWeight": "bold","fontSize": "20",},
                                ),
                                html.Span(
                                    "×",
                                    id="opportunities_modal_close",
                                    n_clicks=0,
                                    style={"float": "right","cursor": "pointer","marginTop": "0","marginBottom": "17",},
                                ),
                            ],
                            className="row",
                            style={"borderBottom": "1px solid #C8D4E3"},
                        ),
                        # modal data
                        html.Div(
                            [
                                html.P(id='row_no'),
                            ],
                            className="row",
                            style={"paddingTop": "2%"},
                        ),


                    ],
                    className="modal-content",
                    style={"textAlign": "center"},
                )
            ],
            className="modal",
        ),
        id="tweet_modal",
        style={"display": "none"},
    )

def news_modal():
    return html.Div(
        html.Div(
            [
                html.Div(
                    [
                        # modal header
                        html.Div(
                            [
                                html.Span(
                                    "News",
                                    style={"color": "#000080","fontWeight": "bold","fontSize": "20",},
                                ),
                                html.Span(
                                    "×",
                                    id="news_modal_close",
                                    n_clicks=0,
                                    style={"float": "right","cursor": "pointer","marginTop": "0","marginBottom": "17",},
                                ),
                            ],
                            className="row",
                            style={"borderBottom": "1px solid #C8D4E3"},
                        ),
                        # modal data
                        html.Div(
                            [
                                html.P(id='news_modal_data'),
                            ],
                            className="row",
                            style={"paddingTop": "2%"},
                        ),


                    ],
                    className="modal-content",
                    style={"textAlign": "center"},
                )
            ],
           className="modal",
        ),
        id="news_modal",
        style={"display": "none"},
    )









app.layout = html.Div([

    html.Div([



        dcc.Tabs(id="tabs", children=[

            dcc.Tab(label='Market Sentiment Analysis', children=[

                html.Div([
                    dcc.RadioItems(id='radio-div',
                        options=[
                            {'label': ' Company Name', 'value': 'CN'},
                            {'label': ' Extract', 'value': 'EX'},
                        ],
                        value='CN',
                        labelStyle={'display': 'inline-block'}
                    ),

                    dcc.Dropdown(id='my-dropdown',
                            options=[{'label': 'Microsoft', 'value': 'MSFT'}, {'label': 'Apple', 'value': 'AAPL'},
                                 {'label': 'Google', 'value': 'GOOG'}], value='MSFT',),

                    html.Div([dcc.Input(id='text_search', value='', placeholder='Enter a extract....', ),
                    html.Button('Submit', id='button'),], id='extract_div',style={"display": "none"} ),

                ], id='my-dropdown-div'),

                html.Div([
                    html.Div([ html.H3('Sentiment Chart'), ], className='div-30'),
                    html.Div([html.H3('Stock Chart'), ], className='div-70'),


                ], className='sentiment_div', ),

                html.Div([
                    html.Div([html.Div([dcc.Graph(id='pie-chart', config={'displayModeBar': False}, ), ], className='pie-chart-div', id='pie-chart-container')], className='div-30'),
                    html.Div([html.Div([dcc.Graph(id='my-graph', config={'displayModeBar': False}, ),], className='pie-chart-div', id='stock-price-container',)], className='div-70' ),

                ], className='sentiment_div', ),



                html.Div([
                    html.Div([html.H3('News Analysis') ], className='div-50'),
                    html.Div([html.H3('Twitter feed Analysis') ], className='div-50'),
                ], className='sentiment_div', id='tp'),

                html.Div([
                    html.Div([
                        dash_table.DataTable(
                                id='news_table_data',
                                columns=[{"name":'Title',"id":'title'}],
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
                        columns=[{"name":'Tweet Description',"id":'message'}],
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
    modal(), news_modal(),
    ], className="container")



app.scripts.append_script({"external_url": ['https://code.jquery.com/jquery-3.2.1.min.js',]})


#show hide dropdown / text field
@app.callback(
    [Output('my-dropdown', 'style'),
     Output('extract_div', 'style'),],
    [Input('radio-div', 'value')])
def display_search_field(value):
    if value == 'EX':
        return {"display": "none"},{"display": "block"}
    else:
        return {"display": "block"},{"display": "none"}





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
    stock_data_df['timestamp'] = stock_data_df['timestamp'].dt.date
    trace1.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"], y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["open"],mode='lines',
        opacity=0.7, name=f'Open', textposition='bottom center'))
    trace2.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"], y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["close"],mode='lines',
        opacity=0.6 , name=f'Close',textposition='bottom center'))



    traces = [trace1, trace2]
    data = [val for sublist in traces for val in sublist]
    figure = {'data': data,
        'layout': go.Layout(colorway=["#000080", '#318af2'],
            title=f"Opening and Closing Prices for " + dropdown[selected_dropdown_value],
            xaxis={ 'type': 'date'},yaxis={"title":"Price (USD)"},
            margin = go.layout.Margin(l=60, r=10, b=40, t=50, ),)}
    return figure

@app.callback(Output('pie-chart', 'figure'),
              [Input('my-dropdown', 'value'),
               Input('my-graph', 'clickData'),])
def update_piechart(selected_dropdown_value,stock_clickData):
    dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google", "FB": 'Facebook'}

    #fetch tweet data
    label_data_dict = es.search(index='tweets_data', body={"size": 100, "query": {"match": {"company_name": dropdown[selected_dropdown_value]}}})
    initial_df = pd.DataFrame.from_dict(label_data_dict['hits']['hits'])
    label_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)

    #convert tweet data to timestamp
    label_data_df['date'] = pd.to_datetime(label_data_df.date, infer_datetime_format=True)
    label_data_df['date'] = label_data_df['date'].dt.date
    label_data_df['date'] = pd.to_datetime(label_data_df['date'], errors='coerce')

    #fetch news data
    news_data_dict = es.search(index='news_data', body={"size": 100, "query": {"match": {"company_name": dropdown[selected_dropdown_value]}}})
    initial_df = pd.DataFrame.from_dict(news_data_dict['hits']['hits'])
    news_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)

    #convert news data to timestamp
    news_data_df['timestamp'] = pd.to_datetime(news_data_df.timestamp, infer_datetime_format=True)
    news_data_df['timestamp'] = news_data_df['timestamp'].dt.date
    news_data_df['timestamp'] = pd.to_datetime(news_data_df['timestamp'], errors='coerce')

    if stock_clickData:
        date = stock_clickData['points'][0]['x']
        news_data_df = news_data_df.loc[news_data_df['timestamp'] == date]
        label_data_df = label_data_df.loc[label_data_df['date'] == date]


    negative = label_data_df.loc[label_data_df.label == 'Negative', 'label'].count() + news_data_df.loc[news_data_df.sentiment == 'Negative', 'sentiment'].count()
    positive = label_data_df.loc[label_data_df.label == 'Positive', 'label'].count() + news_data_df.loc[news_data_df.sentiment == 'Positive', 'sentiment'].count()

    data = [go.Pie(values=[positive.item(),negative.item()], labels=['Positive','Negative'],marker={'colors': ["#000080", '#318af2']}, )]

    figure = {
        'data':data,
        'layout': go.Layout(
            #paper_bgcolor='rgba(0,0,0,0)',
            #plot_bgcolor='rgba(0,0,0,0)'
           legend=dict(orientation='h',yanchor='bottom',xanchor='center',y=1.2, x=0.5, ), margin=go.layout.Margin(l=10, r=10, b=10, t=10, ),
    ),
    }

    return figure


@app.callback(Output('news_table_data', 'data'),
              [Input('my-dropdown', 'value'),
               Input('pie-chart', 'clickData'),
               Input('my-graph', 'clickData'),])
def update_news_feed(selected_dropdown_value,clickData, stock_clickData):
    dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google", }
    news_data_dict = es.search(index='news_data', body={"size": 100, "query": {"match": {"company_name": dropdown[selected_dropdown_value] }}})
    initial_df = pd.DataFrame.from_dict(news_data_dict['hits']['hits'])
    news_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)

    news_data_df['timestamp'] = pd.to_datetime(news_data_df.timestamp, infer_datetime_format=True)
    news_data_df['timestamp'] = news_data_df['timestamp'].dt.date
    news_data_df['timestamp'] = pd.to_datetime(news_data_df['timestamp'], errors='coerce')

    if clickData:
        sentiment = clickData['points'][0]['label']
        news_data_df = news_data_df.loc[news_data_df['sentiment'] == sentiment]

    if stock_clickData:
        date = stock_clickData['points'][0]['x']
        news_data_df = news_data_df.loc[news_data_df['timestamp'] == date]

    news_data_df = news_data_df.loc[:, ['title']]

    return news_data_df.head(20).to_dict('records')





# hide/show modal for news table
@app.callback(
    [Output("news_modal", "style"),
     Output("news_modal_data", "children"),

     ],
    [Input('news_table_data', "data"),
     Input('news_table_data',"selected_rows"),
    ]
)


def display_news_modal_callback(rows,selected_rows):
    if selected_rows is not 0:
        #selected_list = [rows[i] for i in selected_rows]
        dff = pd.DataFrame(rows).iloc[selected_rows]

        news_modal_dict = es.search(index='news_data', body={"size": 1, "query": {"match": {"title": dff['title'].to_json() }}})
        initial_df = pd.DataFrame.from_dict(news_modal_dict['hits']['hits'])
        news_modal_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)],
                                  axis=1)


        return {"display": "block"}, html.Div([
            #html.Div([ news_modal_df['source'].iloc[0]], className='tweet_class' ),
            html.Div([html.P(['Title: '], className='modal-label'),news_modal_df['title'].iloc[0]],className='tweet_class heading'),
            html.Div([html.P(['Date: '], className='modal-label'), news_modal_df['timestamp'].iloc[0]],className='tweet_class'),
            #html.Div([news_modal_df['urlToImage'].iloc[0]], className='tweet_class'),
            html.Div([html.P(['Description: '], className='modal-label'),news_modal_df['description'].iloc[0]],className='tweet_class'),
            html.Div([html.P(['Link: '], className='modal-label'),html.A(news_modal_df['url'].iloc[0], href=news_modal_df['url'].iloc[0], target="_blank"), ], className='tweet_class'),
            html.Div([html.P(['Sentiment: '], className='modal-label'),news_modal_df['sentiment'].iloc[0]], className='tweet_class'),

        ], id='news_modal_div' )


    else:
        return {"display": "none"}, 2



# reset to 0 add button n_clicks property for tweet table
@app.callback(

        Output('news_table_data',"selected_rows"),
    [
        Input("news_modal_close", "n_clicks"),
    ],
)
def close_modal_callback(n):
      return 0






@app.callback(Output('tweet_table_data', 'data'),
              [Input('my-dropdown', 'value'),
               Input('pie-chart', 'clickData'),
               Input('my-graph', 'clickData'),])

def update_tweet_feed(selected_dropdown_value,clickData,stock_clickData ):
    dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google", "FB":'Facebook' }
    tweet_data_dict = es.search(index='tweets_data', body={"size": 100, "query": {"match": {"company_name": dropdown[selected_dropdown_value] }}})
    initial_df = pd.DataFrame.from_dict(tweet_data_dict['hits']['hits'])
    tweet_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)

    tweet_data_df['date'] = pd.to_datetime(tweet_data_df.date, infer_datetime_format=True)
    tweet_data_df['date'] = tweet_data_df['date'].dt.date
    tweet_data_df['date'] = pd.to_datetime(tweet_data_df['date'], errors='coerce')

    if clickData:
        sentiment = clickData['points'][0]['label']
        tweet_data_df = tweet_data_df.loc[tweet_data_df['label'] == sentiment]

    if stock_clickData:
        date = stock_clickData['points'][0]['x']
        tweet_data_df = tweet_data_df.loc[tweet_data_df['date'] == date]

    tweet_data_df = tweet_data_df.loc[:,['message']]

    #{'name':'Tweet Description'}, {'name':'Sentiment'}
    return tweet_data_df.head(20).to_dict('records')



# hide/show modal for tweet table
@app.callback(
    [Output("tweet_modal", "style"),
     Output("row_no", "children"),

     ],
    [Input('tweet_table_data', "data"),
     Input('tweet_table_data',"selected_rows"),]
)
def display_tweet_modal_callback(rows,selected_rows):
    if selected_rows is not 0:
        #selected_list = [rows[i] for i in selected_rows]
        dff = pd.DataFrame(rows).iloc[selected_rows]

        tweet_modal_dict = es.search(index='tweets_data', body={"size": 1, "query": {"match": {"message": dff['message'].to_json() }}})
        initial_df = pd.DataFrame.from_dict(tweet_modal_dict['hits']['hits'])
        tweet_modal_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)],
                                  axis=1)
        tweet_modal_df['date'] = pd.to_datetime(tweet_modal_df.date, infer_datetime_format=True)
        tweet_modal_df['date'] = tweet_modal_df['date'].dt.date
        tweet_modal_df['date'] = pd.to_datetime(tweet_modal_df['date'], errors='coerce')

        return {"display": "block"}, html.Div([
            html.Div([html.P(['Author: '], className='modal-label'), tweet_modal_df['author'].iloc[0]], className='tweet_class heading' ),
            html.Div([html.P(['Date: '],className='modal-label'), tweet_modal_df['date'].iloc[0]],className='tweet_class'),
            html.Div([html.P(['Tweet: '], className='modal-label'), tweet_modal_df['message'].iloc[0]],className='tweet_class'),
            html.Div([html.P(['Sentiment: '],className='modal-label'), tweet_modal_df['label'].iloc[0]],className='tweet_class'),



        ], id='tweet_modal_div' )


    else:
        return {"display": "none"}, 2




# reset to 0 add button n_clicks property for tweet table
@app.callback(

        Output('tweet_table_data',"selected_rows"),
    [
        Input("opportunities_modal_close", "n_clicks"),
    ],
)
def close_modal_callback(n):
      return 0









#reset clickdata to none in sentiment graph
@app.callback(
    Output('pie-chart', 'clickData'),
[Input('pie-chart-container', 'n_clicks')])
def reset_clickData(n_clicks):
    return None


if __name__ == '__main__':
    app.run_server(debug=False)
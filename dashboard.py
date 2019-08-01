#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
import json
import pandas as pd
import plotly as py
import plotly.graph_objs as go
import random
import spacy
from spacy import displacy
from collections import Counter
import en_core_web_sm
import numpy as np

from eligibilitycheck import eligibilitycheck
from futurepricing import generate_price_df
from elasticsearch import Elasticsearch

nlp = en_core_web_sm.load()


app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True


es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])

if 'DYNO' in os.environ:
	app_name = os.environ['DASH_APP_NAME']
else:
	app_name = 'stock-timeseriesplot'

def context_search(article):
	doc = nlp(article)
	ent = []
	for X in doc:
		if((X.ent_iob_ == "B")& (X.ent_type_== "ORG")):
			ent.append(X.text)
	return(Counter(ent).most_common(10)[0][0],dict(Counter(ent).most_common(10)))


# returns modal (hidden by default)
def modal():
	return html.Div(
		html.Div(
			[html.Div(
					[  # modal header
						html.Div(
							[
								html.Span("Tweet",style={"color": "#000080","fontWeight": "bold","fontSize": "20",},),
								html.Span("×",id="opportunities_modal_close",n_clicks=0,
									style={"float": "right","cursor": "pointer","marginTop": "0","marginBottom": "17",},
								),
							],
							className="row",style={"borderBottom": "1px solid #C8D4E3"},
						),
						# modal data
						html.Div([html.P(id='row_no'),],className="row",style={"paddingTop": "2%"},),

					],className="modal-content",style={"textAlign": "center"},)
			],className="modal",
		),id="tweet_modal",style={"display": "none"},
	)

def news_modal():
	return html.Div(
		html.Div(
			[html.Div(
				[# modal header
					html.Div(
						[
							html.Span("News",style={"color": "#000080","fontWeight": "bold","fontSize": "20",},),
							html.Span("×",id="news_modal_close",n_clicks=0,
								style={"float": "right","cursor": "pointer","marginTop": "0","marginBottom": "17",},
							),
						],
						className="row",style={"borderBottom": "1px solid #C8D4E3"},
					),
					# modal data
					html.Div([html.P(id='news_modal_data'),],className="row",style={"paddingTop": "2%"},),

				],className="modal-content",style={"textAlign": "center"},)
			],className="modal",
		),id="news_modal",style={"display": "none"},
	)

def critical_table_modal():
	return html.Div(
		html.Div(
			[html.Div(
				[# modal header
					html.Div(
						[
							html.Span("Critical Values and Ratios",style={"color": "#000080","fontWeight": "bold","fontSize": "20",},),
							html.Span("×",id="critical_modal_close",n_clicks=0,
								style={"float": "right","cursor": "pointer","marginTop": "0","marginBottom": "17",},
							),
						],
						className="row",style={"borderBottom": "1px solid #C8D4E3"},
					),
					# modal data
					html.Div([html.Div([],id='critical_modal_data'),],className="row",style={"paddingTop": "2%"},),

				],className="modal-content",style={"textAlign": "center"},)
			],className="modal",
		),id="critical_modal",style={"display": "none"},
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

					html.Div([dcc.Input(id='text_search',value = None, placeholder='Enter a extract....', ),
					html.Button('Submit', id='button'),], id='extract_div',style={"display": "none"} ),

					html.Div([dcc.Graph(id = 'wordcloud',style = {"display": "block",}),],id = 'wordcloud-div',style = {"display": "none"}),
					html.Div(id = 'test'),

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
				], className='sentiment_div'),

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
						css=[{'selector': '.dash-cell div.dash-cell-value',
							'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
							 }],

						)], id ='tweet_table', className='div-50'),
				], className='sentiment_div', ),

				]),

			dcc.Tab(label='Earnings Call Analysis', children=[

				html.Div([
					html.Div([html.H3('Buy / Sell Decision'), ], className='div-33'),
					html.Div([html.H3('Analyst Rating'), ], className='div-33'),
					html.Div([html.H3('Warning Flags'), ], className='div-33'),
				], className='sentiment_div', ),

				html.Div([

					html.Div([dcc.Graph(id='decision-chart', config={'displayModeBar': False}, style={'align':'center', } ), ], id='decision-chart-div',className='indicators',),

					html.Div([],id='expected-future-price-table',style={'display':'none'},),
					html.Div([html.Div([html.Button('Current', id='current-button',n_clicks_timestamp=0, className='div-30 button'),
								html.Button('1 Month Ago', id='one_month',n_clicks_timestamp=0, className='div-30 button'),
								html.Button('3 Month Ago', id='three_month',n_clicks_timestamp=0, className='div-30 button'),], className='buttons-container' ),
							  dcc.Graph(id='analyst-chart', config={'displayModeBar': False}, style={'align':'center', } ), ],style={'display':'block'}, className='indicators',),
					html.Div([html.Table(id='reason-list'),],className='indicators',),

				],className='sentiment_div',),

				html.Div([
					html.Div([html.H3('Critical varables and Ratios'), ], className='div-40'),
					html.Div([html.H3('Technical indicators'), ], className='div-60'),
				], className='sentiment_div', ),

				html.Div([
					html.Div([dcc.Dropdown(id='critical-indicators-dropdown',
							options=[{'label': 'Earnings Per Share (EPS)', 'value': 'eps'},
								{'label': 'EPS Growth', 'value': 'epsgrowth'},
								{'label': 'Net Income', 'value': 'netincome'},
								{'label': 'Share Holder Equity', 'value': 'shareholderequity'},
								{'label': 'Return on Assests (ROA)', 'value': 'roa'},
								{'label': 'Long Term Debt', 'value': 'longtermdebt'},
								{'label': 'Interest Expense', 'value': 'interestexpense'},
								{'label': 'EBITDA', 'value': 'ebitda'},
								{'label': 'Return on Equity (ROE) ', 'value': 'roe'},
								{'label': 'Interest Coverage Ratio', 'value': 'interestcoverageratio'},
									],searchable=False, value='eps',), ], className='div-40'),
					html.Div([dcc.Dropdown(id='tech-indicators-dropdown',
							options=[{'label': 'Simple Moving Average (SMA)', 'value': 'SMA'},
									 {'label': 'Exponetial Moving Average (EMA)', 'value': 'EMA'},
									{'label': 'Relative Strength Index (RSI)', 'value': 'RSI'},
									],searchable=False, value='SMA',), ], className='div-60'),
				], className='sentiment_div', ),

				html.Div([

					html.Div([dcc.Graph(id='critical-graph', config={'displayModeBar': False}, ),   ],className='div-40 pie-chart-div',),
					html.Div([dcc.Graph(id='indicators-graph', config={'displayModeBar': False}, ), ], className='div-60 pie-chart-div',),

				],className='sentiment_div',),

			]),
		]),

	], className='right-container'),
	modal(), news_modal(), critical_table_modal(),
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




@app.callback(
	Output('wordcloud', 'style'),
	[Input('button','n_clicks')])
def display_wordcloud_onclick(value):
	if(value != None):
		return {"display": "block"}
	else:
		return {"display":'none'}

@app.callback(
	Output('wordcloud-div', 'style'),
	[Input('button','n_clicks')])
def display_wordcloud_onclick1(value):
	if(value != None):
		return {'box-shadow': '0px 0px 5px 0px rgba(0,0,0,0.2)'}
	else:
		return {"display":'none'}



@app.callback(Output('my-graph', 'figure'),
			  [Input('my-dropdown', 'value'),
			  Input('text_search','value'),
			  Input('wordcloud','clickData')])
def update_graph(selected_dropdown_value,text_search,wordcloud_data):
	if(text_search != None):
		company  = context_search(text_search)
		company = company[0]
		dropdown1 = {"Microsoft": "MSFT", "Apple": "AAPL", "Google": "GOOG", }
		if wordcloud_data:
			selected_dropdown_value1 = wordcloud_data['points'][0]['text']
		else:
			selected_dropdown_value1 = company
		selected_dropdown_value = dropdown1[selected_dropdown_value1]
	else:
		selected_dropdown_value = selected_dropdown_value


	dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google", }
	trace1 = []
	trace2 = []

	global stock_data_df

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
			   Input('my-graph', 'clickData'),
			   Input('text_search','value'),
			   Input('wordcloud','clickData')])
def update_piechart(selected_dropdown_value,stock_clickData,text_search,wordcloud_data):
	if(text_search != None):
		company  = context_search(text_search)
		company = company[0]
		if wordcloud_data:
			selected_dropdown_value = wordcloud_data['points'][0]['text']
		else:
			selected_dropdown_value = company
		label_data_dict = es.search(index='tweets_data', body={"size": 100, "query": {"match": {"company_name": selected_dropdown_value}}})
		news_data_dict = es.search(index='news_data', body={"size": 100, "query": {"match": {"company_name": selected_dropdown_value}}})
	else:
		selected_dropdown_value = selected_dropdown_value
		dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google"}
		label_data_dict = es.search(index='tweets_data', body={"size": 100, "query": {"match": {"company_name": dropdown[selected_dropdown_value]}}})
		news_data_dict = es.search(index='news_data', body={"size": 100, "query": {"match": {"company_name": dropdown[selected_dropdown_value]}}})

	initial_df = pd.DataFrame.from_dict(label_data_dict['hits']['hits'])
	label_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)
	label_data_df['date'] = pd.to_datetime(label_data_df.date, infer_datetime_format=True)
	label_data_df['date'] = label_data_df['date'].dt.date
	label_data_df['date'] = pd.to_datetime(label_data_df['date'], errors='coerce')


	
	initial_df = pd.DataFrame.from_dict(news_data_dict['hits']['hits'])
	news_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)

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


@app.callback(Output('indicators-graph', 'figure'),
              [Input('my-dropdown', 'value'),
			   Input('tech-indicators-dropdown', 'value'),
			   Input('text_search', 'value'),
			   Input('wordcloud', 'clickData')])
def update_indicator_graph(selected_dropdown_value,tech_dropdown_value,text_search,wordcloud_data):
	if text_search is not None:
		company = context_search(text_search)
		company = company[0]
		dropdown1 = {"Microsoft": "MSFT", "Apple": "AAPL", "Google": "GOOG", }
		if wordcloud_data:
			selected_dropdown_value1 = wordcloud_data['points'][0]['text']
		else:
			selected_dropdown_value1 = company
		selected_dropdown_value = dropdown1[selected_dropdown_value1]
	else:
		selected_dropdown_value = selected_dropdown_value

	trace1 = []
	trace2 = []

	data_dict = es.search(index='stock_data', body={"size": 50, "query": {"match": {"stock-symbol": selected_dropdown_value}}})
	initial_df = pd.DataFrame.from_dict(data_dict['hits']['hits'])
	stock_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)],axis=1)

	stock_data_df['timestamp'] = pd.to_datetime(stock_data_df.timestamp, infer_datetime_format=True)

	if tech_dropdown_value == 'SMA' or tech_dropdown_value == 'EMA':
		trace1.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"],
			y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["close"],
			mode='lines',opacity=0.7, name=f'Close', textposition='bottom center'))
		if tech_dropdown_value == 'SMA':
			trace2.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"], y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["close"].rolling(window=10).mean(),mode='lines',
			opacity=0.6 , name=f'SMA',textposition='bottom center'))
		elif tech_dropdown_value == 'EMA':
			trace2.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"],
				y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["close"].ewm(span=10,
				adjust=False).mean(), mode='lines',opacity=0.7, name=f'EMA', textposition='bottom center'))

	if tech_dropdown_value == 'RSI':
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
								 y=RSI2, mode='lines',
								 opacity=0.7, name=f'RSI based on SMA', textposition='bottom center'))

	traces = [trace1, trace2]
	data = [val for sublist in traces for val in sublist]
	figure = {'data': data,
        'layout': go.Layout(colorway=["#000080", '#318af2'],
            legend_orientation="h", margin=go.layout.Margin(l=60, r=10, b=0, t=5,),
            xaxis={'type': 'date'},yaxis={"title":"Price (USD)"})}
	return figure





# for the critical variables and Ratio graph
@app.callback(Output('critical-graph', 'figure'),
			  [Input('my-dropdown', 'value'),
			   Input('critical-indicators-dropdown', 'value'),
			   Input('text_search', 'value'),
			   Input('wordcloud', 'clickData')])
def generate_critical_graph(selected_dropdown_value,critical_dropdown_value,text_search,wordcloud_data):
	if (text_search != None):
		company = context_search(text_search)
		company = company[0]
		dropdown1 = {"Microsoft": "MSFT", "Apple": "AAPL", "Google": "GOOG", }
		if wordcloud_data:
			selected_dropdown_value1 = wordcloud_data['points'][0]['text']
		else:
			selected_dropdown_value1 = company
		selected_dropdown_value = dropdown1[selected_dropdown_value1]
	else:
		selected_dropdown_value = selected_dropdown_value

	financial_data_dict = es.search(index='financial_data',body={"size": 2000, "query": {"match": {"stock-symbol": selected_dropdown_value}}})
	initial_df = pd.DataFrame.from_dict(financial_data_dict['hits']['hits'])
	financial_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)],
								  axis=1)
	for i in ['netincome', 'shareholderequity', 'longtermdebt', 'interestexpense', 'ebitda']:
		financial_data_df[i] = financial_data_df[i].astype('int64')

	financial_data_df['interestcoverageratio'] = financial_data_df.ebitda / financial_data_df.interestexpense

	financialreportingwritten = financial_data_df
	financialreportingwritten[['roe', 'interestcoverageratio']] = np.round(financial_data_df[['roe', 'interestcoverageratio']], 2)

	data = [go.Bar(x=financialreportingwritten['year'], y = financialreportingwritten[financialreportingwritten[critical_dropdown_value] >= 0][critical_dropdown_value], marker_color='#28559A', name ='Positive' ),
			go.Bar(x=financialreportingwritten['year'], y=financialreportingwritten[financialreportingwritten[critical_dropdown_value] < 0][critical_dropdown_value],marker_color='#7ED5EA', name='Negative')
			]

	figure = {
		'data': data,
		'layout': go.Layout( xaxis={'type': 'date'},yaxis={"title":"Price (USD)"},
			margin = go.layout.Margin(l=60, r=10, b=40, t=50, ), showlegend=False,)
	}


	return figure


# for the Analyst Rating graph
@app.callback(Output('analyst-chart', 'figure'),
				[Input('my-dropdown', 'value'),
				Input('current-button', 'n_clicks_timestamp'),
				Input('one_month', 'n_clicks_timestamp'),
				Input('three_month', 'n_clicks_timestamp'),
				Input('text_search', 'value'),
				Input('wordcloud', 'clickData')])
def generate_analyst_graph(selected_dropdown_value,current,one_month,three_month,text_search,wordcloud_data):
	if (text_search != None):
		company = context_search(text_search)
		company = company[0]
		dropdown1 = {"Microsoft": "MSFT", "Apple": "AAPL", "Google": "GOOG", }
		if wordcloud_data:
			selected_dropdown_value1 = wordcloud_data['points'][0]['text']
		else:
			selected_dropdown_value1 = company
		selected_dropdown_value = dropdown1[selected_dropdown_value1]
	else:
		selected_dropdown_value = selected_dropdown_value

	analyst_data_dict = es.search(index='analyst_data',
									body={"size": 2000, "query": {"match": {"stock-symbol": selected_dropdown_value}}})
	initial_df = pd.DataFrame.from_dict(analyst_data_dict['hits']['hits'])
	analyst_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)],
								  axis=1)
	if int(current) > int(one_month) and int(current) > int(three_month):
		analyst_data_df = analyst_data_df[analyst_data_df['duration'] == 'current']
	elif int(one_month) > int(current) and int(one_month) > int(three_month) :
		analyst_data_df = analyst_data_df[analyst_data_df['duration'] == 'one_month']
	elif int(three_month) > int(current) and int(three_month) > int(one_month):
		analyst_data_df = analyst_data_df[analyst_data_df['duration'] == 'three_month']
	else:
		analyst_data_df = analyst_data_df[analyst_data_df['duration'] == 'current']

	data = [go.Bar(x=analyst_data_df[['buy', 'hold', 'sell']].values.tolist()[0],
				   y=['Buy', 'Hold', 'Sell'],orientation='h',
				   marker = dict(color=[ "#28559A", '#4B9FE1','#7ED5EA']),),
			]

	title ='Current Analyst Rating'
	figure = {
		'data': data,
		'layout': go.Layout(title= title ,
							margin=go.layout.Margin(l=40, r=40, b=30, t=30, ), showlegend=False, )
	}


	return figure



@app.callback(Output('news_table_data', 'data'),
			  [Input('my-dropdown', 'value'),
			   Input('pie-chart', 'clickData'),
			   Input('my-graph', 'clickData'),
			   Input('wordcloud','clickData'),
			   Input('text_search','value')])
def update_news_feed(selected_dropdown_value,clickData, stock_clickData,wordcloud_data,text_search):
	if(text_search != None):
		company  = context_search(text_search)
		company = company[0]
		if wordcloud_data:
			selected_dropdown_value = wordcloud_data['points'][0]['text']
		else:
			selected_dropdown_value = company
		news_data_dict = es.search(index='news_data', body={"size": 100, "query": {"match": {"company_name": selected_dropdown_value }}})
	else:
		selected_dropdown_value = selected_dropdown_value
		dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google"}
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
			   Input('my-graph', 'clickData'),
			   Input('wordcloud','clickData'),
			   Input('text_search','value')])

def update_tweet_feed(selected_dropdown_value,clickData,stock_clickData,wordcloud_data,text_search ):
	if(text_search != None):
		company  = context_search(text_search)
		company1 = company[0]
		print(selected_dropdown_value)
		if wordcloud_data:
			selected_dropdown_value = wordcloud_data['points'][0]['text']
		else:
			selected_dropdown_value = company1
		tweet_data_dict = es.search(index='tweets_data', body={"size": 100, "query": {"match": {"company_name": selected_dropdown_value }}})
	else:
		selected_dropdown_value = selected_dropdown_value
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
		return {"display": "none"}, 0




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


@app.callback(
	Output('wordcloud', 'figure'),
[Input('button', 'n_clicks')],
[State('text_search','value')])
def wordcloud(clicks,y):
	x=context_search(y)
	print(x[1])
	words = list(x[1].keys())


	frequency = list(x[1].values())

	lower, upper = 15, 45
	frequency = [((x - min(frequency)) / (max(frequency) - min(frequency))) * (upper - lower) + lower for x in frequency]


	percent = [0.362086258776329, 0.13139418254764293, 0.11802072885322636, 0.055834169174189235, 0.041123370110330994, 0.03978602474088933, 0.02774991641591441, 0.02139752591106653, 0.01905717151454363, 0.015379471748579069]

	lenth = len(words)
	colors = [py.colors.DEFAULT_PLOTLY_COLORS[random.randrange(1, 10)] for i in range(lenth)]

	data = go.Scatter(
	x=[5,1,2,4,3,6,7,8,9,10],
	y=random.choices(range(lenth), k=lenth),
	mode='text',
	text=words,
	hovertext=['{0}{1}'.format(w, f) for w,f in zip(words, frequency)],
	hoverinfo='text',
	textfont={'size': frequency*2, 'color': colors})
	layout = go.Layout({'xaxis': {'showgrid': False, 'showticklabels': False, 'zeroline': False},
						'yaxis': {'showgrid': False, 'showticklabels': False, 'zeroline': False},
						}, margin = go.layout.Margin(l=20, r=10, b=40, t=10, ), )

	fig = go.Figure(data=[data], layout=layout,)
	return fig




# for the reason-list
@app.callback(Output('reason-list', 'children'), [Input('my-dropdown', 'value')])
def generate_reason_list(selected_dropdown_value):
	global financial_data_df  # Needed to modify global copy of financialreportingdf

	financial_data_dict = es.search(index='financial_data',
									body={"size": 2000, "query": {"match": {"stock-symbol": selected_dropdown_value}}})
	initial_df = pd.DataFrame.from_dict(financial_data_dict['hits']['hits'])
	financial_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)],
								  axis=1)
	for i in ['netincome', 'shareholderequity', 'longtermdebt', 'interestexpense', 'ebitda']:
		financial_data_df[i] = financial_data_df[i].astype('int64')

	financial_data_df['interestcoverageratio'] = financial_data_df.ebitda / financial_data_df.interestexpense

	#financialreportingdf = getfinancialreportingdfformatted(selected_dropdown_value.strip().lower()).reset_index()
	reasonlist = eligibilitycheck(selected_dropdown_value.strip().lower(), financial_data_df)
	# print(financialreportingdf)
	# Header
	return [html.Tr(html.Td(reason)) for reason in reasonlist]



# for the expected-future-price-table
@app.callback(
		[Output('expected-future-price-table', 'children'),
		 Output('decision-chart', 'figure'),],
		[Input('my-dropdown', 'value'),
		Input('text_search', 'value'),
	   	Input('wordcloud', 'clickData')])
def generate_future_price_table(selected_dropdown_value,text_search,wordcloud_data, max_rows=10):
	global stock_data_df
	global financial_data_df

	financial_data_dict = es.search(index='financial_data',
									body={"size": 2000, "query": {"match": {"stock-symbol": selected_dropdown_value}}})
	initial_df = pd.DataFrame.from_dict(financial_data_dict['hits']['hits'])
	financial_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)],
								  axis=1)
	for i in ['netincome', 'shareholderequity', 'longtermdebt', 'interestexpense', 'ebitda']:
		financial_data_df[i] = financial_data_df[i].astype('int64')

	data_dict = es.search(index='stock_data',
						  body={"size": 2000, "query": {"match": {"stock-symbol": selected_dropdown_value}}})
	initial_df = pd.DataFrame.from_dict(data_dict['hits']['hits'])

	stock_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)
	stock_data_df['timestamp'] = pd.to_datetime(stock_data_df.timestamp, infer_datetime_format=True)
	stock_data_df['timestamp'] = stock_data_df['timestamp'].dt.date

	pricedf = generate_price_df(selected_dropdown_value.strip(), financial_data_df, stock_data_df, 0.15,0.15)

	data = [go.Pie(
		values=[50, 16.5, 17, 16.5],
		labels=["Recommendation", "Hold", "Sell",  "Buy"],
		domain={"x": [0, .8]},
		marker_colors=['#fff', '#4B9FE1','#7ED5EA', '#28559A'],

		name="Gauge",
		hole=.3,
		direction="clockwise",
		rotation=90,
		showlegend=False,
		hoverinfo="none",
		textinfo="label",
		textposition="inside"
	)]

	if pricedf.decision[0] == 'SELL':
		path = 'M 0.395 0.5 L 0.31 0.57 L 0.405 0.5 Z'
		back_color = '#7ED5EA'
		color = '#000000'
	elif pricedf.decision[0] == 'HOLD':
		path = 'M 0.395 0.5 L 0.4 0.65  L 0.405 0.5 Z'
		back_color = '#4B9FE1'
		color = '#000000'
	elif pricedf.decision[0] == 'BUY':
		path = 'M 0.395 0.5 L 0.49 0.57 L 0.405 0.5 Z'
		back_color = '#28559A'
		color = '#ffffff'
	figure = {
		'data': data,
		'layout': go.Layout(

			shapes=[
				dict(type='path', path=path, fillcolor='rgba(44, 160, 101, 0.5)',
					 line_width=0.5, xref='paper', yref='paper')],

			margin=go.layout.Margin(l=30, r=0, b=0, t=20, ),
		),
	}


	# Header
	return  html.Div([
			html.Div([html.P(['Annual Growth Rate'], className='modal-label div-25'),
				html.P(['Last EPS ($)'], className='modal-label div-25'),
				html.P(['Future EPS ($)'], className='modal-label div-25'),
				html.P(['PE Ratio ($)'], className='modal-label div-25')
			], className='sentiment_div'),
			html.Div([html.P([round(pricedf['annualgrowthrate'].iloc[0],2)], className='modal-label div-25'),
				html.P([round(pricedf['lasteps'].iloc[0], 2)], className='modal-label div-25'),
				html.P([round(pricedf['futureeps'].iloc[0], 2)], className='modal-label div-25'),
				html.P([round(pricedf['peratio'].iloc[0], 2)], className='modal-label div-25'),
			], className='sentiment_div'),
			html.Div([html.P(['Future Value ($)'], className='modal-label div-25'),
				html.P(['Present Value ($)'], className='modal-label div-25'),
				html.P(['Margin Price ($)'], className='modal-label div-25'),
				html.P(['Last Share Price ($)'], className='modal-label div-25')
			], className='sentiment_div'),
			html.Div([html.P([round(pricedf['FV'].iloc[0], 2)], className='modal-label div-25'),
				html.P([round(pricedf['PV'].iloc[0], 2)], className='modal-label div-25'),
				html.P([round(pricedf['marginprice'].iloc[0], 2)], className='modal-label div-25'),
				html.P([round(pricedf['lastshareprice'].iloc[0], 2)], className='modal-label div-25'),
			], className='sentiment_div'),
			html.Div([html.Div([pricedf['decision'].iloc[0]],
						style={'background-color': back_color, 'color': color}, id='decision-div', className='div-40')]
					 ,className='sentiment_div')

		], id='expected_price_modal_div'), figure


@app.callback(
		[Output('critical_modal', 'style'),
		Output('critical_modal_data', 'children'), ],
		[Input('decision-chart', 'clickData'),],
		[State('expected-future-price-table', 'children'),])
def generate_future_price_table(clickData, pricetable):
	if clickData is not 0:
		return {"display": "block"}, pricetable
	else:
		return {"display": "none"}, pricetable


#reset clickdata to none in sentiment graph
@app.callback(
	Output('decision-chart', 'clickData'),
[Input("critical_modal_close", "n_clicks")])
def reset_clickdata(n_clicks):
	return 0


if __name__ == '__main__':
	app.run_server(debug=False)
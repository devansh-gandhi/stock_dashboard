import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objs as go
import numpy as np
from src.view.eligibilitycheck import eligibilitycheck
from src.view.futurepricing import generate_price_df
from elasticsearch import Elasticsearch
from src.view.app import app
import os, base64, re, logging

#es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])


def get_es():
	logging.basicConfig(level=logging.INFO)

	os.environ['BONSAI_URL'] = 'https://1uxb44vnlu:26dsa53ns7@ash-591153868.us-east-1.bonsaisearch.net'

	try:
		bonsai = os.environ.get('BONSAI_URL')
	except Exception as e:
		print("{0}".format(e.__class__))

	# Parse the auth and host from env:
	auth = re.search('https\:\/\/(.*)\@', bonsai).group(1).split(':')
	host = bonsai.replace('https://%s:%s@' % (auth[0], auth[1]), '')

	es_header = [{
		'host': host,
		'port': 443,
		'use_ssl': True,
		'http_auth': (auth[0], auth[1])
	}]

	es = Elasticsearch(es_header)

	return es



def critical_table_modal():
	return html.Div(
		html.Div(
			[html.Div(
				[
					html.Div(
						[
							html.Span("Critical Values and Ratios",
									  style={"color": "#000080","fontWeight": "bold","fontSize": "20",},),
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


layout = html.Div([

	html.Div([
		html.Div([html.H3('Buy / Sell Decision'), ], className='div-33'),
		html.Div([html.H3('Analyst Rating'), ], className='div-33'),
		html.Div([html.H3('Warning Flags'), ], className='div-33'),
	], className='sentiment_div', ),

	html.Div([

		html.Div([dcc.Graph(id='decision-chart', config={'displayModeBar': False}, style={'align': 'center', }),
				  html.Table(id='reason-list'),],
				 id='decision-chart-div', className='indicators', ),

		html.Div([], id='expected-future-price-table', style={'display': 'none'}, ),
		html.Div(
			[html.Div([html.Button('Current', id='current-button', n_clicks_timestamp=0, className='div-30 button'),
					html.Button('1 Month Ago', id='one_month', n_clicks_timestamp=0, className='div-30 button'),
					html.Button('3 Month Ago', id='three_month', n_clicks_timestamp=0, className='div-30 button'), ],
					className='buttons-container'),
			 dcc.Graph(id='analyst-chart', config={'displayModeBar': False}, style={'align': 'center', }), ],
			style={'display': 'block'}, className='indicators', ),

		html.Div([ ], className='indicators', ),


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
			], searchable=False, value='eps', ), ], className='div-40'),
		html.Div([dcc.Dropdown(id='tech-indicators-dropdown',
							options=[{'label': 'Simple Moving Average (SMA)', 'value': 'SMA'},
										{'label': 'Exponetial Moving Average (EMA)', 'value': 'EMA'},
										{'label': 'Relative Strength Index (RSI)', 'value': 'RSI'},
							], searchable=False, value='SMA', ), ], className='div-60'),
	], className='sentiment_div', ),

	html.Div([

		html.Div([dcc.Graph(id='critical-graph', config={'displayModeBar': False}, ), ],
				 className='div-40 pie-chart-div', ),
		html.Div([dcc.Graph(id='indicators-graph', config={'displayModeBar': False}, ), ],
				 className='div-60 pie-chart-div', ),

	], className='sentiment_div', ),

	critical_table_modal(),
	html.Div([], id='div-hidden', style={'display': 'none'}, ),

])





@app.callback(Output('indicators-graph', 'figure'),
            [Input('tech-indicators-dropdown', 'value'),],
			[State('selected_dropdown_store', 'data')])
def update_indicator_graph(tech_dropdown_value,selected_dropdown_value):

	trace1 = []
	trace2 = []
	es = get_es()
	data_dict = es.search(index='stock_data', body={"size": 50, "query": {"match": {"stock-symbol": selected_dropdown_value}}})
	initial_df = pd.DataFrame.from_dict(data_dict['hits']['hits'])
	stock_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)],axis=1)

	stock_data_df['timestamp'] = pd.to_datetime(stock_data_df.timestamp, infer_datetime_format=True)

	if tech_dropdown_value == 'SMA' or tech_dropdown_value == 'EMA':
		trace1.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"],
			y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["close"],
			mode='lines',opacity=0.7, name=f'Close', textposition='bottom center'))
		if tech_dropdown_value == 'SMA':
			trace2.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"],
			y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["close"].rolling(window=10).mean(),
			mode='lines', opacity=0.6 , name=f'SMA',textposition='bottom center'))
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
			[Input('critical-indicators-dropdown', 'value'),],
			[State('selected_dropdown_store', 'data'),]
			)
def generate_critical_graph(critical_dropdown_value,selected_dropdown_value):

	es = get_es()
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
				[
				Input('current-button', 'n_clicks_timestamp'),
				Input('one_month', 'n_clicks_timestamp'),
				Input('three_month', 'n_clicks_timestamp'),
				],
			  [State('selected_dropdown_store', 'data'),]
			  )
def generate_analyst_graph(current,one_month,three_month,selected_dropdown_value):

	es = get_es()
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

	data = [go.Bar(x=analyst_data_df[['sell', 'hold', 'buy']].values.tolist()[0],
				   y=['Sell', 'Hold', 'Buy'],orientation='h',
				   marker = dict(color=[ "#28559A", '#4B9FE1','#7ED5EA']),),
			]

	title ='Current Analyst Rating'
	figure = {
		'data': data,
		'layout': go.Layout(title= title ,
							margin=go.layout.Margin(l=40, r=40, b=30, t=30, ), showlegend=False, )
	}


	return figure





# for the reason-list
@app.callback(Output('reason-list', 'children'),
			  [Input('div-hidden', 'children')],
			  [State('selected_dropdown_store', 'data'),])
def generate_reason_list(no_input, selected_dropdown_value):
	global financial_data_df  # Needed to modify global copy of financialreportingdf

	es = get_es()
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
		[Input('div-hidden', 'children')],
		[State('selected_dropdown_store', 'data'),]
		)
def generate_future_price_table(no_input,selected_dropdown_value, max_rows=10):

	es = get_es()
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
	if clickData is not None:
		return {"display": "block"}, pricetable
	else:
		return {"display": "none"}, pricetable


#reset clickdata to zero in decision graph
@app.callback(
	Output('decision-chart', 'clickData'),
[Input("critical_modal_close", "n_clicks")])
def reset_clickdata(n_clicks):
	return None

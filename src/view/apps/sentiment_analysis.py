import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
import pandas as pd
import plotly as py
import plotly.graph_objs as go
import random
from collections import Counter
import en_core_web_sm
#import spacy
from elasticsearch import Elasticsearch
import os, base64, re, logging
from src.view.app import app

es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])
#nlp = spacy.load('en_core_web_sm')

nlp = en_core_web_sm.load()


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

def context_search(article):
	doc = nlp(article)
	ent = []
	for X in doc:
		if X.ent_iob_ == "B" and X.ent_type_ == "ORG":
			ent.append(X.text)
	return Counter(ent).most_common(10)[0][0],dict(Counter(ent).most_common(10))


# returns modal (hidden by default)
def modal():
	return html.Div(
		html.Div(
			[html.Div(
					[
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
				[
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


layout = html.Div([

	html.Div([
		dcc.RadioItems(id='radio-div',
			options=[
				{'label': ' Company Name', 'value': 'CN'},
				{'label': ' Extract', 'value': 'EX'},
			],
			value='CN',labelStyle={'display': 'inline-block'}
		),

		dcc.Dropdown(id='my-dropdown',
				options=[{'label': 'Microsoft', 'value': 'MSFT'}, {'label': 'Apple', 'value': 'AAPL'},
							{'label': 'Google', 'value': 'GOOG'}], value='MSFT', ),

		html.Div([dcc.Input(id='text_search', value='', placeholder='Enter a extract....', ),
				html.Button('Submit', id='button'), ], id='extract_div', style={"display": "none"}),

		html.Div([dcc.Graph(id='wordcloud', style={"display": "block", }), ], id='wordcloud-div',
				style={"display": "none"}),
		html.Div(id='test'),

	], id='my-dropdown-div'),


	html.Div([
		html.Div([html.Div([dcc.Graph(id='pie-chart', config={'displayModeBar': False}, ), ], className='pie-chart-div',
						id='pie-chart-container')], className='div-30'),
		html.Div([html.Div([dcc.Graph(id='my-graph', config={'displayModeBar': False}, ), ], className='pie-chart-div',
						id='stock-price-container', )], className='div-70'),

	], className='sentiment_div', ),

	html.Div([
		html.Div([html.H3('News Analysis')], className='div-50'),
		html.Div([html.H3('Twitter feed Analysis')], className='div-50'),
	], className='sentiment_div'),

	html.Div([
		html.Div([
			dash_table.DataTable(
				id='news_table_data',
				columns=[{"name": 'Title', "id": 'title'}],
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

		], id='news_table', className='div-50'),

		html.Div([dash_table.DataTable(
			id='tweet_table_data',
			columns=[{"name": 'Tweet Description', "id": 'message'}],
			row_selectable='single',
			style_cell={
				'minWidth': '0px', 'maxWidth': '85%',
				'whiteSpace': 'normal',
				'textAlign': 'left',
			},
			css=[{'selector': '.dash-cell div.dash-cell-value',
				'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
				}],

		)], id='tweet_table', className='div-50'),
	], className='sentiment_div', ),

	modal(), news_modal(),
	html.Div([], id='div-hidden', style={'display': 'none'}, ),

])


# pass dropdown value to dash store
@app.callback(
	[Output('selected_dropdown_store', 'data'),
	 Output('div-hidden', 'children'),],
	[Input('my-dropdown', 'value'),
	Input('wordcloud', 'clickData'),
	Input('button', 'n_clicks')
	],
	[State('text_search', 'value'),]
)
def upload_data_selected_dropdown_store(selected_dropdown_value, wordcloud_data,nclicks,text_search):
	dropdown = {"Microsoft": "MSFT", "Apple": "AAPL", "Google": "GOOG", }
	if nclicks:
		if text_search != '':
			company = context_search(text_search)
			company = company[0]

			selected_dropdown_value1 = company
		if wordcloud_data:
			selected_dropdown_value1 = wordcloud_data['points'][0]['text']

		selected_dropdown_value = dropdown[selected_dropdown_value1]
	else:
		selected_dropdown_value = selected_dropdown_value

	return selected_dropdown_value,selected_dropdown_value


# show hide dropdown / text field
@app.callback(
	[Output('my-dropdown', 'style'),
	 Output('extract_div', 'style'),
	 Output('button', 'n_clicks')],
	[Input('radio-div', 'value')])
def display_search_field(value):
	if value == 'EX':
		return {"display": "none"}, {"display": "block"}, None
	else:
		return {"display": "block"}, {"display": "none"}, None


@app.callback(Output('my-graph', 'figure'),
			[Input('div-hidden', 'children'),],
			[State('selected_dropdown_store', 'data')])
def update_graph(no_input,selected_dropdown_value):


	dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google", }
	trace1 = []
	trace2 = []

	es = get_es()
	data_dict = es.search(index='stock_data',
						body={"size": 50, "query": {"match": {"stock-symbol": selected_dropdown_value}}})
	initial_df = pd.DataFrame.from_dict(data_dict['hits']['hits'])

	stock_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)
	stock_data_df['timestamp'] = pd.to_datetime(stock_data_df.timestamp, infer_datetime_format=True)
	stock_data_df['timestamp'] = stock_data_df['timestamp'].dt.date

	trace1.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"],
							y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["open"],
							mode='lines',opacity=0.7, name=f'Open', textposition='bottom center'))

	trace2.append(go.Scatter(x=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["timestamp"],
							y=stock_data_df[stock_data_df["stock-symbol"] == selected_dropdown_value]["close"],
							mode='lines',opacity=0.6, name=f'Close', textposition='bottom center'))

	traces = [trace1, trace2]
	data = [val for sublist in traces for val in sublist]
	figure = {'data': data,
			'layout': go.Layout(colorway=["#000080", '#318af2'],
								title=f"Opening and Closing Prices for " + dropdown[selected_dropdown_value],
								xaxis={'type': 'date'}, yaxis={"title": "Price (USD)"},
								margin=go.layout.Margin(l=60, r=10, b=40, t=50, ), )}

	return figure


@app.callback(Output('pie-chart', 'figure'),
			[Input('div-hidden', 'children'),
			 Input('my-graph', 'clickData'),],
			[State('selected_dropdown_store', 'data')])
def update_piechart(no_input,stock_clickData,selected_dropdown_value):

	dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google"}
	es = get_es()
	label_data_dict = es.search(index='tweets_data', body={"size": 100, "query": {
			"match": {"company_name": dropdown[selected_dropdown_value]}}})
	news_data_dict = es.search(index='news_data', body={"size": 100, "query": {
			"match": {"company_name": dropdown[selected_dropdown_value]}}})


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
	negative = label_data_df.loc[label_data_df.label == 'Negative', 'label'].count() + news_data_df.loc[
		news_data_df.sentiment == 'Negative', 'sentiment'].count()
	positive = label_data_df.loc[label_data_df.label == 'Positive', 'label'].count() + news_data_df.loc[
		news_data_df.sentiment == 'Positive', 'sentiment'].count()

	data = [go.Pie(values=[positive.item(), negative.item()], labels=['Positive', 'Negative'],
				   marker={'colors': ["#000080", '#318af2']}, )]
	figure = {
		'data': data,
		'layout': go.Layout(
			# paper_bgcolor='rgba(0,0,0,0)',
			# plot_bgcolor='rgba(0,0,0,0)'
			title=f"Sentiment Analysis",
			legend=dict(orientation='h', yanchor='bottom', xanchor='center', y=1.2, x=0.5, ),
			margin=go.layout.Margin(l=10, r=10, b=10, t=30, ),
		),
	}
	return figure


@app.callback(Output('news_table_data', 'data'),
			[Input('div-hidden', 'children'),
			Input('pie-chart', 'clickData'),
			Input('my-graph', 'clickData'),],
			[State('selected_dropdown_store', 'data')])
def update_news_feed(no_input, clickData, stock_clickData, selected_dropdown_value,):

	dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google"}

	es = get_es()
	news_data_dict = es.search(index='news_data', body={"size": 100, "query": {
			"match": {"company_name": dropdown[selected_dropdown_value]}}})

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
	 Input('news_table_data', "selected_rows"),
	 ]
)
def display_news_modal_callback(rows, selected_rows):
	if selected_rows is not 0:
		# selected_list = [rows[i] for i in selected_rows]
		dff = pd.DataFrame(rows).iloc[selected_rows]

		es = get_es()
		news_modal_dict = es.search(index='news_data',
									body={"size": 1, "query": {"match": {"title": dff['title'].to_json()}}})
		initial_df = pd.DataFrame.from_dict(news_modal_dict['hits']['hits'])
		news_modal_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)],
								  axis=1)

		return {"display": "block"}, html.Div([
			# html.Div([ news_modal_df['source'].iloc[0]], className='tweet_class' ),
			html.Div([html.P(['Title: '], className='modal-label'), news_modal_df['title'].iloc[0]],
					 className='tweet_class heading'),
			html.Div([html.P(['Date: '], className='modal-label'), news_modal_df['timestamp'].iloc[0]],
					 className='tweet_class'),
			# html.Div([news_modal_df['urlToImage'].iloc[0]], className='tweet_class'),
			html.Div([html.P(['Description: '], className='modal-label'), news_modal_df['description'].iloc[0]],
					 className='tweet_class'),
			html.Div([html.P(['Link: '], className='modal-label'),
					  html.A(news_modal_df['url'].iloc[0], href=news_modal_df['url'].iloc[0], target="_blank"), ],
					 className='tweet_class'),
			html.Div([html.P(['Sentiment: '], className='modal-label'), news_modal_df['sentiment'].iloc[0]],
					 className='tweet_class'),

		], id='news_modal_div')

	else:
		return {"display": "none"}, 2


# reset to 0 add button n_clicks property for tweet table
@app.callback(

	Output('news_table_data', "selected_rows"),
	[
		Input("news_modal_close", "n_clicks"),
	],
)
def close_modal_callback(n):
	return 0


@app.callback(Output('tweet_table_data', 'data'),
			[Input('div-hidden', 'children'),
			Input('pie-chart', 'clickData'),
			Input('my-graph', 'clickData'), ],
			[State('selected_dropdown_store', 'data')])
def update_tweet_feed(no_input, clickData, stock_clickData,selected_dropdown_value ):

	dropdown = {"MSFT": "Microsoft", "AAPL": "Apple", "GOOG": "Google", "FB": 'Facebook'}
	es = get_es()
	tweet_data_dict = es.search(index='tweets_data', body={"size": 100, "query": {
			"match": {"company_name": dropdown[selected_dropdown_value]}}})


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

	tweet_data_df = tweet_data_df.loc[:, ['message']]

	return tweet_data_df.head(20).to_dict('records')


# hide/show modal for tweet table
@app.callback(
	[Output("tweet_modal", "style"),
	Output("row_no", "children"), ],
	[Input('tweet_table_data', "data"),
	Input('tweet_table_data', "selected_rows"), ]
)
def display_tweet_modal_callback(rows, selected_rows):
	if selected_rows is not 0:

		dff = pd.DataFrame(rows).iloc[selected_rows]
		es = get_es()

		tweet_modal_dict = es.search(index='tweets_data',
									 body={"size": 1, "query": {"match": {"message": dff['message'].to_json()}}})
		initial_df = pd.DataFrame.from_dict(tweet_modal_dict['hits']['hits'])
		tweet_modal_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)],
								   axis=1)
		tweet_modal_df['date'] = pd.to_datetime(tweet_modal_df.date, infer_datetime_format=True)
		tweet_modal_df['date'] = tweet_modal_df['date'].dt.date
		tweet_modal_df['date'] = pd.to_datetime(tweet_modal_df['date'], errors='coerce')

		return {"display": "block"}, html.Div([
			html.Div([html.P(['Author: '], className='modal-label'), tweet_modal_df['author'].iloc[0]],
					 className='tweet_class heading'),
			html.Div([html.P(['Date: '], className='modal-label'), tweet_modal_df['date'].iloc[0]],
					 className='tweet_class'),
			html.Div([html.P(['Tweet: '], className='modal-label'), tweet_modal_df['message'].iloc[0]],
					 className='tweet_class'),
			html.Div([html.P(['Sentiment: '], className='modal-label'), tweet_modal_df['label'].iloc[0]],
					 className='tweet_class'),

		], id='tweet_modal_div')


	else:
		return {"display": "none"}, 0


# reset to 0 add button n_clicks property for tweet table
@app.callback(

	Output('tweet_table_data', "selected_rows"),
	[Input("opportunities_modal_close", "n_clicks"),],
)
def close_modal_callback(n):
	return 0


# reset clickdata to none in sentiment graph
@app.callback(
	Output('pie-chart', 'clickData'),
	[Input('pie-chart-container', 'n_clicks')])
def reset_clickData(n_clicks):
	return None


@app.callback(
	Output('wordcloud', 'figure'),
	[Input('button', 'n_clicks')],
	[State('text_search', 'value')])
def wordcloud(clicks, y):
	if clicks is not None:
		x = context_search(y)
		print(x[1])
		words = list(x[1].keys())

		frequency = list(x[1].values())

		lower, upper = 15, 45
		frequency = [((x - min(frequency)) / (max(frequency) - min(frequency))) * (upper - lower) + lower for x in
					 frequency]

		percent = [0.362086258776329, 0.13139418254764293, 0.11802072885322636, 0.055834169174189235, 0.041123370110330994,
				   0.03978602474088933, 0.02774991641591441, 0.02139752591106653, 0.01905717151454363, 0.015379471748579069]

		length = len(words)
		colors = [py.colors.DEFAULT_PLOTLY_COLORS[random.randrange(1, 10)] for i in range(length)]

		data = [ go.Scatter(
			x=[5, 1, 2, 4, 3, 6, 7, 8, 9, 10],
			y=random.choices(range(length), k=length),
			mode='text',
			text=words,
			hovertext=['{0}{1}'.format(w, f) for w, f in zip(words, frequency)],
			hoverinfo='text',
			textfont={'size': frequency * 2, 'color': colors})]
	else:
		data = []


	layout = go.Layout({'xaxis': {'showgrid': False, 'showticklabels': False, 'zeroline': False},
						'yaxis': {'showgrid': False, 'showticklabels': False, 'zeroline': False},
						}, margin=go.layout.Margin(l=20, r=10, b=40, t=10, ), )

	fig = go.Figure(data=data, layout=layout, )
	return fig




@app.callback(
	[Output('wordcloud', 'style'),
	 Output('wordcloud-div', 'style'),
	 Output('text_search', 'value'),],
	[Input('button', 'n_clicks')])
def display_wordcloud_onclick(value):
	if value is not None:
		return {"display": "block"} , {'box-shadow': '0px 0px 5px 0px rgba(0,0,0,0.2)'} , ''
	else:
		return {"display": 'none'}, {"display": 'none'}, ''


import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from src.view.app import app
from src.view.apps import sentiment_analysis, earnings_analysis


server = app.server

app.layout = html.Div([

	html.Div([

	dcc.Store(id='selected_dropdown_store', storage_type='session'),
	dcc.Store(id='text_search_store', storage_type='session'),
	dcc.Store(id='wordcloud_store', storage_type='session'),

	dcc.Tabs(
		id="tabs",

		children=[

			dcc.Tab(label='Market Sentiment Analysis',value='sentiment_tab' ),
			dcc.Tab(label='Earnings Call Analysis', value='earnings_tab'),

		],
		value="sentiment_tab",
	),

	html.Div([],id="tab-content"),

	],className='right-container'),


], className="container")



@app.callback(Output('tab-content', 'children'),
			[Input('tabs', 'value')])
def display_page(tab):
	if tab == 'sentiment_tab':
		return  sentiment_analysis.layout
	elif tab == 'earnings_tab':
		return earnings_analysis.layout
	else:
		return sentiment_analysis.layout

if __name__ == '__main__':
	app.run_server(debug=False)
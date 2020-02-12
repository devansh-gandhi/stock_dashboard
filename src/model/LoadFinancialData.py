import pandas as pd
from bs4 import BeautifulSoup
import requests
from src.view.eligibilitycheck import eligibilitycheck
from src.view.futurepricing import generate_price_df
from src.model.format import format


def getfinancialreportingdf(ticker):
	# try:
	urlfinancials = 'https://www.marketwatch.com/investing/stock/' + ticker + '/financials'
	urlbalancesheet = 'https://www.marketwatch.com/investing/stock/' + ticker + '/financials/balance-sheet'

	text_soup_financials = BeautifulSoup(requests.get(urlfinancials).text, "lxml")  # read in
	text_soup_balancesheet = BeautifulSoup(requests.get(urlbalancesheet).text, "lxml")  # read in

	# Income statement
	titlesfinancials = text_soup_financials.findAll('td', {'class': 'rowTitle'})
	epslist = []
	netincomelist = []
	longtermdebtlist = []
	interestexpenselist = []
	ebitdalist = []

	for title in titlesfinancials:
		if 'EPS (Basic)' in title.text:
			epslist.append([td.text for td in title.findNextSiblings(attrs={'class': 'valueCell'}) if td.text])
		if 'Net Income' in title.text:
			netincomelist.append([td.text for td in title.findNextSiblings(attrs={'class': 'valueCell'}) if td.text])
		if 'Interest Expense' in title.text:
			interestexpenselist.append(
				[td.text for td in title.findNextSiblings(attrs={'class': 'valueCell'}) if td.text])
		if 'EBITDA' in title.text:
			ebitdalist.append([td.text for td in title.findNextSiblings(attrs={'class': 'valueCell'}) if td.text])

	# Balance sheet
	titlesbalancesheet = text_soup_balancesheet.findAll('td', {'class': 'rowTitle'})
	equitylist = []
	for title in titlesbalancesheet:
		if 'Total Shareholders\' Equity' in title.text:
			equitylist.append([td.text for td in title.findNextSiblings(attrs={'class': 'valueCell'}) if td.text])
		if 'Long-Term Debt' in title.text:
			longtermdebtlist.append([td.text for td in title.findNextSiblings(attrs={'class': 'valueCell'}) if td.text])

	# Variables
	# eps = epslist[0]
	# epsgrowth = epslist[1]
	# netincome = netincomelist[0]
	# shareholderequity = equitylist[0]
	# roa = equitylist[1]

	# longtermdebt = longtermdebtlist[0]
	# interestexpense = interestexpenselist[0]
	# ebitda = ebitdalist[0]

	eps = getelementinlist(epslist, 0)
	epsgrowth = getelementinlist(epslist, 1)
	netincome = getelementinlist(netincomelist, 0)
	shareholderequity = getelementinlist(equitylist, 0)
	roa = getelementinlist(equitylist, 1)

	longtermdebt = getelementinlist(longtermdebtlist, 0)
	interestexpense = getelementinlist(interestexpenselist, 0)
	ebitda = getelementinlist(ebitdalist, 0)
	# Don't forget to add in roe, interest coverage ratio

	# Make it into Dataframes
	df = pd.DataFrame(
		{'eps': eps, 'epsgrowth': epsgrowth, 'netincome': netincome, 'shareholderequity': shareholderequity, 'roa':
			roa, 'longtermdebt': longtermdebt, 'interestexpense': interestexpense, 'ebitda': ebitda},
		index=[2014, 2015, 2016, 2017, 2018])

	df = df.apply(format)
	for i in ['netincome', 'shareholderequity', 'longtermdebt', 'interestexpense', 'ebitda']:
		df[i] = df[i].astype('int64')

	df['interestcoverageratio'] = df.ebitda / df.interestexpense

	# Adding roe, interest coverage ratio

	df['roe'] = df.netincome / df.shareholderequity
	df['interestcoverageratio'] = df.ebitda / df.interestexpense

	return df


def getelementinlist(list, element):
	try:
		return list[element]
	except:
		return '-'


# Getting financial reporting df
def getfinancialreportingdfformatted(ticker, es):
	dfformatted = getfinancialreportingdf(ticker)
	# Format all the number in dataframe

	# future price prediction
	data_dict = es.search(index='stock_data',
						  body={"size": 2000, "query": {"match": {"stock-symbol": ticker}}})
	initial_df = pd.DataFrame.from_dict(data_dict['hits']['hits'])
	stock_data_df = pd.concat([initial_df.drop(['_source'], axis=1), initial_df['_source'].apply(pd.Series)], axis=1)

	stock_data_df['timestamp'] = pd.to_datetime(stock_data_df.timestamp, infer_datetime_format=True)
	stock_data_df['timestamp'] = stock_data_df['timestamp'].dt.date
	pricedf = generate_price_df(ticker, dfformatted, stock_data_df, 0.15, 0.15)

	price_list = pricedf.to_dict()

	reasonlist = eligibilitycheck(ticker, dfformatted)

	dfformatted['reasonlist'] = [reasonlist, None,None,None,None]
	#dfformatted['reasonlist'].iloc[0] = reasonlist



	dfformatted['future_pricing'] =[price_list, None,None,None,None]

	#dfformatted['future_pricing'].iloc[0] = 1
	#dfformatted = dfformatted.set_value(0,'future_pricing', price_list)
	#print(dfformatted['future_pricing'].iloc[0])

	#print(dfformatted.dtypes)
	#dfformatted['future_pricing'].iloc[0] = price_list
	for index, row in dfformatted.iterrows():
		es.index(index='financial_data', ignore=400, body={
			'stock-symbol': ticker,
			'year': index,
			'eps': row['eps'],
			'epsgrowth': row['epsgrowth'],
			'netincome': row['netincome'],
			'shareholderequity': row['shareholderequity'],
			'roa': row['roa'],
			'longtermdebt': row['longtermdebt'],
			'interestexpense': row['interestexpense'],
			'ebitda': row['ebitda'],
			'roe': row['roe'],
			'interestcoverageratio': row['interestcoverageratio'],
			'reasonlist': row['reasonlist'],
			'future_pricing': row['future_pricing']
		})



if __name__ == '__main__':
	getfinancialreportingdfformatted(stock_ticker, es)

import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
from elasticsearch import Elasticsearch

es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])

def loadanalystrating(ticker):
	urlratings = 'https://www.marketwatch.com/investing/stock/'+ticker+'/analystestimates'

	text_soup_ratings = BeautifulSoup(requests.get(urlratings).text, "lxml")

	titlesratings = text_soup_ratings.find('table', {'class': 'ratings'})
	titlesratings = titlesratings.findAll('td', {'class': 'first'})

	buylist = []
	overweightlist = []
	holdlist = []
	underweightlist = []
	selllist = []
	meanlist = []

	for title in titlesratings:
		if 'BUY' in title.text:
			buylist.append([td.text for td in title.findNextSiblings() if td.text])
		if 'OVERWEIGHT' in title.text:
			overweightlist.append([td.text for td in title.findNextSiblings() if td.text])
		if 'HOLD' in title.text:
			holdlist.append([td.text for td in title.findNextSiblings() if td.text])
		if 'UNDERWEIGHT' in title.text:
			underweightlist.append([td.text for td in title.findNextSiblings() if td.text])
		if 'SELL' in title.text:
			selllist.append([td.text for td in title.findNextSiblings() if td.text])
		if 'MEAN' in title.text:
			meanlist.append([td.text for td in title.findNextSiblings() if td.text])

	buy = getelementinlist(buylist, 0)
	overweight = getelementinlist(overweightlist, 0)
	hold = getelementinlist(holdlist, 0)
	underweight = getelementinlist(underweightlist, 0)
	sell = getelementinlist(selllist, 0)
	mean = getelementinlist(meanlist, 0)

	for i in range(len(buy)):
		buy[i] = int(buy[i]) + int(overweight[i])
		sell[i] = int(sell[i]) + int(underweight[i])


	df = pd.DataFrame(
		{'buy': buy, 'hold': hold,  'sell': sell, },
		index=['current', 'one_month', 'three_month'])


	for index, row in df.iterrows():
	# print(index,row)
		es.index(index='analyst_data', ignore=400, body={
			'stock-symbol': ticker,
			'duration': index,
			'buy': row['buy'],
			'hold': row['hold'],
			'sell': row['sell'],
		})


def getelementinlist(list,element):
	try:
		return list[element]
	except:
		return '-'



if __name__ == '__main__':

	loadanalystrating(stock_ticker)


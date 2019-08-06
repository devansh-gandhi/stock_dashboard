import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
from elasticsearch import Elasticsearch



def loadanalystrating(ticker,es):
	urlratings = 'https://www.marketwatch.com/investing/stock/'+ticker+'/analystestimates'

	text_soup_ratings = BeautifulSoup(requests.get(urlratings).text, "lxml")

	titlesratings = text_soup_ratings.find('table', {'class': 'estimates'})
	titlesratings = titlesratings.findAll('td', {'class': 'first'})

	enolist = []
	emeanlist = []
	ehighlist = []
	elowlist = []
	evariancelist = []


	for title in titlesratings:
		if '# of Estimates' in title.text:
			enolist.append([td.text for td in title.findNextSiblings() if td.text])
		if 'Mean Estimate' in title.text:
			emeanlist.append([td.text for td in title.findNextSiblings() if td.text])
		if 'High Estimates' in title.text:
			ehighlist.append([td.text for td in title.findNextSiblings() if td.text])
		if 'Low Estimates' in title.text:
			elowlist.append([td.text for td in title.findNextSiblings() if td.text])
		if 'Coefficient Variance' in title.text:
			evariancelist.append([td.text for td in title.findNextSiblings() if td.text])


	eno = getelementinlist(enolist, 0)
	emean = getelementinlist(emeanlist, 0)
	ehigh = getelementinlist(ehighlist, 0)
	elow = getelementinlist(elowlist, 0)
	evariance = getelementinlist(evariancelist, 0)




	df = pd.DataFrame(
		{'number': eno, 'mean': emean,  'high': ehigh, 'low': elow, 'variance': evariance },
		index=['this_quarter', 'next_quarter', 'this_fiscal','next_fiscal'])


	for index, row in df.iterrows():
		es.index(index='future_estimate_data', ignore=400, body={
			'stock-symbol': ticker,
			'duration': index,
			'number': row['number'],
			'mean': row['mean'],
			'high': row['high'],
			'low': row['low'],
			'variance': row['variance'],

		})


def getelementinlist(list,element):
	try:
		return list[element]
	except:
		return '-'



if __name__ == '__main__':

	loadanalystrating(stock_ticker,es)


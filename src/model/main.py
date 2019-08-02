from Load import Load
from elasticsearch import Elasticsearch
import os
import sys

if __name__ == '__main__':

	keyword = sys.argv[1]

	stock_dict = {"apple": "AAPL", "google": "GOOG", "microsoft": "MSFT", "amazon": "AMZN", "facebook": "FB",
                   "walmart": "WMT", "intel": "INTC", "barclays": "BCS"}
	stock_ticker = stock_dict[keyword.lower().strip()]

	#data = Load(keyword)
	#data.load_stock_data()
	#data.load_news_data()



	exec(open('LoadAnalystRating.py').read())
	exec(open('LoadFinancialData.py').read())
	exec(open('TwitterStream.py').read())
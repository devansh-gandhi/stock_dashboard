from Load import Load
from elasticsearch import Elasticsearch
import os
import os, base64, re, logging
import sys

import sys
sys.path

if __name__ == '__main__':
	# Log transport details (optional):
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

	#keyword = sys.argv[1]
	keyword = 'Google'

	stock_dict = {"apple": "AAPL", "google": "GOOG", "microsoft": "MSFT", "amazon": "AMZN", "facebook": "FB",
                   "walmart": "WMT", "intel": "INTC", "barclays": "BCS"}
	stock_ticker = stock_dict[keyword.lower().strip()]

	print(stock_ticker)

	data = Load(keyword,es)
	data.load_stock_data()
	data.load_news_data()



	exec(open('LoadAnalystRating.py').read())
	exec(open('LoadFinancialData.py').read())
	exec(open('LoadFutureEstimates.py').read())
	exec(open('TwitterStream.py').read())

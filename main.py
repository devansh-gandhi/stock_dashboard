from Load import Load
from elasticsearch import Elasticsearch
import TwitterStream
import os

if __name__ == '__main__':
    data = Load('Google')
    data.load_stock_data()
    data.load_news_data()
    #es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])
    #result = es.search(index='stock_data', body={"query": {"match": {"company_name": "Microsoft"}}})
    #print(result)

    #TwitterStream.keyword = 'Apple'

    #print(TwitterStream.keyword)


    os.system('python TwitterStream.py Google' )
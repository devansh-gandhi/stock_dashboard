from Transform import Transform
import requests, json, os
from elasticsearch import Elasticsearch



class Load:
    es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])

    def __init__(self, company_name):
        self.company_name = company_name
        self.transform = Transform(self.company_name)
        self.res = requests.get('http://localhost:9200')

    def load_stock_data(self):
        stock_data = self.transform.get_stock_data()

        for value in stock_data['Time Series (Daily)']:
            self.es.index(index='stock_data', ignore=400, doc_type='external', body={
                'company_name': self.company_name,
                'stock-symbol': stock_data['Meta Data']['2. Symbol'],
                'timestamp': value,
                'open': stock_data['Time Series (Daily)'][value]['1. open'],
                'high': stock_data['Time Series (Daily)'][value]['2. high'],
                'close': stock_data['Time Series (Daily)'][value]['3. low'],
                'low': stock_data['Time Series (Daily)'][value]['4. close'],
                'volume': stock_data['Time Series (Daily)'][value]['5. volume']
            })


    def load_news_data(self):
        news_data = self.transform.get_news_data()
        for article in news_data['articles']:
            self.es.index(index='news_data', ignore=400, doc_type='external', body={
                'timestamp': article['publishedAt'],
                'title': article['title'],
                'description': article['description'],
                'url': article['url'],
                'sentiment': article['sentiment'],
                'company_name': self.company_name
            })



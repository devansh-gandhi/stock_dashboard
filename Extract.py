import requests
import json


class Extract:
    symbol_dict = {"apple": "AAPL", "google": "GOOG", "microsoft": "MSFT", "amazon": "AMZN", "facebook": "FB",
                   "walmart": "WMT", "intel": "INTC", "barclays": "BCS"}

    def __init__(self, name):
        self.name = name

    def set_symbol_dict(Extract, name, company_symbol):
        name = name.lower().strip()
        Extract.symbol_dict[name] = company_symbol

    def get_symbol_dict(self):
        return self.symbol_dict

    def get_stock_symbol(self, company_name):
        return self.symbol_dict.get(company_name)

    def get_stockprice_extract(self):
        company_name = self.name.lower()
        symbol = self.get_stock_symbol(company_name)
        response = requests.get(
            'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=' + symbol + '&outputsize=full&apikey=5EO00YFWTU7L1EED')
            #'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=' + symbol + '&interval=5min&apikey=5EO00YFWTU7L1EED')
        # Print the status code of the response.
        return (response)

    def get_news_extract(self):
        response = requests.get(
            'https://newsapi.org/v2/everything?q=' + self.name + '&sources=the-wall-street-journal,the-verge,techcrunch,cnbc,cnn,engadget,the-new-york-times,the-economist,techradar,reuters,google-news,financial-post,business-insider,bloomberg&pageSize=100&sortBy=publishedAt&apiKey=30f781a305e34b55bcb18fd76d3fbd8c'
        )
        # Print the status code of the response.
        return (response)



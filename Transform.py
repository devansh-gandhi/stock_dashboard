from textblob import TextBlob
from Extract import Extract
import json
import spacy


class Transform:

    def __init__(self, name):
        self.name = name
        self.extract = Extract(name)

    def get_sentiment(self, text):
        sentimentBlob = TextBlob(text)
        if (sentimentBlob.sentiment.polarity > 0):
            return ('Positive')
        else:
            return ('Negative')

    def get_stock_data(self):
        data = self.extract.get_stockprice_extract()
        stock_data = data.json()
        return stock_data

    def get_ner_dict(self,description):
        ner_list = []
        spacy_nlp = spacy.load('en')
        document = spacy_nlp(description)
        for element in document.ents:
            ner_list.append(str(element))
        return ner_list

    def get_news_data(self):
        data = self.extract.get_news_extract().json()
        for article in data['articles']:
            sentiment = self.get_sentiment(article['description'])
            article['sentiment'] = sentiment
            ner_tags = self.get_ner_dict(article['description'])
            article['ner_tags'] = ner_tags
        return data

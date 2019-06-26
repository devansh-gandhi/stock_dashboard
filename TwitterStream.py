import json
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from elasticsearch import Elasticsearch
import sys
#import Label
#import KTFInfo
from Transform import Transform
es = Elasticsearch()


class TweetsStreamDataListener(StreamListener):
    # on success
    def on_data(self, data):
        dict_data = json.loads(data)
        tweet_label = Transform.get_sentiment(Transform,dict_data["text"])
        if tweet_label != 'uncategorized' and ('RT @' not in dict_data['text']):
            #print(tweet_label + " : " + dict_data["text"])
            es.index(index="tweets_data",
                     doc_type="tweet",
                     body={"author": dict_data["user"]["screen_name"],
                           "date": dict_data["created_at"],
                           "label": tweet_label,
                           "message": dict_data["text"],
                           "company_name": keyword},

                     )

        return True

    # on failure
    def on_error(self, status):
        print(status)


if __name__ == '__main__':
    # create instance of the tweepy tweet stream listener
    listener = TweetsStreamDataListener()

    # set twitter keys/tokens
    # consumer_key = "RK6Gn5h3cq1llfXTz1zY7Hsjx"
    # consumer_secret = "X6cqtrIH6Pe8HFk5I9MaKmcW0SjsEksqk8b3fUfcL9L4Vye4LV"
    # access_token = "206985484-ZR2aQPnxdzBOpSeuobtH3dDLkO4NLhJRwwGLtrmQ"
    # access_token_secret = "lUerNXEmhVlXydVi03tn3LWNPcp1Iy9vaBMeLH2QmRIFZ"
    keyword = sys.argv[1]

    #print(sys.argv[1])

    consumer_key = 'sljGvj4bKLY9LPKlHpySGuMW5'
    consumer_secret = 'MGDfahGilqS0pJBxLOVk5FPAfqluLs51XCzZUWdd8TF2QuQ7WQ'
    access_token = '2894483640-G5e7wjEW8FoKCmCrq8lWG0OR2E1e07gqympzid9'
    access_token_secret = 'D8EMLNXFT3SiaXpKjeWBX5f0cxbOjBdFjqvbek5YR2QxA'

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = Stream(auth, listener)
    stream.filter(track=[keyword], languages=["en"])
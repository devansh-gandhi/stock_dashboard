# Stock Dashboard

https://stock-dashboard-app.herokuapp.com/

This is a demo application for a stock dashboard. It is for financial analyst to to make informed investment decisions about the company using Elasticsearch and dash. 

The project is divided into two parts. The model part is the backend part of it. It performs web scrapping and loads all the data into Elasticsearch.  The view part is the front end part which the user sees. 

Model 

This folder is primarily in order to scrape information from the web and load it into Elasticsearch.

Main.py – This file is the central file which call all of the other files and executes them.

Extract.py – This files extracts the stock data from Alphavantage API and the news data from NewsOrg API. It then converts them into JSON format.

Transform.py – This file performs sentiment analysis on the news and the tweets.

Load.py – This file loads the stock prices and news into Elasticsearch

TwitterStream.py – This file streams Twitter to extract relevant tweets about the particular company. It then calls the Transform module to perform sentiment analysis on the tweet. It loads all of this data into Elasticsearch.

LoadAnalystRating.py – This file scrapes analyst ratings from MarketWatch and loads them into Elasticsearch. The buy and the overweight rating are aggregated into buy for simplicity purpose. Similar aggregation is done for sell and underweight.  

LoadFinancialData.py – This file loads the following financial information into Elasticsearch:- 

•	Earnings per share
•	Eps growth
•	net income
•	shareholder equity
•	Return on Assets
•	long term debt
•	interest expense
•	ebitda
•	Return on equity

LoadFutureEstimates.py – This file loads the future eps estimates of the for the next quarter and fiscal into Elasticsearch.


VIEW:

This is the front end / User Interface part of the project.

App.py – Initializes the dash application

Index.py – This is the first page that loads the application. By default, it opens the Market Sentiment Analysis tab.  

Sentiment_analysis.py -  This tab is the landing page of the application.  The first component of the page is the search bar. The user can select the company name directly from the dropdown or enter an extract in the search bar after selecting the extract option. The extract option generates a word cloud based on the extract. In the extract option, information about the most prominent company name in the extract is shown. The user can also click company names in the word cloud to display their information. The second component is the stock price chart. It shows daily stock prices for that company for the last five years. The next component is the news table. It shows the latest news headlines related to that company. The table next to it shows the latest tweets regarding that company. The user can select a row in both the tables i.e news table and tweets table to open in depth information.    

Earnings_analysis.py – This tab is for advance analytical and technical indicators. The first graph shows the stock recommendation. This decision is based on the difference between the margin price and last share price. If the difference is less than -30 then it is a “SELL” recommendation, between -30 and 30 then a “HOLD” or more than 30 it gives a “BUY” recommendation. When the recommendation tab is clicked, it open a modal which displays various critical values and ratios.

The next graph shows the current and next eps estimates for quarter and fiscal.

The next graph shows the analyst rating for the current month, previous month and three months back.

The next graph shows information about different financial data.

The next graph shows the technical indicators such as Simple Moving Average(SMA), Exponential Moving Average (EMA)  and the Relative Strength Index(RSI).





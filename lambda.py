from Secrets import api_key_coinmaketcap
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import requests
         
result = {
  "messages": [
    {
      "contentType": 'PlainText',
      "content": ""
    }
  ],
  "sessionState": {
    "originatingRequestId": "",
    "intent": { "name": "", "state": 'Fulfilled' },
    "dialogAction": { "type": 'Close', "fulfillmentState": 'Fulfilled' }
  }
}

def get_price(symbol):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    parameters = {
    'symbol':symbol
    }
    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': api_key_coinmaketcap,
    }
    session = Session()
    session.headers.update(headers)
    response = session.get(url, params=parameters)
    data = json.loads(response.text)
    price = str(data['data'][symbol]['quote']['USD']['price'])
    return price
    
  
def get_sentiments_twitter_and_reddit(symbol):
    url = "https://finnhub.io/api/v1/stock/social-sentiment?symbol="+symbol+"&token=c9iahaaad3i9bpe2e0bg"
    r = requests.get(url)
    try:
        data1 = json.loads(r.text)
    except:
        print("Bad request")
    
    arr1 = data1['reddit']
    arr2 = data1['twitter']
    
    if len(arr1) == 0:
        reddit_positive_mean = None
        reddit_negative_mean = None
    else:
        reddit_positive_scores = [i['positiveScore'] for i in arr1]
        reddit_negative_scores = [i['negativeScore'] for i in arr1]
        reddit_positive_mean = sum(reddit_positive_scores)/len(reddit_positive_scores)
        reddit_negative_mean = sum(reddit_negative_scores)/len(reddit_negative_scores)

    if len(arr2) == 0:
        twitter_positive_mean = None
        twitter_negative_mean = None
    else:
        twitter_positive_scores = [i['positiveScore'] for i in arr2]
        twitter_negative_scores = [i['negativeScore'] for i in arr2]
        twitter_positive_mean = sum(twitter_positive_scores)/len(twitter_positive_scores)
        twitter_negative_mean = sum(twitter_negative_scores)/len(twitter_negative_scores)
        
    return (reddit_positive_mean , reddit_negative_mean , twitter_positive_mean , twitter_negative_mean)

def get_sentiment(symbol):
    reddit_pos , reddit_neg , twitter_pos , twitter_neg = get_sentiments_twitter_and_reddit(symbol)
    sentiment_string = ""
    if reddit_pos == None and twitter_pos == None:
        sentiment_string = "Sentiments for "+symbol+" not found"
    elif reddit_pos == None:
        sentiment_string = "Sentiments for "+symbol+" on reddit are missing , Positive sentiment from Twitter: "+str(twitter_pos)[:6]+" Negative sentiment from Twitter: "+str(twitter_neg)[:6]
    elif twitter_pos == None:
        sentiment_string = "Positive sentiment for "+symbol+" from Reddit: "+str(reddit_pos)[:6]+" Negative sentiment from Reddit: "+str(reddit_neg)[:6]+" But sentiments for twitter are missing"
    else:
        sentiment_string = "Positive sentiment for "+symbol+" from Reddit: "+str(reddit_pos)[:6]+" Negative sentiment from Reddit: "+str(reddit_neg)[:6]+" and Positive sentiment from Twitter: "+ str(twitter_pos)[:6]+" Negative sentiment from Twitter: "+str(twitter_neg)[:6]
    
    return sentiment_string

def get_all_news_for(symbol):
    url = "https://finnhub.io/api/v1/company-news?symbol="+symbol+"&from=2022-03-22&to=2022-04-22&token=c9iahaaad3i9bpe2e0bg"
    r = requests.get(url)
    try:
        data1 = json.loads(r.text)
    except:
        print("Bad request")
    
    headlines_arr = [i['headline'] for i in data1]
    if len(headlines_arr) == 0:
        return None

    if len(headlines_arr)>5:
        headlines_arr = headlines_arr[:5]

    news_string = ""
    for i in range(len(headlines_arr)):
        news_string += str(i+1)
        news_string += headlines_arr[i] + " "

    return news_string

def get_news_string(symbol):
    news_string = get_all_news_for(symbol)
    if news_string == None:
        return "News for this company was not found"
    else:
        return news_string

def all_finances_for(symbol):
    url = "https://finnhub.io/api/v1/stock/metric?symbol="+symbol+"&metric=all&token=c9iahaaad3i9bpe2e0bg"
    r = requests.get(url)
    data1 = json.loads(r.text)
    arr = ['52WeekHigh','52WeekLow','roiAnnual','freeCashFlowAnnual']

    d = dict()
    for i in data1['metric']:
        if i in arr:
            d[i] = data1['metric'][i]
    if len(d.keys()) == 0:
        return None

    finance_string = "The basic financials for the"+symbol+"are : "
    for i in d:
        finance_string += i.lower()+" -> "
        finance_string += str(d[i])+ ", "

    finance_string = finance_string[:-2]
    finance_string = finance_string+ "."
    return finance_string

def get_finances_string(symbol):
    finance_string = all_finances_for(symbol)
    if finance_string == None:
        return "Sorry, Financials for this company were not found in our database"
    else:
        return finance_string

def lambda_handler(event,context):
    
    interpretations = event["interpretations"][0]["intent"]["slots"]
    intent_name = event["interpretations"][0]["intent"]["name"]
    session_id = event["sessionState"]["originatingRequestId"]
    result["sessionState"]["originatingRequestId"] = session_id
    result["sessionState"]["intent"]["name"] = intent_name
    
    print(list(interpretations.keys())[0]) # DONT REMOVE

    Ticker_name =  list(interpretations.keys())[0]   


    if Ticker_name == "CoinTicker":
        symbol = interpretations["CoinTicker"]["value"]["interpretedValue"]
        price = get_price(symbol)    
        try:
            result["messages"][0]["content"] = "The price for " +symbol + ": " + price
        except:
            result["messages"][0]["content"] = "runtime error fetching the prices"
        
        return result
        
    elif Ticker_name == "SentimentTicker":
        symbol = interpretations["SentimentTicker"]["value"]["interpretedValue"]
        sentiment_string = get_sentiment(symbol)
        try:
            result["messages"][0]["content"] = sentiment_string
        except:
            result["messages"][0]["content"] = "runtime error fetching the Sentiments"
        
        return result
    
    elif Ticker_name  == "ChartTicker":
        symbol = interpretations["ChartTicker"]["value"]["interpretedValue"]
        url = "https://www.tradingview.com/chart/?symbol="+symbol
        try:
            result["messages"][0]["content"] = url
        except:
            result["messages"][0]["content"] = "runtime error fetching the chart ticker"
        
        return result
    
    elif Ticker_name == "NewsTicker":
        symbol = interpretations["NewsTicker"]["value"]["interpretedValue"]
        news_strings = get_news_string()
        try:
            result["messages"][0]["content"] = news_strings
        except:
            result["messages"][0]["content"] = "runtime error fetching the chart ticker"
        
        return result
    
    elif Ticker_name == "FinanceTicker":
        symbol = interpretations["FinanceTicker"]["value"]["interpretedValue"]
        finance_string = get_finances_string()
        try:
            result["messages"][0]["content"] = finance_string
        except:
            result["messages"][0]["content"] = "runtime error fetching the chart ticker"
        
        return result

    else:
        result["messages"][0]["content"] = "We don't have this functionality yet"
        return result


    # Add try except block towards the end
        
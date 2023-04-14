import numpy as np
import tweepy
import pandas as pd
from datetime import datetime, timedelta
import pycountry 
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from src.paths import PARENT_DIR
from dotenv import load_dotenv
import os 

load_dotenv(PARENT_DIR / '.env')

TWITTER_CONSUMER_KEY=os.environ['TWITTER_CONSUMER_KEY']
TWITTER_CONSUMER_SECRET=os.environ['TWITTER_CONSUMER_SECRET']
TWITTER_ACCESS_TOKEN=os.environ['TWITTER_ACCESS_TOKEN']
TWITTER_ACCESS_TOKEN_SECRET=os.environ['TWITTER_ACCESS_TOKEN_SECRET']
query_default = 'chatgpt'
roberta = "cardiffnlp/twitter-roberta-base-sentiment"

# Authenticate with the Twitter API
auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# load ML model and tokenizer
model = AutoModelForSequenceClassification.from_pretrained(roberta)
tokenizer = AutoTokenizer.from_pretrained(roberta)
labels = [-1, 0, 1]

def get_tweets_about(n_hours,
                     query = query_default,
                     max_tweets = 100):
    # Get the current time in UTC
    now = datetime.now()

    # Calculate the time window
    since_time = now - timedelta(hours=n_hours)


    # Search for tweets containing the search query within the time window
    tweets = tweepy.Cursor(api.search_tweets,
                        q=query,
                        tweet_mode='extended',
                        lang='en',
                        since_id=since_time.strftime('%Y-%m-%dT%H:%M:%SZ')).items(max_tweets)
    
    # Extract the relevant data from the tweets and store it in a list
    tweet_data = []
    for tweet in tweets:
        tweet_data.append({
            'created_at': tweet.created_at,
            'text': tweet.full_text,
            'user_location':tweet.user.location
        })

    # Convert the list of tweet data to a pandas dataframe
    tweet_df = pd.DataFrame(tweet_data)
    validated_tweet_df = validate_tweet_data(tweet_df)
    validated_tweet_df['sentiment'] = validated_tweet_df['text'].apply(lambda x: predict_sentiment(x))
    tweet_df_final = group_data_by_country(validated_tweet_df)
    return tweet_df_final

def validate_tweet_data(tweet_df):
    tweet_df['country_code'] = tweet_df['user_location'].apply(lambda x: process_location(x))
    tweet_df = tweet_df.dropna(subset=['country_code'])
    tweet_df = tweet_df.reset_index(drop=True)
    return tweet_df


def process_location(location_string):
    try:
        country_code = pycountry.countries.search_fuzzy(location_string)[0].alpha_3
        return country_code
    except:
        return None

def predict_sentiment(tweet):
    encoded_tweet = tokenizer(tweet, return_tensors='pt')
    output = model(**encoded_tweet)

    sentiment = labels[np.argmax(output[0][0].detach().numpy())]
    return sentiment

def group_data_by_country(tweet_df):
    grouped_df = tweet_df.groupby('country_code')['sentiment'].sum().to_frame()
    grouped_df = grouped_df.rename(columns={'sentiment': 'total_sentiment'})

    # get the maximum absolute value of 'total_sentiment'
    max_abs = np.max(np.abs(grouped_df['total_sentiment']))
    # normalize the 'total_sentiment' column between -1 and 1
    grouped_df['values_norm'] = grouped_df['total_sentiment'] / max_abs
    # replace NaN values (if any) with 0
    grouped_df['values_norm'].fillna(0, inplace=True)

    grouped_df = grouped_df.reset_index(drop=False)

    # add two new rows to the dataframe
    new_rows = [
        {'country_code': 'foo', 'total_sentiment': 0, 'values_norm': 1},
        {'country_code': 'bar', 'total_sentiment': 0, 'values_norm': -1}
    ]
    grouped_df = pd.concat([grouped_df, pd.DataFrame(new_rows)] )
    return grouped_df
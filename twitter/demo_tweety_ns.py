import json
from tweety import Twitter
from tweety.filters import SearchFilters
import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from tweety.exceptions_ import RateLimitReached, DeniedLogin,InvalidCredentials, UnknownError
import time


# def get_free_credential():
#     # Fetch one free credential from the database, prioritizing those with human_action = 'No'
#     return TwitterCred.objects.filter(current_status='free').order_by('human_action').first()



def search_tweets(keyword, filter_, pages, wait_time):
    try:
        if filter_ == None:
            tweets =  app.search(keyword,pages=pages, wait_time=wait_time)
        else:
            tweets =  app.search(keyword, filter_=filter_, pages=pages, wait_time=wait_time)
        return tweets
    except RateLimitReached:
        print("Rate limit reached. Please wait for a while before making more requests.")
    except DeniedLogin:
        print("Login denied. Please check your username and password.")
    except UnknownError as e:
        print(f"An unknown error occurred: {e}")
    return []



def extract_tweet_data(tweets):
    tweet_data = []
    for tweet in tweets:
        data = {
            'tweetid': tweet.id,
            'userid': tweet.author.id,
            'username': tweet.author.username,
            'created_on': str(tweet.created_on),
            'text': tweet.text,
            'is_retweet': tweet.is_retweet,
            'views': tweet.views,
            'likes': tweet.likes,
            'tweet_url': tweet.url
        }
        tweet_data.append(data)
    return tweet_data


def remove_duplicates(tweet_data):
    seen = set()
    unique_data = []
    for data in tweet_data:
        if data['tweetid'] not in seen:
            seen.add(data['tweetid'])
            unique_data.append(data)
    return unique_data


def analyze_tweets(tweet_data, product_description):
    # Initialize the VADER sentiment intensity analyzer
    sia = SentimentIntensityAnalyzer()

    # Tokenize the product description
    product_words = word_tokenize(product_description)

    for data in tweet_data:
        sentiment_scores = sia.polarity_scores(data['text'])
    
        # Categorize the tweet based on its compound sentiment score
        if sentiment_scores['compound'] > 0.05:
            category = 'highly relevant'
        elif sentiment_scores['compound'] < -0.05:
            category = 'less relevant'
        else:
            category = 'neutral'
    
        # Check if any of the words in the product description appear in the tweet
        tweet_words = word_tokenize(data['text'])
        if any(word in tweet_words for word in product_words):
            relevance = 'relevant'
        else:
            relevance = 'not relevant'
    
        # Add the 'relevance' and 'category' to the tweet data
        data['relevance'] = relevance
        data['category'] = category

    # Remove the tweets that are not relevant
    tweet_data = [data for data in tweet_data if data['relevance'] != 'not relevant']

    return tweet_data

app = Twitter("session3")
app.sign_in('SuhaibSirr', 'Gpk@12345')
print(app.user)


# credential = TwitterCred.objects.filter(current_status='free').order_by('human_action').first()


keywords = ['text to video']
pages = 2
wait_time = 1
# Provide a description of your product
product_description = """A free text to video tool Creating video from text
is an AI model that can create realistic and imaginative scenes from text instructions.
"""


def twitter_instance_get_app():
    # Timer
    start_time = time.time()

    while True:
        # Fetch one free credential from the database
        # credential = TwitterCred.objects.filter(current_status='free').order_by('human_action').first()
        credential = [
                {'username': 'tob_12345', 'password': 'Gpk@12345', 'session_details': 'session2', 'current_status': 'occupied','human_action':'No'},
                
                {'username': 'SuhaibSirr', 'password': 'Gpk@12345', 'session_details': 'session3', 'current_status': 'free','human_action':'No'},

                {'username': 'britt_simar', 'password': 'Gpk@12345', 'session_details': 'session4', 'current_status': 'free','human_action':'No'},
            ]

        if not credential:
            if time.time() - start_time > 45 * 60:  # 45 minutes
                raise Exception("Problem with Twitter login: no free credentials available after 45 minutes.")
            else:
                print("No free credentials available. Waiting for 5 minutes before checking again...")
                time.sleep(5 * 60)  # 5 minutes
                continue
        else:
            try:
                app = Twitter(credential.session_details)
                app.sign_in(credential.username, credential.password)
                print(app.user)

                # Mark the credential as occupied
                credential.current_status = 'occupied'
                credential.save()

                return app

            except (InvalidCredentials, DeniedLogin, UnknownError):
                credential.human_action = 'Yes'
                credential.save()
                print(f"An error occurred with the credentials for {credential.username}. Marking 'human_action' as 'Yes'.")
                continue  # Continue with the next iteration of the while loop


for keyword in keywords:
    print(f"Searching for the latest tweets with keyword '{keyword}'...")
    latest_tweets = search_tweets(keyword, SearchFilters.Latest(), pages, wait_time)
    latest_tweet_data = extract_tweet_data(latest_tweets)
    print("Number of latest_tweet_data:", len(latest_tweet_data))

    time.sleep(wait_time)

    print(f"Searching for the top tweets with keyword '{keyword}'...")
    top_tweets = search_tweets(keyword, None, pages, wait_time)
    top_tweet_data = extract_tweet_data(top_tweets)
    print("Number of top_tweet_data:", len(top_tweet_data))

    # Combine the latest and top tweets
    all_tweet_data = latest_tweet_data + top_tweet_data
    print("Number of all_tweet_data:", len(all_tweet_data))

    # Remove duplicates
    all_unique_tweet_data = remove_duplicates(all_tweet_data)

    print("Number of all_unique_tweet_data:", len(all_unique_tweet_data))

    all_post_sent_unique_tweet_data = analyze_tweets(all_unique_tweet_data, product_description)

    print("Number of all_post_sent_unique_tweet_data:", len(all_post_sent_unique_tweet_data))

    # Convert lists of dictionaries into pandas DataFrames
    # df_combined = pd.DataFrame(all_unique_tweet_data)
    # df_combined = pd.DataFrame(all_post_sent_unique_tweet_data)


    # # Save DataFrames as CSV files
    # df_combined.to_csv('all_unique_tweet_data.csv', index=False)
    # df_combined.to_csv('all_post_sent_unique_tweet_data.csv', index=False)
    
    # Convert to JSON
    # all_tweet_data_json = json.dumps(all_unique_tweet_data)

    print("last",all_post_sent_unique_tweet_data)

    print("Number of all_post_sent_unique_tweet_data:", len(all_post_sent_unique_tweet_data))



    

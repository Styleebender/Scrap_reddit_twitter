import time
from tweety import Twitter
from tweety.filters import SearchFilters
from tweety.exceptions_ import RateLimitReached, DeniedLogin, InvalidCredentials, UnknownError
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from .models import TwitterCred

MAX_LOGIN_RETRIES = 3  # Maximum number of login retry attempts
MAX_CHECKS = 9  # Maximum number of checks for free credentials
CHECK_INTERVAL_SECONDS = 300  # Interval between each check for free credentials (300 seconds = 5 minutes)

def get_free_credential():
    return TwitterCred.objects.filter(current_status='free').order_by('-human_action').first()
    # return TwitterCred.objects.filter(current_status='free').order_by('human_action').first()

MAX_LOGIN_RETRIES = 3  # Maximum number of login retry attempts

def login_with_credential(credential):
    retries = 0
    while retries < MAX_LOGIN_RETRIES:
        try:
            app = Twitter(credential.session_details)
            app.sign_in(credential.username, credential.password)
            return app
        except (InvalidCredentials, DeniedLogin, UnknownError):
            retries += 1
            credential.human_action = 'Yes'
            credential.save()
            print(f"Error occurred with credentials for {credential.username}. Retrying... ({retries}/{MAX_LOGIN_RETRIES})")
            credential = wait_and_check_for_free_credentials(9)  # Get a new credential
    print(f"Failed to login with credentials for {credential.username} after {MAX_LOGIN_RETRIES} attempts.")
    return None


def search_tweets(app, keyword, filter_, pages, wait_time):
    tweets = None
    try:
        if filter_ is None:
            tweets = app.search(keyword, pages=pages, wait_time=wait_time)
        else:
            tweets = app.search(keyword, filter_=filter_, pages=pages, wait_time=wait_time)
        return 'success', tweets
    except RateLimitReached:
        print("Rate limit reached. Please wait for a while before making more requests.")
        return 'RateLimit', tweets
    except UnknownError as e:
        print(f"An unknown error occurred: {e}")
        return 'fail', tweets
    return []

def extract_tweet_data(tweets):
    tweet_data = []
    try:
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
        return 'success', tweet_data
    except Exception as e:
        print("extract_tweet_data failed.", str(e))
        return 'fail', tweet_data

def remove_duplicates(tweet_data):
    seen = set()
    unique_data = []
    try:
        for data in tweet_data:
            if data['tweetid'] not in seen:
                seen.add(data['tweetid'])
                unique_data.append(data)
        return 'success', unique_data
    except Exception as e:
        print("remove_duplicates failed.", str(e))
        return 'fail', unique_data
    
    
def analyze_tweets(tweet_data, product_description):
    tweet_data = None
    try:
        sia = SentimentIntensityAnalyzer()
        product_words = word_tokenize(product_description)

        for data in tweet_data:
            sentiment_scores = sia.polarity_scores(data['text'])
            if sentiment_scores['compound'] > 0.05:
                category = 'highly relevant'
            elif sentiment_scores['compound'] < -0.05:
                category = 'less relevant'
            else:
                category = 'neutral'
            
            tweet_words = word_tokenize(data['text'])
            if any(word in tweet_words for word in product_words):
                relevance = 'relevant'
            else:
                relevance = 'not relevant'
            
            data['relevance'] = relevance
            data['category'] = category

        tweet_data = [data for data in tweet_data if data['relevance'] != 'not relevant']

        return 'success', tweet_data
    except Exception as e:
        print("analyze_tweets failed.", str(e))
        return 'fail', tweet_data

def wait_and_check_for_free_credentials():
    for _ in range(MAX_CHECKS):
        print("Checking for free credentials...")
        credential = get_free_credential()
        if credential:
            credential.current_status = 'occupied'
            credential.save()
            return credential  # Return credential if found
        
        time.sleep(CHECK_INTERVAL_SECONDS)  # Wait for CHECK_INTERVAL_SECONDS before checking again

    raise Exception(f"No free credentials available after {MAX_CHECKS * CHECK_INTERVAL_SECONDS/60} minutes.")

# Configuration
keywords = ['text to video']
pages = 2
wait_time = 1
product_description = """A free text to video tool Creating video from text
is an AI model that can create realistic and imaginative scenes from text instructions.
"""


# ------------------------------------------------------------------------------------------------------------------
#  1. Need to pass app instace to every method right now it is global worng
#  2. Need to improve if suppose in mili sec before making it occupied what is some other process made it occupied.
#  3. Need to mark credentials free also in exception important
#  4. refer reddit cript
# ------------------------------------------------------------------------------------------------------------------


try:
    credential = wait_and_check_for_free_credentials()
    app = login_with_credential(credential)
    if app is None:
        exit()

    for keyword in keywords:
        keyword = f"\"{keyword}\""
        print(f"Searching for latest")
        msg, latest_tweets = search_tweets(app, keyword, SearchFilters.Latest(), pages, wait_time)
        if msg == 'RateLimit':
            print("Rate limit reached. Waiting for 15 minutes before retrying...")
            time.sleep(900)  # Wait for 15 minutes (900 seconds)
            print("Retrying search after waiting...")
            msg, latest_tweets = search_tweets(app, keyword, SearchFilters.Latest(), pages, wait_time)
            if msg is not 'success':
                credential.current_status = 'free'
                credential.human_action = 'Yes'
                credential.save()
                # write in porject that no data failed...
                exit()
        elif msg == 'fail' or msg == 'UnknownError':
            print("Unknown error or failure occurred. Trying again with new credentials...")
            credential.current_status = 'free'
            credential.human_action = 'Yes'
            credential.save()
            credential = wait_and_check_for_free_credentials()
            app = login_with_credential(credential)
            if app is None:
                # write in porject that no data failed...
                exit()
            msg, latest_tweets = search_tweets(app, keyword, SearchFilters.Latest(), pages, wait_time)
            if msg is not 'success':
                credential.current_status = 'free'
                credential.human_action = 'Yes'
                credential.save()
                # write in porject that no data failed...
                exit()

        msg, latest_tweet_data = extract_tweet_data(latest_tweets)
        time.sleep(wait_time)

        print(f"Searching for top")
        msg, top_tweets = search_tweets(app, keyword, pages, wait_time)
        if msg == 'RateLimit':
            print("Rate limit reached. Waiting for 15 minutes before retrying...")
            time.sleep(900)  # Wait for 15 minutes (900 seconds)
            print("Retrying search after waiting...")
            msg, top_tweets = search_tweets(app, keyword, pages, wait_time)
            if msg is not 'success':
                credential.current_status = 'free'
                credential.human_action = 'Yes'
                credential.save()
                # write in porject that no data failed...
                exit()
        elif msg == 'fail' or msg == 'UnknownError':
            print("Unknown error or failure occurred. Trying again with new credentials...")
            credential.current_status = 'free'
            credential.human_action = 'Yes'
            credential.save()
            credential = wait_and_check_for_free_credentials()
            app = login_with_credential(credential)
            if app is None:
                # write in porject that no data failed...
                exit()
            msg, top_tweets = search_tweets(app, keyword, pages, wait_time)
            if msg is not 'success':
                credential.current_status = 'free'
                credential.human_action = 'Yes'
                credential.save()
                # write in porject that no data failed...
                exit()

        msg, top_tweet_data = extract_tweet_data(top_tweets)
        all_tweet_data = latest_tweet_data + top_tweet_data
        msg, all_unique_tweet_data = remove_duplicates(all_tweet_data)

        msg, all_post_sent_unique_tweet_data = analyze_tweets(all_unique_tweet_data, product_description)

        print("Number of all_post_sent_unique_tweet_data:", len(all_post_sent_unique_tweet_data))

        # Need to make Credentials Free
except Exception as e:
    print(e)



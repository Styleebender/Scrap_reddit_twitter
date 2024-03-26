import time
import praw
import json
import pandas as pd
from prawcore.exceptions import Forbidden
from praw.exceptions import RedditAPIException, PRAWException
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from django.db import transaction
from .models import RedditCred

MAX_LOGIN_RETRIES = 3  # Maximum number of login retry attempts
MAX_CHECKS = 9  # Maximum number of checks for free credentials
CHECK_INTERVAL_SECONDS = 300  # Interval between each check for free credentials (300 seconds = 5 minutes)

# # Reddit API Creds
# client_id = 'FgxSw-LaHPfhP6K70rqgbg'
# secret = "EgoFaB4MKZv-QAzgHbcScMLFdqGYaw"

# # Reddit User Creds
# user_name = "Ok-Radish-764"
# pass_word = "Gpk@12345"


# reddit = praw.Reddit(
#     client_id= client_id,
#     client_secret= secret,
#     password=pass_word,
#     user_agent="my_research_application_v1.0 by u/"+user_name,
#     username=user_name,
#     ratelimit_seconds=370
# )

# print("verify",reddit.user.me())

# exact=False
# related_subreddits = reddit.subreddits.search_by_name(keyword, exact=False)


def get_free_reddit_credentials():
    return RedditCred.objects.filter(current_status='free').order_by('-human_action').first()

# ------------------------------------------------------------------------------------------------------------------
#  Need to improve if suppose in mili sec before making it occupied what is some other process made it occupied.
# ------------------------------------------------------------------------------------------------------------------
def wait_and_check_for_free_credentials():
    for _ in range(MAX_CHECKS):
        print("Checking for free credentials...")
        credential = get_free_reddit_credentials()
        if credential:
            with transaction.atomic():
                credential.current_status = 'occupied'
                credential.save()
            return credential  # Return credential if found
        
        time.sleep(CHECK_INTERVAL_SECONDS)  # Wait for CHECK_INTERVAL_SECONDS before checking again
 
    raise Exception(f"No free credentials available after {MAX_CHECKS * CHECK_INTERVAL_SECONDS/60} minutes.")


def login_with_credential(credential):
    retries = 0
    while retries < MAX_LOGIN_RETRIES:
        try:
            reddit = praw.Reddit(
                client_id=credential.client_id,
                client_secret=credential.secret,
                password=credential.password,
                user_agent=f"my_research_application_v1.0 by u/{credential.username}",
                username=credential.username,
            )
            return reddit
        except Forbidden:
            retries += 1
            credential.human_action = 'Yes'
            credential.current_status = 'free'
            credential.save()
            print(f"Error occurred with credentials for {credential.username}. Retrying... ({retries}/{MAX_LOGIN_RETRIES})")
            credential = wait_and_check_for_free_credentials()  # Get a new credential
    print(f"Failed to login with credentials for {credential.username} after {MAX_LOGIN_RETRIES} attempts.")
    return None


def get_related_subreddits(keyword, reddit, min_subscribers=1000):
    related_subreddits = set()
    try:
        for subreddit in reddit.subreddits.search(keyword):
            if subreddit.subscribers is not None and subreddit.subscribers > min_subscribers:
                related_subreddits.add(subreddit.display_name)
        return 'success', related_subreddits
    except RedditAPIException as e:
        print("Rate limit reached. Please wait for a while before making more requests.", str(e))
        return 'RateLimit', related_subreddits
    except Exception as e:
        print("Rate limit reached. Please wait for a while before making more requests.", str(e))
        return 'fail', related_subreddits

def search_posts_with_keyword(keyword, subreddits,reddit,time_filter="year"):
    submissions_data = []  # List to store submission data as dictionaries
    index = 0
    sort_types = ['relevance', 'new', 'hot', 'top']
    try:
        for subreddit_name in subreddits:
            print("cuurent subreddit name: ", subreddit_name)
            try:
                subreddit = reddit.subreddit(subreddit_name)
                for sort_type in sort_types:
                    for submission in subreddit.search(keyword, time_filter=time_filter, sort=sort_type, limit=None):
                        print("url",submission.url)
                        index = index + 1
                        print("index", index)
                        submission_data = {
                            "title": submission.title,
                            "author": str(submission.author),
                            "url": submission.url,
                            "score": submission.score,
                            "num_comments": submission.num_comments,
                            "created_utc": submission.created_utc,
                            "id": submission.id,
                            "selftext": submission.selftext,
                            "permalink": submission.permalink,
                            "subreddit": submission.subreddit.display_name,
                            "subreddit_name_prefixed": submission.subreddit_name_prefixed,
                            "is_video": submission.is_video,
                            # Add more attributes as needed
                        }
                        submissions_data.append(submission_data)
                    time.sleep(15)
            except Forbidden:
                print(f"Skipping private subreddit: {subreddit_name}")
        return 'success', submissions_data
    
    except RedditAPIException as e:
        print("Rate limit reached. Please wait for a while before making more requests.", str(e))
        return 'RateLimit', submissions_data
    except Exception as e:
        print("Rate limit reached. Please wait for a while before making more requests.", str(e))
        return 'fail', submissions_data


def analyze_posts(post_data, product_description):
    post_data = None
    try:
        sia = SentimentIntensityAnalyzer()
        product_words = word_tokenize(product_description)

        for data in post_data:
            # Combine the title and selftext
            text = data['title'] + ' ' + data['selftext']
            sentiment_scores = sia.polarity_scores(text)
            if sentiment_scores['compound'] > 0.05:
                category = 'highly relevant'
            elif sentiment_scores['compound'] < -0.05:
                category = 'less relevant'
            else:
                category = 'neutral'
            
            post_words = word_tokenize(text)
            if any(word in post_words for word in product_words):
                relevance = 'relevant'
            else:
                relevance = 'not relevant'
            
            data['relevance'] = relevance
            data['category'] = category

        post_data = [data for data in post_data if data['relevance'] != 'not relevant']

        return 'success', post_data
    except Exception as e:
        print("Rate limit reached. Please wait for a while before making more requests.", str(e))
        return 'fail', post_data



# Function to remove duplicate entries based on URL
def remove_duplicates(posts):
    unique_posts = []
    try:
        unique_posts = []
        post_urls = set()
        for post in posts:
            print("url",post["url"])
            if post["url"] not in post_urls:
                unique_posts.append(post)
                post_urls.add(post["url"])
        return 'success', unique_posts
    except Exception as e:
        print("Remove duplicated failed.", str(e))
        return 'fail', unique_posts

# def add_quotes(keyword):
#     return f'"{keyword}"'

# # usage
# keyword = add_quotes("text to video")
# for exact search

def global_search(keyword, reddit, sort_types=['relevance', 'new', 'hot', 'top']):
    global_search_posts = []
    try:
        for sort_type in sort_types:
            global_search_posts.extend([{
                "title": submission.title,
                "author": str(submission.author),
                "url": submission.url,
                "score": submission.score,
                "num_comments": submission.num_comments,
                "created_utc": submission.created_utc,
                "id": submission.id,
                "selftext": submission.selftext,
                "permalink": submission.permalink,
                "subreddit": submission.subreddit.display_name,
                "subreddit_name_prefixed": submission.subreddit_name_prefixed,
                "is_video": submission.is_video,
            } for submission in reddit.subreddit("all").search(keyword, time_filter="year", sort=sort_type, limit=None)])
        return 'success', global_search_posts
    except RedditAPIException as e:
        print("Rate limit reached. Please wait for a while before making more requests.", str(e))
        return 'RateLimit', global_search_posts
    except Exception as e:
        print("Rate limit reached. Please wait for a while before making more requests.", str(e))
        return 'fail', global_search_posts


def process_keyword(keyword,reddit_instsance,credential):

    # Perform a global search for the keyword
    msg, global_search_posts = global_search(keyword,reddit_instsance)
    if msg == 'RateLimit':
        print("Rate limit reached. Waiting for 10 minutes before retrying...")
        time.sleep(600)  # Wait for 10 minutes (600 seconds)
        print("Retrying search after waiting...")
        msg, global_search_posts = global_search(keyword,reddit_instsance)
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
        reddit_instsance = login_with_credential(credential)
        if reddit_instsance is None:
            # write in porject that no data failed...
            exit()
        msg, global_search_posts = global_search(keyword,reddit_instsance)
        if msg is not 'success':
            credential.current_status = 'free'
            credential.human_action = 'Yes'
            credential.save()
            # write in porject that no data failed...
            exit()

    print("global_search_posts",len(global_search_posts))

    # Find related subreddits for the keyword
    msg, related_subreddits = get_related_subreddits(keyword,reddit_instsance)
    if msg == 'RateLimit':
        print("Rate limit reached. Waiting for 10 minutes before retrying...")
        time.sleep(600)  # Wait for 10 minutes (600 seconds)
        print("Retrying search after waiting...")
        msg, global_search_posts = get_related_subreddits(keyword,reddit_instsance)
    elif msg == 'fail' or msg == 'UnknownError':
        print("Unknown error or failure occurred. Trying again with new credentials...")
        credential.current_status = 'free'
        credential.human_action = 'Yes'
        credential.save()
        credential = wait_and_check_for_free_credentials()
        reddit_instsance = login_with_credential(credential)
        if reddit_instsance is None:
            # write in porject that no data failed...
            exit()
        msg, global_search_posts = get_related_subreddits(keyword,reddit_instsance)
        if msg is not 'success':
            credential.current_status = 'free'
            credential.human_action = 'Yes'
            credential.save()
            # write in porject that no data failed...
            exit()

    print("related_subreddits",related_subreddits)

    # Search for posts within the related subreddits
    msg, subreddit_search_posts = search_posts_with_keyword(keyword, related_subreddits,reddit_instsance)
    if msg == 'RateLimit':
        print("Rate limit reached. Waiting for 10 minutes before retrying...")
        time.sleep(600)  # Wait for 10 minutes (600 seconds)
        print("Retrying search after waiting...")
        msg, global_search_posts = search_posts_with_keyword(keyword,reddit_instsance)
    elif msg == 'fail' or msg == 'UnknownError':
        print("Unknown error or failure occurred. Trying again with new credentials...")
        credential.current_status = 'free'
        credential.human_action = 'Yes'
        credential.save()
        credential = wait_and_check_for_free_credentials()
        reddit_instsance = login_with_credential(credential)
        if reddit_instsance is None:
            # write in porject that no data failed...
            exit()
        msg, global_search_posts = search_posts_with_keyword(keyword,reddit_instsance)
        if msg is not 'success':
            credential.current_status = 'free'
            credential.human_action = 'Yes'
            credential.save()
            # write in porject that no data failed...
            exit()

    # Combine the results from the global search and subreddit-specific searches
    combined_posts = global_search_posts + subreddit_search_posts
    print("combined_posts len", len(combined_posts))

    # Remove duplicate posts
    msg, unique_posts = remove_duplicates(combined_posts)
    unique_posts_len = len(unique_posts)
    print("unique_posts_len",unique_posts_len)

    # Analyze the posts
    msg, analyzed_posts = analyze_posts(unique_posts, keyword)
    analyzed_posts_len = len(analyzed_posts)
    print("analyzed_posts_len",analyzed_posts_len)
    
    # Convert lists of dictionaries into pandas DataFrames
    # df_combined = pd.DataFrame(combined_posts)
    # df_unique = pd.DataFrame(unique_posts)

    # # Save DataFrames as CSV files
    # df_combined.to_csv('combined_posts.csv', index=False)
    # df_unique.to_csv('unique_posts.csv', index=False)


    # Convert 'unique_posts' to JSON format
    json_data = json.dumps(analyzed_posts)

    print("Total unique posts:", analyzed_posts_len)

    return analyzed_posts,credential



def scrape_reddit(keywords):
    try:
        credential = wait_and_check_for_free_credentials()
        reddit_instsance = login_with_credential(credential)
        if reddit_instsance is None:
            # write in porject that no data failed...
            exit()
        
        for keyword in keywords:
            keyword = f"\"{keyword}\""
            # f'"{keyword}"'
            data,credential_modified  = process_keyword(keyword,reddit_instsance,credential)

        credential = credential_modified
        time.sleep(60)
        credential.current_status = 'free'
        credential.save()

    except Exception as e:
        print(e)


keywords = ["text to video"]

# Dictionary to store the results for each keyword
results = {}

# Process each keyword

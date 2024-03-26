import time
import praw
import json
import pandas as pd
from prawcore.exceptions import Forbidden
from nltk.tokenize import word_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer

# Reddit API Creds
client_id = 'FgxSw-LaHPfhP6K70rqgbg'
secret = "EgoFaB4MKZv-QAzgHbcScMLFdqGYaw"

# Reddit User Creds
user_name = "Ok-Radish-764"
pass_word = "Gpk@12345"

reddit = praw.Reddit(
    client_id= client_id,
    client_secret= secret,
    password=pass_word,
    user_agent="my_research_application_v1.0 by u/"+user_name,
    username=user_name,
    ratelimit_seconds=370
)

print("verify",reddit.user.me())

# exact=False
# related_subreddits = reddit.subreddits.search_by_name(keyword, exact=False)

def get_related_subreddits(keyword, min_subscribers=1000):
    related_subreddits = set()
    for subreddit in reddit.subreddits.search(keyword):
        if subreddit.subscribers is not None and subreddit.subscribers > min_subscribers:
            related_subreddits.add(subreddit.display_name)
    return related_subreddits

def search_posts_with_keyword(keyword, subreddits, time_filter="year"):
    submissions_data = []  # List to store submission data as dictionaries
    index = 0
    sort_types = ['relevance', 'new', 'hot', 'top']
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
    return submissions_data


def analyze_posts(post_data, product_description):
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

    return post_data


# Function to remove duplicate entries based on URL
def remove_duplicates(posts):
    unique_posts = []
    post_urls = set()
    for post in posts:
        print("url",post["url"])
        if post["url"] not in post_urls:
            unique_posts.append(post)
            post_urls.add(post["url"])
    return unique_posts


# def add_quotes(keyword):
#     return f'"{keyword}"'

# # usage
# keyword = add_quotes("text to video")
# for exact search

def global_search(keyword, sort_types=['relevance', 'new', 'hot', 'top']):
    global_search_posts = []
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
    return global_search_posts


def process_keyword(keyword):
    # Perform a global search for the keyword
    global_search_posts = global_search(keyword)
    print("global_search_posts",len(global_search_posts))

    # Find related subreddits for the keyword
    related_subreddits = get_related_subreddits(keyword)
    print("related_subreddits",related_subreddits)
    related_subreddits = {'machinelearningnews'}
    # related_subreddits = {'machinelearningnews', 'MachineLearning', 'Futurology'}

    # Search for posts within the related subreddits
    subreddit_search_posts = search_posts_with_keyword(keyword, related_subreddits)

    # Combine the results from the global search and subreddit-specific searches
    combined_posts = global_search_posts + subreddit_search_posts
    print("combined_posts len", len(combined_posts))

    # Remove duplicate posts
    unique_posts = remove_duplicates(combined_posts)
    unique_posts_len = len(unique_posts)
    print("unique_posts_len",unique_posts_len)

    # Analyze the posts
    descriptions = "Build, iterate, and design faster with Miro — the visual workspace for innovation."
    analyzed_posts = analyze_posts(unique_posts, descriptions)
    analyzed_posts_len = len(analyzed_posts)
    print("analyzed_posts_len",analyzed_posts_len)
    
    # Convert lists of dictionaries into pandas DataFrames
    df_unique = pd.DataFrame(unique_posts)
    df_analyzed = pd.DataFrame(analyzed_posts)

    # # Save DataFrames as CSV files
    df_unique.to_csv('df_unique.csv', index=False)
    df_analyzed.to_csv('df_analyzed.csv', index=False)


    # Convert 'unique_posts' to JSON format
    json_data = json.dumps(analyzed_posts)

    print("Total unique posts:", analyzed_posts_len)

    return analyzed_posts


keywords = ["text to video"]

# Dictionary to store the results for each keyword
results = {}

# Process each keyword
for keyword in keywords:
    keyword = f"\"{keyword}\""
    # f'"{keyword}"'
    data  = process_keyword(keyword)
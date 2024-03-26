
import praw
import datetime 
import time


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
    user_agent="demo_1 by u/Ok-Radish-764",
    username=user_name,
    ratelimit_seconds=60
)

print("verify",reddit.user.me())

if reddit.read_only:  # If the instance is read-only, it's not authenticated
    print("Reddit account is not authenticated.")
else:
    print("Reddit account is authenticated.")

subreddit = reddit.subreddit("python")


index = 0

# Define an empty list to store the search results
search_results = []

# Perform the initial search
query = 'Generative AI'
for submission in subreddit.search(query, limit=1000):  # You can adjust the limit as needed
    print("submission 33", submission.url)
    print("submission 34", submission.title)
    index = index + 1
    print(index)
    search_results.append(submission)

# Fetch more results using pagination
while len(search_results) < 500:  # Specify the desired number of results
    last_submission = search_results[-1]
    for submission in subreddit.search(query, limit=1000, params={'after': last_submission.fullname}):
        print("submission 34", submission.url)
        index = index + 1
        print(index)
        search_results.append(submission)
    if last_submission == search_results[-1]:  # Break the loop if no new submissions are found
        break

print("search_results",search_results)
print("search_results_len ",len(search_results))

print("index",index)



# ------------------------------------------------------

        # time.sleep(1)

# exact=False

# related_subreddits = reddit.subreddits.search_by_name(keyword, exact=False)

# for subreddit in related_subreddits:
#     for submission in subreddit.search(keyword, limit=None, time_filter="all"):
#         print(submission.url)


# -----------------------------------------------------------------------------------------
# import praw

# # Reddit API Creds
# client_id = 'FgxSw-LaHPfhP6K70rqgbg'
# secret = "EgoFaB4MKZv-QAzgHbcScMLFdqGYaw"

# # Reddit User Creds
# user_name = "Ok-Radish-764"
# pass_word = "Gpk@12345"

# reddit = praw.Reddit(
#     client_id=client_id,
#     client_secret=secret,
#     password=pass_word,
#     user_agent="demo_1 by u/Ok-Radish-764",
#     username=user_name
# )



# def get_related_subreddits(keyword):
#     related_subreddits = set()
#     for subreddit in reddit.subreddits.search(keyword):
#         related_subreddits.add(subreddit.display_name)
#         print ("subreddit.display_name",subreddit)
#         print ("subreddit.display_name",subreddit.display_name)
#     return related_subreddits

# def search_posts_in_subreddits(keyword, related_subreddits):
#     index = 0
#     for subreddit_name in related_subreddits:
#         subreddit = reddit.subreddit(subreddit_name)
#         print(f"Searching in r/{subreddit_name}...")
#         for submission in subreddit.search(keyword, time_filter="all", limit=None):
#             index = index +1
#             # print(submission.url)
#             print("index",index)

# keyword = "python"  # Replace with your dynamic keyword

# index = 0
# related_subreddits = get_related_subreddits(keyword)
# related_subreddits = {"Python"}
# print("related_subreddits", related_subreddits)
# search_posts_in_subreddits(keyword, related_subreddits)
# print("index",index)



# ----------------------------------------------

# NOrmal praw logic:


# Reddit API Creds

# client_id = 'FgxSw-LaHPfhP6K70rqgbg'
# secret = "EgoFaB4MKZv-QAzgHbcScMLFdqGYaw"

# # Reddit User Creds
# user_name = "Ok-Radish-764"
# pass_word = "Gpk@12345"

# reddit = praw.Reddit(
#     client_id= client_id,
#     client_secret= secret,
#     password=pass_word,
#     user_agent="demo_1 by u/Ok-Radish-764",
#     username=user_name,
#     ratelimit_seconds=10
# )

# print("verify",reddit.user.me())

# url = "https://www.reddit.com/search?q=text+to+video&sort=relevance&type=post&t=all"


# index =0
# for submission in reddit.subreddit("all").search("python",time_filter="year", limit=None):
#     print(submission.url)
#     index = index + 1
#     print(index)

---------------------------------------------------------------------------


import time
import praw
import pandas as pd
from prawcore.exceptions import Forbidden

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

def get_related_subreddits(keyword, min_subscribers=1000):
    related_subreddits = set()
    for subreddit in reddit.subreddits.search(keyword):
        if subreddit.subscribers is not None and subreddit.subscribers > min_subscribers:
            related_subreddits.add(subreddit.display_name)
    return related_subreddits

def search_posts_with_keyword(keyword, subreddits, time_filter="year"):
    submissions_data = []
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
                    }
                    submissions_data.append(submission_data)
        except Forbidden:
            print(f"Skping pvt subredit: {subreddit_name}")
    return submissions_data

# Function to remove duplicate entries
def remove_duplicates(posts):
    unique_posts = []
    post_urls = set()
    for post in posts:
        print("url",post["url"])
        if post["url"] not in post_urls:
            unique_posts.append(post)
            post_urls.add(post["url"])
    return unique_posts

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
            "is_video": submission.is_video,
        } for submission in reddit.subreddit("all").search(keyword, time_filter="year", sort=sort_type, limit=None)])
    return global_search_posts

def process_keyword(keyword):
    global_search_posts = global_search(keyword)
    related_subreddits = get_related_subreddits(keyword)
    subreddit_search_posts = search_posts_with_keyword(keyword, related_subreddits)
    combined_posts = global_search_posts + subreddit_search_posts
    unique_posts = remove_duplicates(combined_posts)
    return unique_posts

keywords = ["text to video"]

for keyword in keywords:
    data  = process_keyword(keyword)



















    ----------------------------------------------------------------

try:
    credential = wait_and_check_for_free_credentials()
    app = login_with_credential(credential)
    if app is None:
        exit()

    for keyword in keywords:
        keyword = f"\"{keyword}\""
        print(f"Searching for latest")
        latest_tweets = search_tweets(app, keyword, SearchFilters.Latest(), pages, wait_time)

        latest_tweet_data = extract_tweet_data(latest_tweets)
        time.sleep(wait_time)

        print(f"Searching for top")
        top_tweets = search_tweets(app, keyword, pages, wait_time)

        top_tweet_data = extract_tweet_data(top_tweets)
        all_tweet_data = latest_tweet_data + top_tweet_data
        all_unique_tweet_data = remove_duplicates(all_tweet_data)

        analyze_tweets = analyze_tweets(all_unique_tweet_data, product_description)

        print("Number of analyze_tweets:", len(analyze_tweets))

        # Need to make Credentials Free
except Exception as e:
    print(e)

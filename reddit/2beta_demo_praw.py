import time
import praw
import json
import pandas as pd
from prawcore.exceptions import Forbidden
from .models import RedditCred

MAX_LOGIN_RETRIES = 3  # Maximum number of login retry attempts
MAX_CHECKS = 9  # Maximum number of checks for free credentials
CHECK_INTERVAL_SECONDS = 300  # Interval between each check for free credentials (300 seconds = 5 minutes)

def get_free_credential():
    return RedditCred.objects.filter(current_status='free').order_by('-human_action').first()

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
            credential.save()
            print(f"Error occurred with credentials for {credential.username}. Retrying... ({retries}/{MAX_LOGIN_RETRIES})")
            credential = wait_and_check_for_free_credentials()  # Get a new credential
    print(f"Failed to login with credentials for {credential.username} after {MAX_LOGIN_RETRIES} attempts.")
    return None

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

def get_related_subreddits(reddit, keyword, min_subscribers=1000):
    related_subreddits = set()
    for subreddit in reddit.subreddits.search(keyword):
        if subreddit.subscribers is not None and subreddit.subscribers > min_subscribers:
            related_subreddits.add(subreddit.display_name)
    return related_subreddits

def search_posts_with_keyword(reddit, keyword, subreddits, time_filter="year"):
    submissions_data = []  # List to store submission data as dictionaries
    index = 0
    sort_types = ['relevance', 'new', 'hot', 'top']
    for subreddit_name in subreddits:
        print("current subreddit name: ", subreddit_name)
        try:
            subreddit = reddit.subreddit(subreddit_name)
            for sort_type in sort_types:
                for submission in subreddit.search(keyword, time_filter=time_filter, sort=sort_type, limit=None):
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
                        "is_self": submission.is_self,
                        "subreddit_name_prefixed": submission.subreddit_name_prefixed,
                        "is_video": submission.is_video,
                    }
                    submissions_data.append(submission_data)
        except Forbidden:
            print(f"Skipping private subreddit: {subreddit_name}")
    return submissions_data

def remove_duplicates(posts):
    unique_posts = []
    post_urls = set()
    for post in posts:
        if post["url"] not in post_urls:
            unique_posts.append(post)
            post_urls.add(post["url"])
    return unique_posts

def scrape_reddit(keywords):
    try:
        credential = wait_and_check_for_free_credentials()
        reddit = login_with_credential(credential)
        if reddit is None:
            exit()

        global_search_posts = []
        for keyword in keywords:
            keyword = f'"{keyword}"'
            sort_types = ['relevance', 'new', 'hot', 'top']
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
                    "is_self": submission.is_self,
                    "subreddit_name_prefixed": submission.subreddit_name_prefixed,
                    "is_video": submission.is_video,
                } for submission in reddit.subreddit("all").search(keyword, time_filter="year", sort=sort_type, limit=None)])

        print("global_search_posts", len(global_search_posts))

        combined_posts = global_search_posts
        related_subreddits = set()
        for keyword in keywords:
            related_subreddits.update(get_related_subreddits(reddit, keyword))

        subreddit_search_posts = search_posts_with_keyword(reddit, keyword, related_subreddits)
        combined_posts.extend(subreddit_search_posts)

        print("combine post length", len(combined_posts))

        unique_posts = remove_duplicates(combined_posts)
        total_posts = len(unique_posts)

        json_data = json.dumps(unique_posts)

        print("Total unique posts:", total_posts)
    
    except Exception as e:
        print(e)

# Configuration
keywords = ['text to video']
scrape_reddit(keywords)

from tweety import Twitter
from tweety.filters import SearchFilters
from tweety.exceptions_ import RateLimitReached, DeniedLogin, UnknownError

app = Twitter("session4")
app.sign_in('britt_simar', 'Gpk@12345')
print(app.user)


tweets = app.search('python',pages=200)
tweet_count = len(tweets)
print("Number of tweets:", tweet_count)

index = 0
for tweet in tweets:
    print("******/n",tweet)
    print("******/n",tweet.text)
    index = index + 1
    print("index",index)



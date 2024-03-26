from tweety import Twitter

# auth_token = """fddd8af7c216ebf8fd9d52a4b3a24ba3926f3726"""
# 
# Cookies can be a str or a dict

# app = Twitter("session2")
# app.load_auth_token(auth_token)
# print(app.me)

app = Twitter("session2")
app.sign_in('tob_12345', 'Gpk@12345')
print(app.user)

# app.search("#pakistan", filter_=SearchFilters.Latest())

tweets = app.search('"text to video"',pages=1)
tweet_count = len(tweets)
print("Number of tweets:", tweet_count)
for tweet in tweets:
    print("******/n",tweet)
    print("******/n",tweet.text)



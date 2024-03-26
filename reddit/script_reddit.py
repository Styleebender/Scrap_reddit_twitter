import requests
from requests.auth import HTTPBasicAuth
import csv
from pprint import pprint

# Reddit API Creds
client_id = 'FgxSw-LaHPfhP6K70rqgbg'
secret = "EgoFaB4MKZv-QAzgHbcScMLFdqGYaw"

# Reddit User Creds
username = "Ok-Radish-764"
password = "Gpk@12345"

# Reddit API access token
auth = requests.auth.HTTPBasicAuth(client_id, secret)
data = {"grant_type": "password", "user": username,"password": password}
headers = {"User-Agent": "demo_1 by u/Ok-Radish-764"}
r= requests.post("https://www.reddit.com/api/v1/access_token", auth=auth, data=data, headers=headers)

reddit_token = r.json()["access_token"]

#Set Up Reddit API Headers

header = {**headers, **{'Authorization': f"bearer {reddit_token}"}}

# Kws to search for

q_list = ["text to video"]

for q in q_list:
    permalink_list = []
    r = requests.get(f"https://www.reddit.com/search?q=test&sort=relevance&type=post&t=all")
    r_json = r.json()
    pprint(r_json)



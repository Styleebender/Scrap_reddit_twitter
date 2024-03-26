import requests
from requests.auth import HTTPBasicAuth
import csv
from pprint import pprint

r = requests.get(f"https://old.reddit.com/search.json?q=test+to+video&sort=relevance&type=post&t=all")

r_json = r.json()
# print("r_json",r_json.length)
print("r_json",len(r_json))
pprint(r_json["data"]['after'])

# q_list = ["text to video"]

# for q in q_list:
#     permalink_list = []
#     r = requests.get(f"https://old.reddit.com/search.json?q=test%to%video&sort=relevance&type=post&t=all")
#     r_json = r.json()
#     pprint(r_json)
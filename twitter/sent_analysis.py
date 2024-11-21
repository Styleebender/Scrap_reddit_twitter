import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize

# Initialize the VADER sentiment intensity analyzer
sia = SentimentIntensityAnalyzer()

# Read the CSV file
df = pd.read_csv('all_unique_tweet_data.csv')

# Provide a description of your product
product_description = """A free text to video tool Creating video from text
is an AI model that can create realistic and imaginative scenes from text instructions.
"""

# Tokenize the product description
product_words = word_tokenize(product_description)

# Create a new column for the relevance of each tweet
df['relevance'] = ''

# Analyze each tweet
for index, row in df.iterrows():
    sentiment_scores = sia.polarity_scores(row['text'])
    
    # Check if any of the words in the product description appear in the tweet
    tweet_words = word_tokenize(row['text'])
    if any(word in tweet_words for word in product_words):
        # Categorize the tweet based on its compound sentiment score
        if sentiment_scores['compound'] > 0.05:
            relevance = 'highly relevant'
        elif sentiment_scores['compound'] < -0.05:
            relevance = 'less relevant'
        else:
            relevance = 'neutral'
    else:
        relevance = 'not relevant'
    
    # Update the 'relevance' column
    df.at[index, 'relevance'] = relevance

# Remove the tweets that are not relevant
df = df[df['relevance'] != 'not relevant']

# Write the results to a new CSV file
df.to_csv('filtered_tweets.csv', index=False)

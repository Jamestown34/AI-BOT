import os
import logging
import datetime
import time
import schedule
import random
from requests_oauthlib import OAuth1Session
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.INFO)

# WEEKLY TOPIC
weekly_topic = "Hypothesis Testing"

# PROMPTS for this week's topic
prompts = [
    f"Write a simple and engaging definition of {weekly_topic} with an everyday example.",
    f"Share a myth or misconception about {weekly_topic} and correct it clearly.",
    f"Give a useful tip for someone learning how to use {weekly_topic} in data analysis.",
    f"Suggest a good resource (book, course, video) for beginners to learn {weekly_topic}."
]

# Set up Twitter OAuth
def setup_twitter_oauth():
    return OAuth1Session(
        os.environ.get("TWITTER_API_KEY"),
        client_secret=os.environ.get("TWITTER_API_SECRET"),
        resource_owner_key=os.environ.get("TWITTER_ACCESS_TOKEN"),
        resource_owner_secret=os.environ.get("TWITTER_ACCESS_SECRET")
    )

# Use OpenAI to generate tweet text from a prompt
def generate_tweet(prompt):
    import openai
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
    )
    return response.choices[0].message['content'].strip()

# Post a tweet
def post_tweet(tweet_text):
    oauth = setup_twitter_oauth()
    if not oauth:
        logging.error("OAuth setup failed.")
        return
    response = oauth.post("https://api.twitter.com/2/tweets", json={"text": tweet_text})
    if response.status_code == 201:
        logging.info(f"✅ Tweet posted: {tweet_text}")
    else:
        logging.error(f"❌ Failed to post tweet: {response.text}")

# Pick a random prompt and post tweet
def post_random_tweet():
    prompt = random.choice(prompts)
    tweet = generate_tweet(prompt)
    post_tweet(tweet)

# Schedule 4 tweets per day
def run_schedule():
    logging.info("🚀 Scheduler started")
    times = ["06:00", "12:00", "18:00", "23:00"]
    for t in times:
        schedule.every().day.at(t).do(post_random_tweet)
    while True:
        schedule.run_pending()
        time.sleep(1)

import os
import logging
import datetime
import time
import schedule
import random
from requests_oauthlib import OAuth1Session
import google.generativeai as genai

# Set up logging
logging.basicConfig(level=logging.INFO)

# ✅ WEEKLY TOPIC — update this anytime
weekly_topic = "Hypothesis Testing"

# ✅ Expanded list of PROMPTS
prompts = [
    f"Write a simple and engaging definition of {weekly_topic} with an everyday example.",
    f"Share a myth or misconception about {weekly_topic} and correct it clearly.",
    f"Give a useful tip for someone learning how to use {weekly_topic} in data analysis.",
    f"Suggest a good beginner-friendly YouTube video or book for learning {weekly_topic}.",
    f"Create a mini case study where {weekly_topic} is applied in a real-world scenario.",
    f"Write a one-sentence summary that explains why {weekly_topic} is important in statistics.",
    f"List 3 things every data analyst should know about {weekly_topic}.",
    f"Explain the difference between Type I and Type II errors in the context of {weekly_topic}.",
    f"How would you explain {weekly_topic} to a 10-year-old?",
    f"Write a 2-line inspirational quote related to learning {weekly_topic}.",
    f"What's a common mistake beginners make when doing {weekly_topic}, and how can they avoid it?",
    f"Explain how {weekly_topic} connects to decision-making in business."
]

# ✅ Set up Twitter OAuth
def setup_twitter_oauth():
    return OAuth1Session(
        os.environ.get("TWITTER_API_KEY"),
        client_secret=os.environ.get("TWITTER_API_SECRET"),
        resource_owner_key=os.environ.get("TWITTER_ACCESS_TOKEN"),
        resource_owner_secret=os.environ.get("TWITTER_ACCESS_SECRET")
    )

# ✅ Use Gemini to generate tweet text
def generate_tweet(prompt):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-pro")
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(f"⚠️ Gemini error: {e}")
        return "Learning about data, one insight at a time. 📊 #DataScience"

# ✅ Post a tweet to Twitter
def post_tweet(tweet_text):
    oauth = setup_twitter_oauth()
    if not oauth:
        logging.error("OAuth setup failed.")
        return
    response = oauth.post("https://api.twitter.com/2/tweets", json={"text": tweet_text})
    if response.status_code == 201:
        logging.info(f"✅ Tweet posted: {tweet_text}")
    else:
        logging.error(f"❌ Failed to post tweet: {response.status_code} - {response.text}")

# ✅ Pick a random prompt and post the tweet
def post_random_tweet():
    prompt = random.choice(prompts)
    logging.info(f"🧠 Using prompt: {prompt}")
    tweet = generate_tweet(prompt)
    post_tweet(tweet)

# ✅ Schedule 4 tweets per day
def run_schedule():
    logging.info("🚀 Scheduler started")
    times = ["06:00", "12:00", "18:00", "23:00"]
    for t in times:
        schedule.every().day.at(t).do(post_random_tweet)
    while True:
        schedule.run_pending()
        time.sleep(1)

# ✅ Uncomment this line if you want to run it manually for local testing
# post_random_tweet()

# ✅ To use scheduling locally (optional):
# run_schedule()

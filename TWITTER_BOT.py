import os
import logging
import random
import google.generativeai as genai
from requests_oauthlib import OAuth1Session
import datetime
import schedule
import time
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[logging.StreamHandler()] + ([logging.FileHandler('twitter_bot.log')] if os.environ.get('LOG_FILE') else [])
)

# Twitter Setup
def setup_twitter_oauth():
    logging.info("➡️ Entering setup_twitter_oauth()")
    consumer_key = os.environ.get("TWITTER_API_KEY")
    consumer_secret = os.environ.get("TWITTER_API_SECRET")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.environ.get("TWITTER_ACCESS_SECRET")

    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        logging.error("❌ Missing Twitter API credentials as environment variables.")
        return None

    return OAuth1Session(
        consumer_key,
        client_secret=consumer_secret,
        resource_owner_key=access_token,
        resource_owner_secret=access_token_secret,
    )

# Gemini AI Setup
def setup_gemini_api():
    logging.info("➡️ Entering setup_gemini_api()")
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logging.error("❌ Missing Gemini API key as environment variable.")
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.environ.get('GEMINI_MODEL_NAME', 'models/gemini-1.5-pro-latest'))
        return model
    except Exception as e:
        logging.error(f"❌ Gemini API configuration failed: {e}")
        return None

# Generate Tweet
def generate_tweet(gemini_model, topic):
    if not gemini_model:
        return None

    tweet_styles_str = os.environ.get('TWEET_STYLES')
    tweet_styles = json.loads(tweet_styles_str) if tweet_styles_str else [
        "Share an insightful fact about {topic}. Keep it concise and engaging.",
        "Write a thought-provoking question about {topic} to spark discussion.",
        "Post a quick tip or hack related to {topic}.",
        "Create a short and witty take on {topic}.",
        "Write a motivational quote related to {topic}.",
        "Provide a little-known historical fact about {topic}.",
        "Break down a complex concept related to {topic} in simple terms."
    ]

    max_retries = int(os.environ.get('MAX_TWEET_GENERATION_RETRIES', '5'))
    max_length = int(os.environ.get('MAX_TWEET_LENGTH', '280'))
    retry_count = 0

    while retry_count < max_retries:
        selected_style = random.choice(tweet_styles).format(topic=topic)

        try:
            response = gemini_model.generate_content(selected_style)
            tweet_text = response.text.strip()

            if len(tweet_text) <= max_length:
                logging.info(f"✅ Generated tweet: {tweet_text}")
                return tweet_text
            else:
                logging.warning(f"⚠️ Generated tweet exceeds maximum length ({len(tweet_text)} characters). Retrying.")
                retry_count += 1

        except Exception as e:
            logging.error(f"❌ Gemini API tweet generation failed (attempt {retry_count + 1}/{max_retries}): {e}")
            retry_count += 1

    logging.error("❌ Failed to generate a suitable tweet after multiple retries.")
    return None

# Post Tweet
def post_tweet(oauth, tweet_text):
    if not oauth or not tweet_text:
        logging.error("❌ Cannot post tweet. Missing OAuth or tweet text.")
        return

    payload = {"text": tweet_text}
    try:
        response = oauth.post("https://api.twitter.com/2/tweets", json=payload)
        if response.status_code != 201:
            logging.error(f"❌ Twitter API error: {response.status_code} {response.text}")
            return

        tweet_id = response.json()['data']['id']
        logging.info(f"✅ Tweet posted: {tweet_text} (ID: {tweet_id})")
    except Exception as e:
        logging.error(f"❌ Twitter API error: {e}")

# Scheduled Tweet Posting (for one execution)
def run_scheduled_tweets_once():
    logging.info("✅ run_scheduled_tweets_once() function has started for this execution.")
    schedule_times_str = os.environ.get('SCHEDULE_TIMES', '["07:00", "13:00", "19:00"]')
    schedule_times = json.loads(schedule_times_str)
    tweets_to_post = []

    for time_str in schedule_times:
        try:
            schedule.every().day.at(time_str).do(lambda t=time_str: tweets_to_post.append(generate_and_post(t)))
            logging.info(f"⏰ Scheduled generation for {time_str}")
        except schedule.InvalidTimeError:
            logging.error(f"❌ Invalid schedule time: {time_str}")

    # Run pending scheduled tasks for a limited duration (e.g., 5 hours)
    end_time = time.time() + (5 * 60 * 60)  # Run for 5 hours
    while time.time() < end_time and schedule.get_jobs():
        schedule.run_pending()
        time.sleep(1)

    logging.info("✅ Scheduled tasks completed for this execution.")
    return [tweet for tweet in tweets_to_post if tweet is not None]

def generate_and_post(schedule_time):
    logging.info(f"➡️ Attempting to generate and post for schedule time: {schedule_time}")
    oauth = setup_twitter_oauth()
    gemini_model = setup_gemini_api()

    if not oauth:
        logging.error("❌ Twitter OAuth failed.")
        return None
    if not gemini_model:
        logging.error("❌ Gemini AI setup failed.")
        return None

    topics_str = os.environ.get('TOPICS')
    topics = json.loads(topics_str) if topics_str else [
        "ETL (Extract, Transform, Load) Processes",
        "Data Streaming Technologies",
        "DevOps for Data Science (MLOps)",
        "Internet of Things (IoT) Data Analysis",
        "The aim of Every business data analysis ",
        "Build your Thought process in every data analysis task",
        "Anomaly Detection in Data",
        "Open Source Data Science Tools",
        "Data Science Career Advice",
        "Writing Technical Documentation",
        "SQL Tips for Data Analysts",
        "Machine Learning Model Optimization",
        "Big Data Trends",
        "Most used shortcut in Excel",
        "Data Security and Privacy",
        "Phython Skills for data science",
        "Power BI and Tableau as first choice tools",
        "Feature Engineering in ML",
        "Python Libraries for Data Science",
        "Version Control for Data Projects (Git)",
        "Data Science Project Management"
    ]

    topic = random.choice(topics)
    logging.info(f"🔹 Generating tweet for topic: {topic}")
    tweet_text = generate_tweet(gemini_model, topic)

    if tweet_text:
        logging.info("🔹 Posting tweet now...")
        post_tweet(oauth, tweet_text)
        logging.info("✅ Tweet successfully posted!")
        return tweet_text
    else:
        logging.error("❌ Tweet generation failed for this schedule time.")
        return None

if __name__ == "__main__":
    logging.info("🚀 Running Twitter bot (once per scheduled execution) ...")
    try:
        run_scheduled_tweets_once()
    except Exception as e:
        logging.error(f"❌ Error in run_scheduled_tweets_once: {e}")

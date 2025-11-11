import streamlit as st
import pandas as pd
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import functions from other project files
from user_db import initialize_database, add_subscription, remove_subscription
from scraper import group_and_send_alerts, load_preprocessed_tweets
from tweet_store import initialize_tweet_database, save_tweets_to_db
import twitter_search

# --- Configuration ---
MOCK_TWEETS_FILE = "moc_tweets.json"

# --- Wrapper Functions ---

def get_subscriptions_df():
    """Gets subscriptions as a pandas DataFrame for Streamlit display."""
    import sqlite3
    try:
        con = sqlite3.connect("subscriptions.db")
        df = pd.read_sql_query("SELECT location, email FROM subscriptions ORDER BY location", con)
    except (pd.io.sql.DatabaseError, sqlite3.OperationalError):
        # Return an empty DataFrame if the table or DB doesn't exist yet
        df = pd.DataFrame(columns=['location', 'email'])
    finally:
        if 'con' in locals() and con:
            con.close()
    return df

def fetch_and_analyze_tweets_live():
    """Fetches and processes live tweets, including images, and saves them to the DB."""
    try:
        import ollama
    except ImportError:
        st.error("The 'ollama' library is not installed. Please run 'pip install ollama' to use this feature.")
        return []

    bearer_token = os.getenv("BEARER_TOKEN")
    if not bearer_token:
        st.error("Bearer token not found! Check your .env file.")
        return []

    search_url = "https://api.twitter.com/2/tweets/search/recent"
    query_params = {
        'query': 'disaster OR emergency OR flooding OR fire India -is:retweet',
        'max_results': 10,
        'expansions': 'author_id,attachments.media_keys',
        'tweet.fields': 'created_at,attachments',
        'media.fields': 'url'
    }

    headers = twitter_search.create_headers(bearer_token)
    results_list = []

    try:
        with st.spinner("Fetching recent tweets..."):
            json_response = twitter_search.connect_to_endpoint(search_url, headers, query_params)

        if "data" in json_response:
            media_includes = json_response.get("includes", {}).get("media", [])
            media_map = {media["media_key"]: media.get("url") for media in media_includes}

            with st.spinner("Analyzing tweets with local NLP and Vision models..."):
                for tweet in json_response["data"]:
                    location, disaster_type = twitter_search.extract_disaster_info(tweet['text'])
                    image_url = "N/A"
                    detected_landmark = "N/A"

                    if "attachments" in tweet and "media_keys" in tweet["attachments"]:
                        for key in tweet["attachments"]["media_keys"]:
                            if key in media_map and media_map[key]:
                                image_url = media_map[key]
                                detected_landmark = twitter_search.analyze_image_for_landmarks(image_url)
                                break

                    results_list.append({
                        "author_id": tweet['author_id'],
                        "timestamp": tweet['created_at'],
                        "text": tweet['text'],
                        "extracted_location": location,
                        "disaster_type": disaster_type,
                        "image_url": image_url,
                        "detected_landmark": detected_landmark
                    })
        else:
            st.warning("No tweets found for the query.")

        if results_list:
            save_tweets_to_db(results_list)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.info("Ensure the Ollama application is running with 'llama3' and 'llava' models available.")

    return results_list

# --- Streamlit UI ---

st.set_page_config(page_title="Disaster Alert System", layout="wide")
st.title("Disaster Alert System Dashboard")

# Initialize the databases on first run
initialize_database()
initialize_tweet_database()

# --- Sidebar for Actions ---
st.sidebar.header("Actions")
with st.sidebar.form("add_sub_form"):
    st.subheader("Add Subscription")
    new_loc = st.text_input("Location (e.g., Bengaluru)").lower()
    new_email = st.text_input("Email Address")
    if st.form_submit_button("Add Subscription"):
        if new_loc and new_email:
            add_subscription(new_loc, new_email)
            st.sidebar.success(f"Added subscription for {new_email} in {new_loc}.")
            st.rerun()

with st.sidebar.form("remove_sub_form"):
    st.subheader("Remove Subscription")
    rem_loc = st.text_input("Location to remove").lower()
    rem_email = st.text_input("Email to remove")
    if st.form_submit_button("Remove Subscription"):
        if rem_loc and rem_email:
            remove_subscription(rem_loc, rem_email)
            st.sidebar.warning(f"Removed subscription for {rem_email} in {rem_loc}.")
            st.rerun()

# --- Main Content Area ---
st.header("Current Subscriptions")
st.dataframe(get_subscriptions_df(), use_container_width=True)

st.header("Disaster Alerting")
st.info("Step 1: Fetch tweets. Step 2: Review, edit, and send alerts.")

# Use session state to hold tweets
if 'tweets' not in st.session_state:
    st.session_state.tweets = []

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("1. Fetch Tweets")
    use_mock_data = st.checkbox("Use Mock Data (moc_tweets.json)", value=True)
    if st.button("Fetch and Analyze Tweets"):
        if use_mock_data:
            st.session_state.tweets = load_preprocessed_tweets(MOCK_TWEETS_FILE)
        else:
            st.session_state.tweets = fetch_and_analyze_tweets_live()
        
        if st.session_state.tweets:
            st.success(f"Loaded {len(st.session_state.tweets)} tweets for review.")
        st.rerun()

with col2:
    st.subheader("2. Review, Edit & Send Alerts")
    if st.session_state.tweets:
        st.write("You can edit the extracted location and disaster type before sending alerts.")
        
        edited_tweets = st.data_editor(
            pd.DataFrame(st.session_state.tweets),
            column_config={
                "extracted_location": "Location",
                "disaster_type": "Disaster Type",
                "image_url": st.column_config.LinkColumn("Image"),
                "detected_landmark": "Detected Landmark"
            },
            disabled=["author_id", "timestamp", "text", "image_url", "detected_landmark"],
            use_container_width=True,
            num_rows="dynamic",
            column_order=("text", "image_url", "detected_landmark", "extracted_location", "disaster_type", "timestamp")
        )
        
        if st.button("Group and Send Alerts to Subscribers"):
            tweets_to_send = edited_tweets.to_dict('records')
            with st.spinner("Grouping tweets, checking for duplicates, and sending alerts..."):
                group_and_send_alerts(tweets_to_send)
                st.success("Alert processing complete! Check console for details.")
    else:
        st.write("No tweets fetched yet. Click the button on the left.")
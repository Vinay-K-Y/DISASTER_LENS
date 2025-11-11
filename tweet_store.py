# tweet_store.py

import sqlite3

TWEET_DB_FILE = "tweets.db"

def initialize_tweet_database():
    """Creates the tweets database and raw_tweets table if they don't exist."""
    con = sqlite3.connect(TWEET_DB_FILE)
    cur = con.cursor()
    # ADD the new detected_landmark column
    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_tweets (
            id INTEGER PRIMARY KEY,
            author_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            text TEXT NOT NULL,
            image_url TEXT,
            extracted_location TEXT,
            disaster_type TEXT,
            detected_landmark TEXT, 
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()
    print("✅ Tweet database initialized successfully.")

def save_tweets_to_db(tweets_list):
    """Saves a list of processed tweets to the raw_tweets table."""
    if not tweets_list:
        return

    con = sqlite3.connect(TWEET_DB_FILE)
    cur = con.cursor()

    tweets_to_save = [
        (
            t.get('author_id'), t.get('timestamp'), t.get('text'),
            t.get('image_url'), t.get('extracted_location'), t.get('disaster_type'),
            t.get('detected_landmark', 'N/A') # Get the landmark, default to N/A
        )
        for t in tweets_list
    ]
    
    # UPDATE the INSERT statement
    cur.executemany(
        "INSERT INTO raw_tweets (author_id, timestamp, text, image_url, extracted_location, disaster_type, detected_landmark) VALUES (?, ?, ?, ?, ?, ?, ?)",
        tweets_to_save
    )

    con.commit()
    print(f"✅ Saved {cur.rowcount} new tweets to the tweet database.")
    con.close()
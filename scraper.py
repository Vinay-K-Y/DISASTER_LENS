import json
from mail_alert import send_email_alert
from user_db import get_subscribers_for_locations, check_if_alert_sent_recently, log_sent_alert

# --- Location Normalization ---
LOCATION_ALIASES = {
    "bangalore": "bengaluru",
    "bombay": "mumbai"
}

def normalize_location(location):
    """Normalizes location names using the alias dictionary."""
    loc_lower = location.lower()
    return LOCATION_ALIASES.get(loc_lower, loc_lower)

def load_preprocessed_tweets(json_file):
    """Loads tweets from a JSON file that have already been analyzed."""
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)

def group_and_send_alerts(disaster_tweets):
    """
    Groups alerts by normalized location and disaster, checks for duplicates,
    and sends one consolidated email per new event group.
    """
    alerts_to_group = {}
    unique_locations = set()

    for tweet in disaster_tweets:
        loc = tweet.get("extracted_location")
        disaster = tweet.get("disaster_type")

        if loc and loc != "N/A" and disaster and disaster != "N/A":
            normalized_loc = normalize_location(loc)
            unique_locations.add(normalized_loc)
            
            alert_key = (normalized_loc, disaster.lower())
            
            if alert_key not in alerts_to_group:
                alerts_to_group[alert_key] = []
            
            alerts_to_group[alert_key].append(tweet)

    subscribers_map = get_subscribers_for_locations(list(unique_locations))

    for (location, disaster_type), tweets in alerts_to_group.items():
        if check_if_alert_sent_recently(location, disaster_type):
            print(f"🚫 Alert for {disaster_type} in {location} already sent recently. Skipping.")
            continue

        subscribers = subscribers_map.get(location, [])
        if not subscribers:
            continue

        email_body_parts = [f"Found {len(tweets)} report(s) for a {disaster_type.title()} in {location.title()}:\n"]
        for tweet in tweets:
            user = tweet.get('author_id')
            email_body_parts.append(f"-> Reported by @{user} at {tweet['timestamp']}:\n   \"{tweet['text']}\"")
            
            image_url = tweet.get("image_url")
            if image_url and image_url != "N/A":
                email_body_parts.append(f"   Image: {image_url}\n")
            else:
                email_body_parts.append("\n")
        
        final_body = "\n".join(email_body_parts)
        subject = f"🚨 {disaster_type.title()} Alert in {location.title()}"
        
        print(f"Found new event: {disaster_type.title()} in {location.title()}. Notifying {len(subscribers)} subscriber(s).")
        for email in subscribers:
            send_email_alert(email, subject, final_body)
        
        log_sent_alert(location, disaster_type)

def main():
    tweets = load_preprocessed_tweets("moc_tweets.json")
    print("🚀 Reading pre-analyzed file, grouping, and sending alerts...")
    group_and_send_alerts(tweets)
    print("✅ Process complete.")

if __name__ == "__main__":
    main()
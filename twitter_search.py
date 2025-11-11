import requests
import os
import json
import ollama
from tweet_store import initialize_tweet_database, save_tweets_to_db

def extract_disaster_info(tweet_text):
    """
    Uses Ollama with llama3 to extract location and disaster type from a tweet.
    """
    system_prompt = f"""
    You are an expert information extractor. From the tweet provided, identify:
    1. The city or primary location of the event.
    2. The type of disaster (e.g., Flood, Fire, Earthquake, Traffic, etc.).

    Respond ONLY with a valid JSON object like this: {{"location": "City Name", "disaster_type": "Disaster"}}
    If a value isn't found, use "N/A".

    Tweet: "{tweet_text}"
    """
    try:
        response = ollama.generate(
            model="llama3",
            prompt=system_prompt,
            format="json",
            stream=False
        )
        data = json.loads(response['response'])
        location = data.get("location", "N/A").strip()
        disaster_type = data.get("disaster_type", "N/A").strip()
        return location, disaster_type
    except json.JSONDecodeError as e:
        print(f"NLP Error: Could not parse model response. {e}")
        return "Error", "Error"
    except Exception as e:
        print(f"NLP Error: An issue occurred with Ollama. {e}")
        return "Error", "Error"

def analyze_image_for_landmarks(image_url):
    """
    Downloads an image and uses Ollama with LLaVA to identify landmarks.
    """
    if not image_url or image_url == "N/A":
        return "N/A"

    print(f"👁️ Analyzing image for landmarks: {image_url}")
    try:
        # Download the image from the URL
        image_response = requests.get(image_url, stream=True, timeout=10)
        image_response.raise_for_status()
        image_bytes = image_response.content

        # Analyze with LLaVA
        system_prompt = "Analyze this image. Identify any specific landmarks, famous buildings, or well-known locations visible. If none are found, respond with 'N/A'."
        
        response = ollama.generate(
            model="llava",
            prompt=system_prompt,
            images=[image_bytes],
            stream=False
        )
        landmark = response.get('response', 'N/A').strip()
        print(f"✅ Landmark detected: {landmark}")
        return landmark
    except requests.exceptions.RequestException as e:
        print(f"CV Error: Could not download image {image_url}. {e}")
        return "Image Download Failed"
    except Exception as e:
        print(f"CV Error: An issue occurred with Ollama/LLaVA. {e}")
        return "Analysis Error"

def create_headers(bearer_token):
    """Creates the necessary authorization headers for the API request."""
    headers = {"Authorization": f"Bearer {bearer_token}"}
    return headers

def connect_to_endpoint(url, headers, params):
    """Sends the API request and returns the JSON response."""
    response = requests.get(url, headers=headers, params=params)
    print(f"Endpoint Response Code: {response.status_code}")
    if response.status_code != 200:
        raise Exception(f"Request returned an error: {response.status_code} {response.text}")
    return response.json()

def main():
    """
    Main function to fetch tweets, process them, save to DB, and output a JSON array.
    """
    initialize_tweet_database()
    bearer_token = os.getenv("BEARER_TOKEN")
    if not bearer_token:
        raise Exception("Bearer token not found! Please set the BEARER_TOKEN environment variable.")

    search_url = "https://api.twitter.com/2/tweets/search/recent"
    
    query_params = {
        'query': 'disaster OR emergency OR flooding OR fire India -is:retweet',
        'max_results': 10,
        'expansions': 'author_id,attachments.media_keys',
        'tweet.fields': 'created_at,attachments',
        'media.fields': 'url'
    }

    headers = create_headers(bearer_token)
    json_response = connect_to_endpoint(search_url, headers, query_params)

    results_list = []

    if "data" in json_response:
        media_includes = json_response.get("includes", {}).get("media", [])
        media_map = {media["media_key"]: media.get("url") for media in media_includes}

        print("\n--- Analyzing Tweets ---")
        for tweet in json_response["data"]:
            tweet_text = tweet['text']
            location, disaster_type = extract_disaster_info(tweet_text)
            image_url = "N/A"
            detected_landmark = "N/A"
            
            if "attachments" in tweet and "media_keys" in tweet["attachments"]:
                for key in tweet["attachments"]["media_keys"]:
                    if key in media_map and media_map[key]:
                        image_url = media_map[key]
                        detected_landmark = analyze_image_for_landmarks(image_url)
                        break
            
            processed_tweet = {
                "author_id": tweet['author_id'],
                "timestamp": tweet['created_at'],
                "text": tweet_text,
                "extracted_location": location,
                "disaster_type": disaster_type,
                "image_url": image_url,
                "detected_landmark": detected_landmark
            }
            results_list.append(processed_tweet)
    else:
        print("No tweets found for the query.")

    if results_list:
        print("\n--- Saving to Database ---")
        save_tweets_to_db(results_list)

    print("\n--- Final JSON Output ---")
    print(json.dumps(results_list, indent=2))


if __name__ == "__main__":
    main()
import sqlite3
import sys
from datetime import datetime, timedelta

DB_FILE = "subscriptions.db"

def initialize_database():
    """Creates the database and necessary tables if they don't exist."""
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    # Subscriptions table with a unique constraint
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY,
            location TEXT NOT NULL,
            email TEXT NOT NULL,
            UNIQUE(location, email)
        )
    """)
    # New table to log sent alerts for de-duplication
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sent_alerts (
            id INTEGER PRIMARY KEY,
            location TEXT NOT NULL,
            disaster_type TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()
    print("✅ Database initialized successfully.")

def get_subscribers_for_locations(locations):
    """
    Fetches all subscribers for a list of locations in a single database query.
    Returns a dictionary mapping each location to a list of its subscribers.
    """
    if not locations:
        return {}
    
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    
    placeholders = ','.join('?' for location in locations)
    query = f"SELECT location, email FROM subscriptions WHERE location IN ({placeholders})"
    
    res = cur.execute(query, tuple(locations))
    
    subscribers_map = {loc: [] for loc in locations}
    for location, email in res.fetchall():
        subscribers_map[location].append(email)
        
    con.close()
    return subscribers_map

def check_if_alert_sent_recently(location, disaster_type, window_hours=6):
    """
    Checks if an alert for the same location and disaster was sent within the last 6 hours.
    """
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    
    time_window = datetime.now() - timedelta(hours=window_hours)
    
    res = cur.execute("""
        SELECT id FROM sent_alerts 
        WHERE location = ? AND disaster_type = ? AND sent_at > ?
        LIMIT 1
    """, (location, disaster_type, time_window))
    
    result = res.fetchone()
    con.close()
    return result is not None

def log_sent_alert(location, disaster_type):
    """Logs that an alert has been sent to the database."""
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("INSERT INTO sent_alerts (location, disaster_type) VALUES (?, ?)", (location, disaster_type))
    con.commit()
    con.close()

def add_subscription(location, email):
    """Adds a new user subscription to a location."""
    try:
        con = sqlite3.connect(DB_FILE)
        cur = con.cursor()
        cur.execute("INSERT INTO subscriptions (location, email) VALUES (?, ?)", (location.lower(), email))
        con.commit()
        print(f"✅ Added '{email}' to location '{location.lower()}'.")
    except sqlite3.IntegrityError:
        print(f"⚠️ User '{email}' is already subscribed to '{location.lower()}'.")
    finally:
        if con:
            con.close()

def remove_subscription(location, email):
    """Removes a user subscription."""
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    cur.execute("DELETE FROM subscriptions WHERE location = ? AND email = ?", (location.lower(), email))
    con.commit()
    if con.total_changes > 0:
        print(f"✅ Removed '{email}' from location '{location.lower()}'.")
    else:
        print(f"🤷 No subscription found for '{email}' in '{location.lower()}'.")
    con.close()

def list_subscriptions():
    """Lists all current subscriptions."""
    con = sqlite3.connect(DB_FILE)
    cur = con.cursor()
    res = cur.execute("SELECT location, email FROM subscriptions ORDER BY location")
    subscriptions = res.fetchall()
    con.close()
    if not subscriptions:
        print("No subscriptions found.")
        return
    print("--- Current Subscriptions ---")
    for location, email in subscriptions:
        print(f"- Location: {location}, User: {email}")

def main():
    """Main function to handle command-line arguments."""
    args = sys.argv[1:]
    if not args:
        print("Usage: python user_db.py <command> [options]")
        print("Commands: init, add, remove, list")
        return

    command = args[0]
    if command == "init":
        initialize_database()
    elif command == "add" and len(args) == 3:
        add_subscription(args[1], args[2])
    elif command == "remove" and len(args) == 3:
        remove_subscription(args[1], args[2])
    elif command == "list":
        list_subscriptions()
    else:
        print("Invalid command or arguments.")
        print("Usage: python user_db.py add <location> <email>")

if __name__ == "__main__":
    main()
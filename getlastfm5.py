import requests
from collections import defaultdict
import calendar
import time
import pandas as pd
import json
import os

# Your API key, username, filenames
API_KEY = 'your_api_key'
USER = 'username'
CSV_FILE = 'top_20_artists.csv'
CACHE_FILE = 'lastfm_cache.json'
CATEGORY_CACHE_FILE = 'artist_categories_cache.json'

# User-defined settings
AGGREGATION = "weekly"  # Choose "monthly" or "weekly"

# Define artist groupings (e.g., group multiple artist names under one label)
artist_groups = {
    "Peps": ["peps persson", "peps blodsband"],
    "bob marley & the wailers": ["bob marley", "the wailers"]
}

# Function to get the UNIX timestamp for the start and end of a month
def get_month_ranges(year, month):
    start_ts = int(time.mktime(time.strptime(f'{year}-{month:02d}-01', '%Y-%m-%d')))
    last_day = calendar.monthrange(year, month)[1]
    end_ts = int(time.mktime(time.strptime(f'{year}-{month:02d}-{last_day}', '%Y-%m-%d')))
    return [(start_ts, end_ts, f'{year}-{month:02d}-01')]

# Function to get the UNIX timestamp ranges for weeks in a month
def get_week_ranges(year, month):
    start_date = time.strptime(f'{year}-{month:02d}-01', '%Y-%m-%d')
    start_ts = int(time.mktime(start_date))
    last_day = calendar.monthrange(year, month)[1]
    end_date = time.strptime(f'{year}-{month:02d}-{last_day}', '%Y-%m-%d')
    end_ts = int(time.mktime(end_date))
    
    week_ranges = []
    current_ts = start_ts
    while current_ts < end_ts:
        next_ts = current_ts + 7 * 24 * 60 * 60  # Add 7 days
        next_ts = min(next_ts, end_ts)  # Ensure we don't exceed the month's end
        week_ranges.append((current_ts, next_ts, time.strftime('%Y-%m-%d', time.localtime(current_ts))))
        current_ts = next_ts
    return week_ranges

# Function to fetch tracks for a given month
def fetch_recent_tracks(from_ts, to_ts, page=1):

    from_date = time.strftime('%Y-%m-%d', time.localtime(start_ts))
    to_date = time.strftime('%Y-%m-%d', time.localtime(end_ts))
    print(f"Fetching data for range: From {from_date} to {to_date}")

    url = f"http://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks&user={USER}&from={from_ts}&to={to_ts}&limit=200&page={page}&api_key={API_KEY}&format=json"
    response = requests.get(url)
    return response.json()

# Function to get the UNIX timestamp for the start and end of a month
def get_month_timestamp(year, month):
    start_ts = int(time.mktime(time.strptime(f'{year}-{month:02d}-01', '%Y-%m-%d')))
    last_day = calendar.monthrange(year, month)[1]
    end_ts = int(time.mktime(time.strptime(f'{year}-{month:02d}-{last_day}', '%Y-%m-%d')))
    return start_ts, end_ts

# Function to map artist names to their grouped name
def map_artist_name(artist_name):
    for group_name, aliases in artist_groups.items():
        if artist_name.lower() in [alias.lower() for alias in aliases]:
            return group_name
    return artist_name  # Return the original name if no mapping exists

# Load cache data from file
def load_cache(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

# Save cache data to file
def save_cache(file_path, cache):
    with open(file_path, 'w') as f:
        json.dump(cache, f)

# Fetch the top tag for an artist from Last.fm (for category)
def fetch_artist_top_tag(artist_name):
    url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getTopTags&artist={artist_name}&api_key={API_KEY}&format=json"
    response = requests.get(url)
    data = response.json()
    if 'toptags' in data and 'tag' in data['toptags']:
        # Return the top tag name if available
        return data['toptags']['tag'][0]['name'] if data['toptags']['tag'] else "unknown"
    return "unknown"

# Function to get the category (top tag) for an artist, with caching
def get_artist_category(artist_name, category_cache):
    if artist_name in category_cache:
        return category_cache[artist_name]  # Return cached category
    else:
        # Fetch category from Last.fm
        top_tag = fetch_artist_top_tag(artist_name)
        category_cache[artist_name] = top_tag  # Cache the category
        save_cache(CATEGORY_CACHE_FILE, category_cache)  # Save updated cache
        return top_tag

# Set start year and month here, e.g.
#start_year = 2007
#start_month = 5
start_year = 2025
start_month = 1
end_year = time.localtime().tm_year
end_month = time.localtime().tm_mon

# Load cached data
cache = load_cache(CACHE_FILE)
category_cache = load_cache(CATEGORY_CACHE_FILE)  # Load category cache

# Dictionary to store cumulative artist play counts
cumulative_artist_freq = defaultdict(int)

# List to store data for CSV
csv_data = []

# Main loop over years and months
for year in range(start_year, end_year + 1):
    for month in range(1, 13):
        # Break if we go past the current month in the current year
        if year == end_year and month > end_month:
            break

        # Skip months before May 2007
        if year == 2007 and month < start_month:
            continue

        # Get the time ranges based on aggregation type
        if AGGREGATION == "monthly":
            ranges = get_month_ranges(year, month)
        elif AGGREGATION == "weekly":
            ranges = get_week_ranges(year, month)
        else:
            raise ValueError("Invalid aggregation type. Choose 'monthly' or 'weekly'.")

        for start_ts, end_ts, date_label in ranges:
            cache_key = date_label
            if cache_key in cache:
                print(f"Using cached data for {date_label}")
                artist_freq = cache[cache_key]
            else:
                print(f"Fetching data for {date_label} from Last.fm")
                # Pagination logic remains the same
                page = 1
                total_pages = 1
                artist_freq = defaultdict(int)
                while page <= total_pages:
                    data = fetch_recent_tracks(start_ts, end_ts, page)
                    tracks = data.get('recenttracks', {}).get('track', [])
                    
                    # Count artist frequencies
                    for track in tracks:
                        artist_name = track['artist']['#text']
                        mapped_artist_name = map_artist_name(artist_name)
                        artist_freq[mapped_artist_name] += 1
                    
                    # Update total pages
                    if 'recenttracks' in data and '@attr' in data['recenttracks']:
                        total_pages = int(data['recenttracks']['@attr']['totalPages'])
                    
                    page += 1
                
                # Update cache
                cache[cache_key] = artist_freq
                save_cache(CACHE_FILE, cache)

            # Add to cumulative data
            for artist, count in artist_freq.items():
                cumulative_artist_freq[artist] += count

            # Sort and get the top 20
            sorted_artists = sorted(cumulative_artist_freq.items(), key=lambda x: x[1], reverse=True)
            top_20 = sorted_artists[:20]

            # Print top 5 for this period
            print(f"Top 5 artists for {date_label}:")
            for artist, count in sorted_artists[:5]:
                print(f"{artist}: {count} plays")

            # Add top 20 to CSV data
            for artist, count in top_20:
                category = get_artist_category(artist, category_cache)  # Fetch category
                csv_data.append([date_label, artist, category, count])

# Create a DataFrame for the CSV
#df = pd.DataFrame(csv_data, columns=['date', 'artist', 'category', 'frequency'])
df = pd.DataFrame(csv_data, columns=['date', 'name', 'category', 'value'])

# Save to CSV
df.to_csv(CSV_FILE, index=False)

print(f"\nTop 20 artist data has been saved to {CSV_FILE}.")



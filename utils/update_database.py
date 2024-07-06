from spotify import create_spotify_client, fetch_top_data
from sqlalchemy import create_engine
import datetime
import os
import pandas as pd

#spotify = spotipy.Spotify(
#    client_credentials_manager=SpotifyClientCredentials(
#        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
#        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
#    )
#)

# Initialize the Spotify client
spotify = create_spotify_client()

# Get the top artists and tracks for the current user using an artist genre mapping
top_artists_list, top_tracks_list = fetch_top_data(spotify)

# Get the current datetime in ISO format
current_timestamp = datetime.datetime.now().isoformat()

# Add the timestamp to each dictionary
for artist_dict in top_artists_list:
    artist_dict["timestamp"] = current_timestamp

for track_dict in top_tracks_list:
    track_dict["timestamp"] = current_timestamp

# Save the lists to the database
db = create_engine(f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@127.0.0.1:5432/spotify")
pd.DataFrame(top_artists_list).to_sql("top_artists", db, if_exists="append", index=False)
pd.DataFrame(top_tracks_list).to_sql("top_tracks", db, if_exists="append", index=False)
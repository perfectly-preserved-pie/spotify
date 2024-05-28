from loguru import logger
from spotify import create_spotify_client, get_playlists, fetch_top_data, generate_embed_html
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

# Get the playlists for the current user
playlists = get_playlists(spotify)

# Loop through the playlists and create a dictionary of playlist names and ids
playlist_dict = {}
for playlist in playlists["items"]:
    if playlist["owner"]["id"] == "1244365996":
        playlist_dict[playlist["name"]] = playlist["id"]

# Constants
LIMIT = 100  # Maximum number of tracks to retrieve per API call

# Initialize an empty list to hold all track dictionaries for all playlists
tracks_list = []

# Go through each playlist and get each playlist's ID
logger.info("Getting tracks from each playlist")
for playlist_name, playlist_id in playlist_dict.items():
    # Initialize an offset
    offset = 0
    # Continuously fetch tracks until no more are available
    while True:
        # Get playlist tracks
        try:
            playlist_items = spotify.playlist_items(
                playlist_id=playlist_id,
                limit=LIMIT,
                offset=offset
            )
        except Exception as e:
            logger.error(f"Could not get tracks from {playlist_name} with offset {offset} because {e}")
            break
        # Check if there are no more tracks to fetch
        if not playlist_items["items"]:
            break
        # Loop through each track in the playlist
        logger.info(f"Getting tracks from {playlist_name} with offset {offset}")
        for track in playlist_items["items"]:
            # Initialize an empty dictionary for each track
            track_dict = {}
            # Fill the dictionary with the track's information
            # https://developer.spotify.com/documentation/web-api/reference/get-playlists-tracks
            track_dict["name"] = track["track"]["name"]
            track_dict["artist"] = track["track"]["artists"][0]["name"]
            artist_id = track["track"]["artists"][0].get("id")
            # If the artist ID exists, get the artist's genre(s)
            if artist_id:
                track_dict["artist_id"] = artist_id
                try:
                    artist_info = spotify.artist(artist_id=artist_id)
                    track_dict["artist_genre"] = artist_info.get("genres", [])
                    images = artist_info.get("images", [{}]*3)
                    track_dict["artist_images_large"] = images[0].get("url", None)
                    track_dict["artist_images_medium"] = images[1].get("url", None)
                    track_dict["artist_images_small"] = images[2].get("url", None)
                except Exception as e:
                    logger.error(f"Error fetching artist info for artist_id: {artist_id}. Error: {e}")
                    track_dict["artist_genre"] = []
                    track_dict["artist_images_large"] = None
                    track_dict["artist_images_medium"] = None
                    track_dict["artist_images_small"] = None
            else:
                track_dict["artist_id"] = None
                track_dict["artist_genre"] = []
                track_dict["artist_images_large"] = None
                track_dict["artist_images_medium"] = None
                track_dict["artist_images_small"] = None
                logger.warning(f"No artist_id found for track {track_dict['name']}. Skipping artist info fetch.")
            track_dict["explicit"] = track["track"]["explicit"]
            track_dict["popularity"] = track["track"]["popularity"]
            track_dict["duration_ms"] = track["track"]["duration_ms"]
            track_dict["preview_url"] = track["track"]["preview_url"]
            track_dict["album"] = track["track"]["album"]["name"]
            track_dict["id"] = track["track"]["id"]
            track_dict["added_at"] = track["added_at"]
            track_dict["uri"] = track["track"]["uri"]
            track_dict["embed_html"] = generate_embed_html(track_dict["uri"])[0]
            track_dict["embed_thumbnail_url"] = generate_embed_html(track_dict["uri"])[1]
            track_dict["playlist_name"] = playlist_name
            logger.success(f"Successfully got track {track_dict['name']} info from {playlist_name}.")
            # Append the track dictionary to the tracks list
            tracks_list.append(track_dict)
        # Increment the offset by the limit for the next iteration
        offset += LIMIT

# Get the top artists and tracks for the current user using an artist genre mapping
top_artists_list, top_tracks_list = fetch_top_data(spotify)

# Get the current datetime in ISO format
current_timestamp = datetime.datetime.now().isoformat()

# Add the timestamp to each dictionary
for track_dict in tracks_list:
    track_dict["timestamp"] = current_timestamp

for artist_dict in top_artists_list:
    artist_dict["timestamp"] = current_timestamp

for track_dict in top_tracks_list:
    track_dict["timestamp"] = current_timestamp

# Save the lists to the database
db = create_engine(f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@127.0.0.1:5432/spotify")
pd.DataFrame(tracks_list).to_sql("all_tracks", db, if_exists="append", index=False)
pd.DataFrame(top_artists_list).to_sql("top_artists", db, if_exists="append", index=False)
pd.DataFrame(top_tracks_list).to_sql("top_tracks", db, if_exists="append", index=False)
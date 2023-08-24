from dotenv import load_dotenv, find_dotenv
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from loguru import logger
import os
import pandas as pd
import spotipy

load_dotenv(find_dotenv())

spotify = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        scope=["playlist-read-private"],
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri="http://localhost",
    )
)

#spotify = spotipy.Spotify(
#    client_credentials_manager=SpotifyClientCredentials(
#        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
#        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
#    )
#)


# Get a list of all my playlists
try:
    playlists = spotify.current_user_playlists()
    logger.success("Successfully got playlists from Spotify API")
except:
    logger.error("Could not get playlists from Spotify API")

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
            # Get the track's name
            track_dict["name"] = track["track"]["name"]
            # Get the track's artist
            track_dict["artist"] = track["track"]["artists"][0]["name"]
            # Get the track's artist ID
            artist_id = track["track"]["artists"][0].get("id")
            if artist_id:
                track_dict["artist_id"] = artist_id
                # Try fetching the artist's genre(s)
                try:
                    track_dict["artist_genre"] = spotify.artist(artist_id=artist_id)["genres"]
                except Exception as e:
                    logger.error(f"Error fetching genres for artist_id: {artist_id}. Error: {e}")
                    track_dict["artist_genre"] = []
            else:
                track_dict["artist_id"] = None
                track_dict["artist_genre"] = []
                logger.warning(f"No artist_id found for track {track_dict['name']}. Skipping genre fetch.")
            # Get the track's album
            track_dict["album"] = track["track"]["album"]["name"]
            # Get the track's ID
            track_dict["id"] = track["track"]["id"]
            # Get the track's added_at date
            track_dict["added_at"] = track["added_at"]
            # Get the track's URI
            track_dict["uri"] = track["track"]["uri"]
            # Get the track's playlist name
            track_dict["playlist_name"] = playlist_name
            logger.success(f"Successfully got track {track_dict['name']} info from {playlist_name}.")
            # Append the track dictionary to the tracks list
            tracks_list.append(track_dict)
        # Increment the offset by the limit for the next iteration
        offset += LIMIT

# Now stuff the tracks list into a dataframe
df = pd.DataFrame(tracks_list)
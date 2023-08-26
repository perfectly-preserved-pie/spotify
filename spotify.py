from dotenv import load_dotenv, find_dotenv
from loguru import logger
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import os
import pandas as pd
import spotipy

load_dotenv(find_dotenv())

spotify = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        scope=["playlist-read-private", "user-top-read"], # https://developer.spotify.com/documentation/web-api/concepts/scopes
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
            track_dict["playlist_name"] = playlist_name
            logger.success(f"Successfully got track {track_dict['name']} info from {playlist_name}.")
            # Append the track dictionary to the tracks list
            tracks_list.append(track_dict)
        # Increment the offset by the limit for the next iteration
        offset += LIMIT

# Create a function to process the artist data when we get the top artists
# https://developer.spotify.com/documentation/web-api/reference/get-users-top-artists-and-tracks
def process_artists(artists, time_range):
    artist_list = []
    for artist in artists:
        artist_dict = {
            "name": artist["name"],
            "id": artist["id"],
            "genres": artist["genres"],
            "time_range": time_range
        }
        images = artist.get("images", [{}]*3)
        artist_dict["images_large"] = images[0].get("url")
        artist_dict["images_medium"] = images[1].get("url")
        artist_dict["images_small"] = images[2].get("url")
        artist_list.append(artist_dict)
    return artist_list

# Time ranges to check
time_ranges = ["long_term", "medium_term", "short_term"]

top_artists_list = []

for time_range in time_ranges:
    artists = spotify.current_user_top_artists(limit=5, time_range=time_range)["items"]
    top_artists_list.extend(process_artists(artists, time_range))

# Now stuff the tracks list into a dataframe
df_tracks = pd.DataFrame(tracks_list)

# Now stuff the top artists list into a dataframe
df_top_artists = pd.DataFrame(top_artists_list)
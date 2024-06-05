from dotenv import load_dotenv, find_dotenv
from loguru import logger
from spotipy import Spotify, SpotifyOAuth, SpotifyException
from typing import Tuple, Any, List, Dict
import json
import os
import requests
import urllib.parse

load_dotenv(find_dotenv())

def create_spotify_client() -> Spotify:
    """
    Create a Spotify client with OAuth2 authentication.

    This function creates a Spotify client with OAuth2 authentication using the client ID and client secret from the environment variables.

    Returns:
        Spotify: The Spotify client.
    """
    try:
        spotify = Spotify(
            auth_manager=SpotifyOAuth(
                scope=["playlist-read-private", "user-top-read"], # https://developer.spotify.com/documentation/web-api/concepts/scopes
                client_id=os.getenv("SPOTIFY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
                redirect_uri="http://localhost:8080",
            )
        )
        return spotify
    except SpotifyException as e:
        logger.error(f"Could not create Spotify client. Error: {e}")
        return None

# Create a function to generate embed HTML for a given Spotify URI
# https://developer.spotify.com/documentation/embeds/reference/oembed
def generate_embed_html(uri: str) -> Tuple[str, str]:
    """
    Generate embed HTML for a given Spotify URI.

    This function sends a GET request to the Spotify oEmbed API and returns the HTML and thumbnail URL from the response.

    See https://developer.spotify.com/documentation/embeds/reference/oembed

    Args:
        uri (str): The Spotify URI to generate embed HTML for.

    Returns:
        Tuple[str, str]: A tuple containing the embed HTML and the thumbnail URL.
    """
    # Construct the URL for the oEmbed request
    encoded_uri = urllib.parse.quote(uri, safe='')
    api_url = f'https://open.spotify.com/oembed?url={encoded_uri}'
    
    # Make the request to the oEmbed API
    response = requests.get(api_url)
    
    if response.status_code == 200:
        try:
            # Parse the response JSON
            response_json = response.json()
            html = response_json.get("html", "")
            thumbnail_url = response_json.get("thumbnail_url", "")
            
            logger.success(f"Successfully generated embed HTML for URI {uri}")
            return html, thumbnail_url
        except json.decoder.JSONDecodeError as e:
            logger.error(f"Invalid JSON response for URI {uri}: {e}")
            return None, None
    else:
        logger.error(f"Request to Spotify oEmbed API failed with status code {response.status_code}")
        return None, None


def get_genre_for_artist(spotify: Spotify, artist_id: str) -> List[str]:
    """
    Fetch genres for a given artist ID.

    This function uses the Spotify Web API to fetch the artist data for a given artist ID, and then returns the genres associated with that artist.

    Args:
        spotify (Spotify): The Spotify Web API client.
        artist_id (str): The Spotify ID of the artist.

    Returns:
        List[str]: A list of genres associated with the artist.
    """
    artist_data = spotify.artist(artist_id)
    genres = artist_data.get("genres", [])
    if not genres:
        logger.warning(f"No genres found for artist ID: {artist_id}, Artist Name: {artist_data.get('name')}")
    logger.success(f"Successfully fetched genres {genres} for artist ID: {artist_id}, Artist Name: {artist_data.get('name')}")
    return genres


def fetch_top_artists(spotify: Spotify, time_ranges: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch the top artists for the current user for each time range.

    This function uses the Spotify Web API to fetch the top artists for the current user for each time range, and then returns a list of dictionaries containing information about each artist.

    Args:
        spotify (Spotify): The Spotify Web API client.
        time_ranges (List[str]): A list of time ranges to fetch the top artists for.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each containing information about an artist.
    """
    top_artists_list = []
    for time_range in time_ranges:
        artists = spotify.current_user_top_artists(limit=150, time_range=time_range)["items"]
        for index, artist in enumerate(artists):
            artist_dict = {
                "name": artist["name"],
                "id": artist["id"],
                "genres": artist["genres"],
                "time_range": time_range,
                "rank": index + 1  # Rank of the artist in the list
            }
            top_artists_list.append(artist_dict)
    return top_artists_list

def fetch_top_tracks(spotify: Spotify, time_ranges: List[str], artist_genre_mapping: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Fetch the top tracks for the current user for each time range.

    This function uses the Spotify Web API to fetch the top tracks for the current user for each time range, and then returns a list of dictionaries containing information about each track.

    Args:
        spotify (Spotify): The Spotify Web API client.
        time_ranges (List[str]): A list of time ranges to fetch the top tracks for.
        artist_genre_mapping (Dict[str, List[str]]): A mapping from artist IDs to genres.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each containing information about a track.
    """
    top_tracks_list = []
    for time_range in time_ranges:
        tracks = spotify.current_user_top_tracks(limit=150, time_range=time_range)["items"]
        for index, track in enumerate(tracks):
            track_dict = {
                "name": track["name"],
                "artist": ", ".join([artist["name"] for artist in track["artists"]]),
                "id": track["id"],
                "explicit": track["explicit"],
                "preview_url": track["preview_url"],
                "time_range": time_range,
                "rank": index + 1  # Rank of the track in the list
            }
            # Using the mapping to get genres of the artist associated with this track
            # If the artist ID is not in the mapping, fetch the genres from the API
            first_artist_id = track["artists"][0]["id"]
            if first_artist_id not in artist_genre_mapping:
                artist_genre_mapping[first_artist_id] = get_genre_for_artist(spotify, first_artist_id)
            track_dict["genres"] = artist_genre_mapping[first_artist_id]
            images = track["album"].get("images", [{}]*3)
            track_dict["images_large"] = images[0].get("url")
            track_dict["images_medium"] = images[1].get("url")
            track_dict["images_small"] = images[2].get("url")
            # Get the embed HTML and thumbnail URL
            embed_html, embed_thumbnail_url = generate_embed_html(track["uri"])
            track_dict["embed_html"] = embed_html
            track_dict["embed_thumbnail_url"] = embed_thumbnail_url
            top_tracks_list.append(track_dict)

    logger.success(f"Successfully fetched top tracks for {len(top_tracks_list)} tracks.")
    return top_tracks_list

def fetch_top_data(spotify: Spotify) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Fetch top artists and tracks for the current user.

    This function uses the Spotify API to fetch the top artists and tracks for the current user for each time range, and then returns a tuple containing a list of dictionaries with information about each artist and track.

    Args:
        spotify (Spotify): The Spotify client.

    Returns:
        Tuple[List[Dict[str, str]], List[Dict[str, str]]]: A tuple containing a list of dictionaries with information about each artist and track.
    """
    time_ranges = ["long_term", "medium_term", "short_term"]
    top_artists_list = fetch_top_artists(spotify, time_ranges)
    artist_genre_mapping = {artist['id']: artist['genres'] for artist in top_artists_list}
    top_tracks_list = fetch_top_tracks(spotify, time_ranges, artist_genre_mapping)
    return top_artists_list, top_tracks_list
from dash import Dash, dcc, html
from dash_ag_grid import AgGrid
from dash.dependencies import Input, Output
from dotenv import load_dotenv, find_dotenv
from pandas import DataFrame
from sqlalchemy import create_engine
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import datetime
import os
import pandas as pd

load_dotenv(find_dotenv())

# Connect to the Postgres database using a SQLAlchemy engine
db = create_engine(f'postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@127.0.0.1:5432/spotify')

# Load the data
df_artists = pd.read_sql_query("SELECT * FROM top_artists", db)
df_tracks = pd.read_sql_query("SELECT * FROM top_tracks", db)

# Function to create top artists grid
def create_top_artists_grid(time_range: str) -> AgGrid:
    """
    Creates a grid of top artists for a given time range.

    Parameters:
    time_range (str): The time range for which to create the grid. This should match a value in the "time_range" column of df_artists.

    Returns:
    AgGrid: A Dash AgGrid component containing the top artists for the given time range.
    """
    df: DataFrame = df_artists[df_artists["time_range"] == time_range]
    return dag.AgGrid(
        id="top-artists-ag-grid",
        columnDefs=[
            #{"headerName": "", "field": "images_small", "sortable": False, "filter": False, "cellRenderer": "ImgThumbnail"},
            {"headerName": "Rank", "field": "rank", "sortable": True, "resizable": True,"sort": "asc", "width": 10, "maxWidth": 95},
            {"headerName": "Artist", "field": "name", "sortable": True, "resizable": True, "filter": True, "cellRenderer": "ArtistOrTrackWithThumbnail"},
            {"headerName": "Genres", "field": "genres", "sortable": True, "resizable": True, "filter": True},
        ],
        columnSize="responsiveSizeToFit",
        rowData=df.to_dict("records"),
        className="ag-theme-alpine-dark",
    )

# Function to create top tracks grid
def create_top_tracks_grid(time_range: str) -> AgGrid:
    """
    Creates a grid of top tracks for a given time range.

    Parameters:
    time_range (str): The time range for which to create the grid. This should match a value in the "time_range" column of df_tracks.

    Returns:
    AgGrid: A Dash AgGrid component containing the top tracks for the given time range.
    """
    df: DataFrame = df_tracks[df_tracks["time_range"] == time_range]
    return dag.AgGrid(
        id="top-tracks-ag-grid",
        defaultColDef={"sortable": True, "resizable": True},
        columnDefs=[
            #{"headerName": "", "field": "images_large", "sortable": False, "filter": False, "cellRenderer": "ImgThumbnail"},
            {"headerName": "Rank", "field": "rank", "sort": "asc"}, 
            {"headerName": "Track", "field": "name", "cellRenderer": "ArtistOrTrackWithThumbnail"},
            {"headerName": "Artist", "field": "artist"},
            {"headerName": "Album", "field": "album"},
            {"headerName": "Genres", "field": "genres"},
            #{"headerName": "Preview URL", "field": "preview_url", "sortable": False, "resizable": True, "filter": False, "cellRenderer": "linkCellRenderer"},
        ],
        columnSize="autoSize",
        rowData=df.to_dict("records"),
        className="ag-theme-alpine-dark",
    )

# Create the app
external_stylesheets = [dbc.themes.DARKLY, dbc.icons.BOOTSTRAP, dbc.icons.FONT_AWESOME, "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css"]
app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    meta_tags = [
      {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
)

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("My Spotify Top Artists and Tracks", className="text-center"),
            html.Hr(),
            html.P("Select a time range to view my top artists and tracks for that time period.", className="text-center"),
            dcc.Dropdown(
                id="time-range-dropdown",
                options=[
                    {"label": "All Time", "value": "long_term"},
                    {"label": "Last 6 Months", "value": "medium_term"},
                    {"label": "Last 4 Weeks", "value": "short_term"},
                    {"label": "Custom Range", "value": "custom"}
                ],
                value="long_term",
                clearable=False,
                className="text-center ag-theme-alpine-dark"
            ),
            dcc.DatePickerRange(
                id='date-range-picker',
                start_date_placeholder_text="Start Period",
                end_date_placeholder_text="End Period",
                display_format='YYYY-MM-DD',
                style={'display': 'none'}  # initially hidden
            ),
            html.Hr(),
            # Create a title for the top artists grid
            html.H2("Top Artists", className="text-center"),
            html.Div(id="top-artists-grid", children=create_top_artists_grid("long_term")),
            html.Hr(),
            # Create a title for the top tracks grid
            html.H2("Top Tracks", className="text-center"),
            html.Div(id="top-tracks-grid", children=create_top_tracks_grid("long_term"))
        ], width=12)
    ])
])

# Callbacks
@app.callback(
    Output("top-artists-grid", "children"),
    Input("time-range-dropdown", "value")
)
def update_top_artists_grid(time_range):
    return create_top_artists_grid(time_range)

@app.callback(
    Output("top-tracks-grid", "children"),
    Input("time-range-dropdown", "value")
)
def update_top_tracks_grid(time_range):
    return create_top_tracks_grid(time_range)

@app.callback(
    Output("date-range-picker", "style"),
    [Input("time-range-dropdown", "value")]
)
def show_date_picker(value):
    if value == "custom":
        return {}  # show date picker
    else:
        return {'display': 'none'}  # hide date picker

@app.callback(
    [
        Output('top-artists-ag-grid', 'rowData'),
        Output('top-tracks-ag-grid', 'rowData')
    ],
    [Input('time-range-dropdown', 'value')]
)
def update_grids(selected_time_range):
    # Get the current datetime
    now = datetime.datetime.now()

    # Calculate the start date based on the selected time range
    if selected_time_range == 'long_term':
        start_date = '2000-01-01T00:00:00'  # A date far in the past to get all songs
    elif selected_time_range == 'medium_term':
        start_date = (now - datetime.timedelta(days=6*30)).isoformat()  # Last 6 months
    elif selected_time_range == 'short_term':
        start_date = (now - datetime.timedelta(days=4*7)).isoformat()  # Last 4 weeks
    else:
        start_date = '2000-01-01T00:00:00'  # Default to all songs if the time range is not recognized

    # Query the database for the top artists and songs based on the start date and selected time range
    songs_query = f"""
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY id ORDER BY timestamp DESC) AS rn
        FROM top_tracks
        WHERE timestamp::text >= '{start_date}' AND time_range = '{selected_time_range}'
    ) AS ranked_tracks WHERE rn = 1;
    """
    artists_query = f"""
    SELECT * FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY id ORDER BY timestamp DESC) AS rn
        FROM top_artists
        WHERE timestamp::text >= '{start_date}' AND time_range = '{selected_time_range}'
    ) AS ranked_artists WHERE rn = 1;
    """

    songs = pd.read_sql(songs_query, db)
    artists = pd.read_sql(artists_query, db)

    # Convert the DataFrames to lists of dictionaries and return them
    return artists.to_dict('records'), songs.to_dict('records')

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
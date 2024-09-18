from dash import Dash, dcc, html, no_update, ctx
from dash_ag_grid import AgGrid
from dash.dependencies import Input, Output, State
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

# Default column definitions for the AgGrid components
default_column_definitions = {
    "sortable": True, 
    "resizable": True
}

# Function to create top artists grid
def create_top_artists_grid() -> AgGrid:
    return dag.AgGrid(
        id="top-artists-ag-grid",
        defaultColDef=default_column_definitions,
        columnDefs=[
            {"headerName": "Rank", "field": "rank", "sort": "asc", "width": 10, "maxWidth": 95},
            {"headerName": "Artist", "field": "name", "filter": True, "cellRenderer": "ArtistOrTrackWithThumbnail"},
            {"headerName": "Genres", "field": "genres", "filter": True},
        ],
        columnSize="responsiveSizeToFit",
        rowData=[],  # Start with an empty grid
        className="ag-theme-alpine-dark",
        dashGridOptions={"rowSelection": "single"},
    )

# Function to create top tracks grid
def create_top_tracks_grid() -> AgGrid:
    return dag.AgGrid(
        id="top-tracks-ag-grid",
        defaultColDef=default_column_definitions,
        columnDefs=[
            {"headerName": "Rank", "field": "rank", "sort": "asc", "width": 10, "maxWidth": 25}, 
            {"headerName": "Track", "field": "name", "cellRenderer": "ArtistOrTrackWithThumbnail"},
            {"headerName": "Artist", "field": "artist"},
            {"headerName": "Album", "field": "album"},
            {"headerName": "Genres", "field": "genres"},
        ],
        columnSize="responsiveSizeToFit",
        rowData=[],  # Start with an empty grid
        className="ag-theme-alpine-dark",
        dashGridOptions={"rowSelection": "single"},
    )

# Create the app
external_stylesheets = [dbc.themes.DARKLY, dbc.icons.BOOTSTRAP, dbc.icons.FONT_AWESOME, "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css"]
app = Dash(
    __name__,
    external_stylesheets=external_stylesheets,
    meta_tags = [
      {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
    suppress_callback_exceptions=True
)

# App layout
app.layout = html.Div([
    html.H1("My Spotify Top Artists and Tracks", className="text-center"),
    html.Hr(),
    html.P("Select a time range to view my top artists and tracks for that time period.", className="text-center"),
    dcc.Dropdown(
        id='time-range-dropdown',
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
    html.H3("Top Artists"),
    create_top_artists_grid(),  # Add the grid directly to layout
    html.H3("Top Tracks"),
    create_top_tracks_grid(),  # Add the grid directly to layout
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Row Data")),
            dbc.ModalBody(id="modal-body"),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-modal", className="ms-auto", n_clicks=0)
            ),
        ],
        id="row-data-modal",
        is_open=False,
    ),
])

# Callbacks
@app.callback(
    Output("top-artists-ag-grid", "rowData"),
    Output("top-tracks-ag-grid", "rowData"),
    Input("time-range-dropdown", "value")
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

# Callback to show/hide date picker based on dropdown value
@app.callback(
    Output("date-range-picker", "style"),
    [Input("time-range-dropdown", "value")]
)
def toggle_date_picker(selected_value):
    if selected_value == "custom":
        return {'display': 'block'}  # Show the date picker
    else:
        return {'display': 'none'}  # Hide the date picker

# Add a callback to handle row clicks and update the modal
@app.callback(
    [Output("row-data-modal", "is_open"), Output("modal-body", "children")],
    [Input("top-artists-ag-grid", "selectedRows"), Input("top-tracks-ag-grid", "selectedRows"), Input("close-modal", "n_clicks")],
    [State("row-data-modal", "is_open")]
)
def display_row_data(selected_artists_rows, selected_tracks_rows, n_clicks, is_open):
    if ctx.triggered_id == "close-modal":
        return False, no_update
    if selected_artists_rows:
        row_data = selected_artists_rows[0]  # Assuming single row selection
        genres = row_data.get("genres", [])
        genres_list = html.Ul([html.Li(genre) for genre in genres])
        return True, genres_list
    elif selected_tracks_rows:
        row_data = selected_tracks_rows[0]  # Assuming single row selection
        genres = row_data.get("genres", [])
        genres_list = html.Ul([html.Li(genre) for genre in genres])
        return True, genres_list
    return no_update, no_update

if __name__ == "__main__":
    app.run_server(debug=True)

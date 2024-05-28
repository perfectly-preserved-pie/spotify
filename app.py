from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from dotenv import load_dotenv, find_dotenv
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

# Function to create initial top artists grid
def initial_top_artists_grid(time_range):
    df = df_artists[df_artists["time_range"] == time_range]
    return dag.AgGrid(
        id="top-artists-ag-grid",
        columnDefs=[
            #{"headerName": "", "field": "images_small", "sortable": False, "filter": False, "cellRenderer": "ImgThumbnail"},
            {"headerName": "Artist", "field": "name", "sortable": True, "filter": True, "cellRenderer": "ArtistOrTrackWithThumbnail"},
            {"headerName": "Genres", "field": "genres", "sortable": True, "filter": True},
        ],
        rowData=df.to_dict("records"),
        className="ag-theme-alpine-dark",
    )

# Function to create top tracks grid
def create_top_tracks_grid(time_range):
    df = df_tracks[df_tracks["time_range"] == time_range]
    return dag.AgGrid(
        id="top-tracks-ag-grid",
        columnDefs=[
            #{"headerName": "", "field": "images_large", "sortable": False, "filter": False, "cellRenderer": "ImgThumbnail"},
            {"headerName": "Track", "field": "name", "sortable": True, "filter": True, "cellRenderer": "ArtistOrTrackWithThumbnail"},
            {"headerName": "Artist", "field": "artist", "sortable": True, "filter": True},
            {"headerName": "Genres", "field": "genres", "sortable": True, "filter": True},
            {"headerName": "Preview URL", "field": "preview_url", "sortable": False, "filter": False, "cellRenderer": "linkCellRenderer"},
        ],
        rowData=df.to_dict("records"),
        className="ag-theme-alpine-dark",
    )

# Create the app
external_stylesheets = [dbc.themes.DARKLY, dbc.icons.BOOTSTRAP, dbc.icons.FONT_AWESOME, "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css"]
app = Dash(__name__, external_stylesheets=external_stylesheets)

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
            html.Div(id="top-artists-grid", children=initial_top_artists_grid(default_time_range)),
            html.Hr(),
            # Create a title for the top tracks grid
            html.H2("Top Tracks", className="text-center"),
            html.Div(id="top-tracks-grid", children=create_top_tracks_grid(default_time_range))
        ], width=12)
    ])
])

# Callbacks
@app.callback(
    Output("top-artists-grid", "children"),
    Input("time-range-dropdown", "value")
)
def update_top_artists_grid(time_range):
    return initial_top_artists_grid(time_range)

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

    # Query the database for the top artists and songs based on the start date
    songs = pd.read_sql(f"SELECT * FROM top_tracks WHERE timestamp::text >= '{start_date}'", db)
    artists = pd.read_sql(f"SELECT * FROM top_artists WHERE timestamp::text >= '{start_date}'", db)

    # Convert the DataFrames to lists of dictionaries and return them
    return artists.to_dict('records'), songs.to_dict('records')

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
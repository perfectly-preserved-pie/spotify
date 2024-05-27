from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import pandas as pd

# Load the data
df_artists = pd.read_parquet("datasets/top_artists.parquet")
df_tracks = pd.read_parquet("datasets/top_tracks.parquet")

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

# Initial default values
default_time_range = "long_term"

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
                value=default_time_range,
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

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)

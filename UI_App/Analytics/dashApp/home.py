from dash import Dash, html, dcc, Input, Output, State, dash_table, callback_context
import dash
from .attendance import get_attendance_layout, register_attendance_callbacks
from .marks import get_marks_layout, register_marks_callbacks
import dash_bootstrap_components as dbc
import base64

# Initialize Dash App
app = Dash(
    __name__, 
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    ],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

app.title = "Student Analytics Dashboard"

# Custom CSS styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            * {
                font-family: 'Inter', sans-serif;
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                background: #f8fafc;
                color: #334155;
            }
        </style>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght=300;400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Main Layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content', style={'minHeight': '100vh'}),
    
    # Global download component (for both modules)
    dcc.Download(id="global-download-data"),
    
    # Store for attendance data
    dcc.Store(id='attendance-upload-store'),
    
    # Store for marks data  
    dcc.Store(id='marks-upload-store'),
])

# Router
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/attendance':
        return get_attendance_layout()
    elif pathname == '/marks':
        return get_marks_layout()
    else:
        return html.Div([
            html.Div([
                html.H1("📊 Analytics Dashboard", 
                       style={'fontSize': '36px', 'fontWeight': 'bold', 'color': '#1e293b', 
                             'textAlign': 'center', 'marginBottom': '16px'}),
                html.P("Select a module from the main menu.", 
                      style={'color': '#64748b', 'textAlign': 'center', 'marginBottom': '40px'}),
                
                html.Div([
                    html.A(
                        html.Div([
                            html.Div([
                                html.I(className="fa-solid fa-calendar-check", 
                                      style={'fontSize': '32px', 'color': '#6366f1', 'marginBottom': '16px'}),
                                html.H3("Attendance Analytics", 
                                       style={'fontWeight': '600', 'color': '#1e293b', 'marginBottom': '8px'}),
                                html.P("Upload CSV, visualize trends", 
                                      style={'color': '#64748b', 'fontSize': '14px'})
                            ])
                        ], style={
                            'background': 'white',
                            'borderRadius': '16px',
                            'padding': '28px',
                            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.05)',
                            'border': '1px solid #e2e8f0',
                            'textAlign': 'center',
                            'cursor': 'pointer',
                            'transition': 'transform 0.2s ease'
                        }),
                        href="/attendance",
                        style={'textDecoration': 'none'}
                    ),
                    
                    html.A(
                        html.Div([
                            html.Div([
                                html.I(className="fa-solid fa-graduation-cap", 
                                      style={'fontSize': '32px', 'color': '#7c3aed', 'marginBottom': '16px'}),
                                html.H3("Marks Analytics", 
                                       style={'fontWeight': '600', 'color': '#1e293b', 'marginBottom': '8px'}),
                                html.P("Analyze grades & performance", 
                                      style={'color': '#64748b', 'fontSize': '14px'})
                            ])
                        ], style={
                            'background': 'white',
                            'borderRadius': '16px',
                            'padding': '28px',
                            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.05)',
                            'border': '1px solid #e2e8f0',
                            'textAlign': 'center',
                            'cursor': 'pointer',
                            'transition': 'transform 0.2s ease',
                            'marginLeft': '20px'
                        }),
                        href="/marks",
                        style={'textDecoration': 'none'}
                    )
                ], style={'display': 'flex', 'justifyContent': 'center', 'gap': '20px', 'maxWidth': '800px', 'margin': '0 auto'})
            ])
        ], style={
            'padding': '60px 20px',
            'minHeight': '100vh', 
            'background': 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)'
        })

# Global download callback for both modules
@app.callback(
    Output("global-download-data", "data"),
    [Input("attendance-download-btn", "n_clicks"),
     Input("marks-download-btn", "n_clicks")],
    [State('attendance-upload-store', 'data'),
     State('marks-upload-store', 'data')],
    prevent_initial_call=True
)
def handle_global_download(attendance_clicks, marks_clicks, attendance_data, marks_data):
    ctx = callback_context
    
    if not ctx.triggered:
        return dash.no_update
    
    # Get which button was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "attendance-download-btn" and attendance_data:
        # Decode base64 data
        decoded = base64.b64decode(attendance_data)
        return dict(
            content=decoded,
            filename="attendance_data.csv"
        )
    elif button_id == "marks-download-btn" and marks_data:
        # Decode base64 data
        decoded = base64.b64decode(marks_data)
        return dict(
            content=decoded,
            filename="marks_data.csv"
        )
    
    return dash.no_update

# Store attendance upload data
@app.callback(
    Output('attendance-upload-store', 'data'),
    [Input('attendance-upload', 'contents')]
)
def store_attendance_data(contents):
    if contents is None:
        return None
    
    # Extract just the base64 part
    content_type, content_string = contents.split(',')
    return content_string

# Store marks upload data
@app.callback(
    Output('marks-upload-store', 'data'),
    [Input('marks-upload', 'contents')]
)
def store_marks_data(contents):
    if contents is None:
        return None
    
    # Extract just the base64 part
    content_type, content_string = contents.split(',')
    return content_string

# Register Callbacks (remove download callbacks from modules)
register_attendance_callbacks(app)
register_marks_callbacks(app)

# IMPORTANT: Remove the download callbacks from attendance.py and marks.py
# Or comment them out since we're handling downloads globally

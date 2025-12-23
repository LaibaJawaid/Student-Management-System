import dash
import pandas as pd
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import io
import base64

# --- LAYOUT DEFINITION ---
def get_attendance_layout():
    return html.Div([
        
        # 1. Header & Upload Section
        html.Div([
            html.Div([
                html.H1("📊 Attendance Analytics Dashboard", 
                        style={'fontSize': '32px', 'fontWeight': '800', 'color': '#0f172a', 'marginBottom': '8px', 'letterSpacing': '-0.02em'}),
                html.P("Upload your CSV file to visualize attendance trends & performance metrics.", 
                       style={'color': '#64748b', 'marginBottom': '24px', 'fontSize': '15px'}),
                
                dcc.Upload(
                    id='attendance-upload',
                    children=html.Div([
                        html.I(className="fa-solid fa-cloud-arrow-up", 
                               style={'fontSize': '48px', 'color': '#6366f1', 'marginBottom': '16px'}),
                        html.H3("Drop your attendance file here", 
                               style={'fontSize': '20px', 'fontWeight': '700', 'color': '#1e293b', 'marginBottom': '8px'}),
                        html.P("Supports CSV files with columns: date, status, section", 
                               style={'color': '#94a3b8', 'fontSize': '14px', 'marginBottom': '20px'}),
                        html.Button(
                            "Browse Files",
                            style={
                                'background': 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
                                'color': 'white', 'border': 'none', 'padding': '12px 28px',
                                'borderRadius': '10px', 'fontWeight': '600', 'cursor': 'pointer',
                                'fontSize': '15px', 'boxShadow': '0 8px 20px rgba(99, 102, 241, 0.3)',
                                'transition': 'all 0.3s ease'
                            }
                        )
                    ], style={'textAlign': 'center'}),
                    style={
                        'border': '3px dashed #c7d2fe', 'borderRadius': '20px', 'padding': '40px',
                        'textAlign': 'center', 'cursor': 'pointer', 'background': 'white',
                        'transition': 'all 0.3s ease', 'boxShadow': '0 4px 20px rgba(0,0,0,0.04)'
                    },
                    multiple=False
                ),
                html.Div(id='upload-status', style={'marginTop': '20px'})
            ], style={
                'background': 'white', 
                'borderRadius': '20px', 
                'padding': '36px', 
                'boxShadow': '0 10px 40px rgba(0,0,0,0.06)',
                'border': '1px solid #f1f5f9'
            })
        ], style={'marginBottom': '28px'}),
        
        # 2. KPI Cards Section
        html.Div(id='kpi-container', 
                style={
                    'display': 'grid', 
                    'gridTemplateColumns': 'repeat(auto-fit, minmax(240px, 1fr))', 
                    'gap': '20px', 
                    'marginBottom': '28px'
                }),
        
        # 3. Charts Section
        html.Div(id='charts-container', className="hidden", children=[
            
            # Row 1: Pie & Bar (Side by Side)
            html.Div([
                # Pie Chart
                html.Div([
                    html.Div([
                        html.H3("📊 Attendance Distribution", 
                               style={'fontSize': '19px', 'fontWeight': '700', 'color': '#0f172a', 'margin': '0'}),
                        html.I(className="fa-solid fa-chart-pie", 
                              style={'color': '#8b5cf6', 'fontSize': '20px'})
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '16px'}),
                    dcc.Graph(id='attendance-pie', config={'displayModeBar': False}, style={'height': '320px'})
                ], style={
                    'background': 'white', 
                    'borderRadius': '18px', 
                    'padding': '24px', 
                    'boxShadow': '0 4px 20px rgba(0,0,0,0.05)', 
                    'border': '1px solid #f1f5f9'
                }),
                
                # Bar Chart
                html.Div([
                    html.Div([
                        html.H3("📈 Section Performance", 
                               style={'fontSize': '19px', 'fontWeight': '700', 'color': '#0f172a', 'margin': '0'}),
                        html.I(className="fa-solid fa-chart-bar", 
                              style={'color': '#3b82f6', 'fontSize': '20px'})
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '16px'}),
                    dcc.Graph(id='section-bar', config={'displayModeBar': False}, style={'height': '320px'})
                ], style={
                    'background': 'white', 
                    'borderRadius': '18px', 
                    'padding': '24px', 
                    'boxShadow': '0 4px 20px rgba(0,0,0,0.05)', 
                    'border': '1px solid #f1f5f9'
                }),
            ], style={
                'display': 'grid', 
                'gridTemplateColumns': 'repeat(auto-fit, minmax(450px, 1fr))', 
                'gap': '20px', 
                'marginBottom': '24px'
            }),
            
            # Row 2: Trend Chart
            html.Div([
                html.Div([
                    html.H3("📅 Daily Attendance Trend", 
                           style={'fontSize': '19px', 'fontWeight': '700', 'color': '#0f172a', 'margin': '0'}),
                    html.I(className="fa-solid fa-chart-line", 
                          style={'color': '#10b981', 'fontSize': '20px'})
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '16px'}),
                dcc.Graph(id='trend-line', config={'displayModeBar': False}, style={'height': '360px'})
            ], style={
                'background': 'white', 
                'borderRadius': '18px', 
                'padding': '24px', 
                'boxShadow': '0 4px 20px rgba(0,0,0,0.05)', 
                'border': '1px solid #f1f5f9', 
                'marginBottom': '24px'
            }),
            
            # Row 3: Summary Table
            html.Div([
                html.Div([
                    html.H3("📋 Summary Report", 
                           style={'fontSize': '19px', 'fontWeight': '700', 'color': '#0f172a', 'margin': '0'}),
                    html.Button([
                        html.I(className="fa-solid fa-download", style={'marginRight': '8px'}),
                        "Download CSV"
                    ], id="download-btn", 
                       style={
                           'background': 'linear-gradient(135deg, #10b981 0%, #059669 100%)', 
                           'color': 'white', 
                           'border': 'none', 
                           'padding': '10px 20px', 
                           'borderRadius': '10px', 
                           'fontWeight': '600', 
                           'cursor': 'pointer', 
                           'fontSize': '14px',
                           'boxShadow': '0 4px 12px rgba(16, 185, 129, 0.3)'
                       })
                ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '20px'}),
                
                dcc.Download(id="download-data"),
                html.Div(id='summary-table')
            ], style={
                'background': 'white', 
                'borderRadius': '18px', 
                'padding': '24px', 
                'boxShadow': '0 4px 20px rgba(0,0,0,0.05)', 
                'border': '1px solid #f1f5f9'
            })
        ])
        
    ], style={
        'padding': '28px', 
        'maxWidth': '1280px', 
        'margin': '0 auto', 
        'background': 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)', 
        'minHeight': '100vh', 
        'fontFamily': '"Inter", -apple-system, sans-serif'
    })


# Helper for KPI cards with gradients
def create_kpi_card(title, value, color, icon):
    color_styles = {
        'blue': {
            'gradient': 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
            'shadow': 'rgba(59, 130, 246, 0.3)',
            'icon_bg': 'rgba(255, 255, 255, 0.2)'
        },
        'green': {
            'gradient': 'linear-gradient(135deg, #10b981 0%, #047857 100%)',
            'shadow': 'rgba(16, 185, 129, 0.3)',
            'icon_bg': 'rgba(255, 255, 255, 0.2)'
        },
        'red': {
            'gradient': 'linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)',
            'shadow': 'rgba(239, 68, 68, 0.3)',
            'icon_bg': 'rgba(255, 255, 255, 0.2)'
        },
        'yellow': {
            'gradient': 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
            'shadow': 'rgba(245, 158, 11, 0.3)',
            'icon_bg': 'rgba(255, 255, 255, 0.2)'
        }
    }
    
    style = color_styles.get(color, color_styles['blue'])
    
    return html.Div([
        html.Div([
            html.Div([
                html.P(title, style={
                    'fontSize': '12px', 
                    'fontWeight': '700', 
                    'color': 'rgba(255, 255, 255, 0.9)',
                    'textTransform': 'uppercase', 
                    'letterSpacing': '0.05em', 
                    'marginBottom': '8px'
                }),
                html.H4(value, style={
                    'fontSize': '32px', 
                    'fontWeight': '800', 
                    'color': 'white',
                    'margin': '0',
                    'lineHeight': '1'
                })
            ]),
            html.Div(
                html.I(className=f"fa-solid {icon}", style={'fontSize': '28px', 'color': 'white'}), 
                style={
                    'padding': '14px', 
                    'borderRadius': '12px', 
                    'background': style['icon_bg'],
                    'backdropFilter': 'blur(10px)'
                }
            )
        ], style={
            'display': 'flex', 
            'justifyContent': 'space-between', 
            'alignItems': 'center'
        })
    ], style={
        'background': style['gradient'],
        'padding': '24px',
        'borderRadius': '16px',
        'boxShadow': f"0 8px 24px {style['shadow']}",
        'transition': 'transform 0.3s ease',
        'border': '1px solid rgba(255, 255, 255, 0.1)'
    })


# --- CHART STYLING HELPER ---
def apply_chart_styling(fig, height=320):
    fig.update_layout(
        font=dict(family="Inter, -apple-system, sans-serif", size=13, color="#475569"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=10, b=40, l=50, r=20),
        height=height,
        xaxis=dict(
            showgrid=False, 
            showline=True, 
            linecolor='#e2e8f0', 
            tickfont=dict(size=12, color='#64748b')
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='rgba(226, 232, 240, 0.5)', 
            showline=False, 
            tickfont=dict(size=12, color='#64748b')
        ),
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=-0.2, 
            xanchor="center", 
            x=0.5, 
            font=dict(size=12, color='#475569')
        )
    )
    return fig


# --- CALLBACKS ---
def register_attendance_callbacks(app):
    
    @app.callback(
        [Output('upload-status', 'children'),
         Output('kpi-container', 'children'),
         Output('attendance-pie', 'figure'),
         Output('section-bar', 'figure'),
         Output('trend-line', 'figure'),
         Output('summary-table', 'children'),
         Output('charts-container', 'className')],
        [Input('attendance-upload', 'contents')],
        [State('attendance-upload', 'filename')]
    )
    def update_dashboard(contents, filename):
        if contents is None:
            return (
                html.Div("📁 Upload a CSV file to begin analysis", 
                        style={'color': '#64748b', 'textAlign': 'center', 'padding': '12px', 'fontSize': '15px'}),
                [], {}, {}, {}, html.Div(), "hidden"
            )

        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            try:
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            except:
                df = pd.read_csv(io.StringIO(decoded.decode('latin-1')))
            
            df.columns = [str(col).strip().lower().replace(' ', '_') for col in df.columns]
            
            if 'status' not in df.columns:
                return (
                    html.Div([
                        html.I(className="fa-solid fa-triangle-exclamation", style={'marginRight': '10px'}),
                        " Error: CSV must contain 'status' column"
                    ], style={
                        'background': '#fef2f2', 
                        'color': '#dc2626', 
                        'padding': '16px', 
                        'borderRadius': '12px', 
                        'fontWeight': '600',
                        'border': '2px solid #fca5a5',
                        'textAlign': 'center'
                    }), 
                    [], {}, {}, {}, html.Div(), "hidden"
                )
            
            df['status'] = df['status'].astype(str).str.strip().str.title()
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                df = df.dropna(subset=['date'])
            
            # KPI Calculations
            total = len(df)
            present = len(df[df['status'] == 'Present'])
            absent = len(df[df['status'] == 'Absent'])
            late = len(df[df['status'] == 'Late'])
            rate = round((present / total) * 100, 1) if total > 0 else 0
            
            kpis = [
                create_kpi_card("Total Records", f"{total:,}", "blue", "fa-users"),
                create_kpi_card("Present", f"{present:,}", "green", "fa-user-check"),
                create_kpi_card("Absent", f"{absent:,}", "red", "fa-user-xmark"),
                create_kpi_card("Attendance Rate", f"{rate}%", "yellow", "fa-chart-line")
            ]
            
            # Chart Colors
            color_map = {'Present': "#3b82f6", 'Absent': "#ec4899", 'Late': "#f59e0b"}
            
            # Pie Chart with Donut Style
            status_counts = df['status'].value_counts()
            pie_fig = go.Figure(data=[go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                hole=0.6,
                marker=dict(
                    colors=[color_map.get(status, '#94a3b8') for status in status_counts.index],
                    line=dict(color='white', width=3)
                ),
                textposition='outside',
                textinfo='percent+label',
                textfont=dict(size=14, weight='bold', color='#334155'),
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )])
            
            pie_fig.update_layout(
                showlegend=False,
                annotations=[dict(
                    text=f'<b>{rate}%</b><br><span style="font-size:12px; color:#64748b;">Overall</span>',
                    x=0.5, y=0.5,
                    font=dict(size=28, color='#0f172a'),
                    showarrow=False
                )]
            )
            pie_fig = apply_chart_styling(pie_fig, height=320)
            
            # Bar Chart - Section Performance
            if 'section' in df.columns:
                bar_data = df.groupby(['section', 'status']).size().reset_index(name='count')
                bar_fig = px.bar(
                    bar_data, 
                    x='section', 
                    y='count', 
                    color='status', 
                    color_discrete_map=color_map, 
                    barmode='group'
                )
                bar_fig.update_traces(
                    marker_line_color='white',
                    marker_line_width=2,
                    texttemplate='%{y}',
                    textposition='outside',
                    textfont=dict(size=12, weight='bold')
                )
                bar_fig = apply_chart_styling(bar_fig, height=320)
            else:
                bar_fig = go.Figure()
                bar_fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=320,
                    annotations=[dict(
                        text="No section data available",
                        xref="paper", yref="paper",
                        x=0.5, y=0.5,
                        showarrow=False,
                        font=dict(size=16, color='#94a3b8')
                    )]
                )
            
            # Trend Line with Area Fill
            if 'date' in df.columns:
                trend_data = df[df['status'] == 'Present'].groupby('date').size().reset_index(name='count').sort_values('date')
                trend_fig = go.Figure()
                
                # Area fill
                trend_fig.add_trace(go.Scatter(
                    x=trend_data['date'],
                    y=trend_data['count'],
                    fill='tozeroy',
                    fillcolor='rgba(59, 130, 246, 0.15)',
                    line=dict(color='rgba(0,0,0,0)'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                # Main line
                trend_fig.add_trace(go.Scatter(
                    x=trend_data['date'],
                    y=trend_data['count'],
                    mode='lines+markers',
                    name='Present',
                    line=dict(color='#3b82f6', width=4, shape='spline'),
                    marker=dict(size=10, color='white', line=dict(width=3, color='#3b82f6')),
                    hovertemplate='<b>%{x|%b %d, %Y}</b><br>Present: %{y}<extra></extra>'
                ))
                
                trend_fig = apply_chart_styling(trend_fig, height=360)
            else:
                trend_fig = go.Figure()
                trend_fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=360,
                    annotations=[dict(
                        text="No date data available",
                        xref="paper", yref="paper",
                        x=0.5, y=0.5,
                        showarrow=False,
                        font=dict(size=16, color='#94a3b8')
                    )]
                )
            
            # Summary Table
            summary_data = [
                ('Total Records', f"{total:,}", '#3b82f6'),
                ('Present Count', f"{present:,}", '#10b981'),
                ('Absent Count', f"{absent:,}", '#ef4444'),
                ('Late Count', f"{late:,}", '#f59e0b'),
                ('Attendance Rate', f"{rate}%", '#8b5cf6')
            ]
            
            summary_html = html.Div([
                html.Div([
                    html.Div([
                        html.Div(style={
                            'width': '5px',
                            'height': '100%',
                            'background': item[2],
                            'borderRadius': '3px 0 0 3px'
                        }),
                        html.Div([
                            html.Span(item[0], style={
                                'fontSize': '14px',
                                'fontWeight': '600',
                                'color': '#475569'
                            }),
                            html.Span(item[1], style={
                                'fontSize': '20px',
                                'fontWeight': '800',
                                'color': item[2]
                            })
                        ], style={
                            'padding': '16px 20px',
                            'flex': '1',
                            'display': 'flex',
                            'flexDirection': 'column',
                            'gap': '4px'
                        })
                    ], style={
                        'display': 'flex',
                        'background': '#f8fafc',
                        'borderRadius': '12px',
                        'marginBottom': '12px',
                        'border': '1px solid #e2e8f0',
                        'overflow': 'hidden'
                    })
                ]) for item in summary_data
            ])
            
            msg = html.Div([
                html.I(className="fa-solid fa-circle-check", style={'fontSize': '22px', 'marginRight': '12px'}),
                html.Div([
                    html.Strong(f"✅ Successfully processed: {filename}", style={'display': 'block', 'marginBottom': '4px'}),
                    html.Span(f"{total} records analyzed • {present} present • {rate}% rate", style={'fontSize': '14px'})
                ])
            ], style={
                'background': 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)',
                'color': '#065f46',
                'padding': '18px 24px',
                'borderRadius': '12px',
                'fontWeight': '600',
                'border': '2px solid #6ee7b7',
                'display': 'flex',
                'alignItems': 'center'
            })
            
            return msg, kpis, pie_fig, bar_fig, trend_fig, summary_html, ""
            
        except Exception as e:
            return (
                html.Div([
                    html.I(className="fa-solid fa-bug", style={'marginRight': '10px'}),
                    f" Error: {str(e)}"
                ], style={
                    'background': '#fef2f2',
                    'color': '#dc2626',
                    'padding': '16px',
                    'borderRadius': '12px',
                    'fontWeight': '600',
                    'border': '2px solid #fca5a5',
                    'textAlign': 'center'
                }),
                [], {}, {}, {}, html.Div(), "hidden"
            )
    
    @app.callback(
        Output("download-data", "data"),
        Input("download-btn", "n_clicks"),
        State('attendance-upload', 'contents'),
        prevent_initial_call=True
    )
    def download_data(n_clicks, contents):
        if contents is None:
            return dash.no_update
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        return dict(content=decoded, filename="attendance_analysis.csv")
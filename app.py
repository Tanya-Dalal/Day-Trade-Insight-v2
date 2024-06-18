import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
from datetime import datetime as dt, timedelta
import pandas as pd
import plotly.graph_objects as go

from model import calculate_slope_and_predict, get_stock_data

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(className="container", children=[
    html.Div(className="nav", children=[
        html.H1("DAY", className="start"),
        html.H4("TRADE INSIGHT V2", className="start2"),
        html.Div([
            dcc.Input(id="stock-code", type="text", placeholder="Enter stock code"),
            dcc.DatePickerRange(id="date-picker-range", start_date=dt(2024, 6, 1), end_date=dt.now().date()),
            html.Button('Get Stock Price', id='stock-price-button'),
            html.Button('Get Indicators', id='indicators-button'),
            dcc.Input(id="forecast-days", type="number", placeholder="Enter number of days"),
            html.Button('Forecast', id='forecast-button'),
        ], className="inputs"),
    ]),
    html.Div(className="content", children=[
        html.Div(id="company-info", className="header"),
        html.Div(id="description", className="description_ticker"),
        html.Div(id="graphs-content", className="graph"),
        html.Div(id="main-content", className="graph"),
        html.Div(id="forecast-content", className="graph"),
    ])
])

def get_stock_price_fig(df):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open Price'],
        high=df['High Price'],
        low=df['Low Price'],
        close=df['Close Price'],
        name='Price'
    ))
    fig.update_layout(
        title="Stock Price vs Date", 
        xaxis_title="Date", yaxis_title="Price", 
        plot_bgcolor='#1f2025',
        paper_bgcolor='#1f2025',
        font=dict(color='white'))
    return fig

@app.callback(
    Output("company-info", "children"),
    [Input("stock-price-button", "n_clicks")],
    [State("stock-code", "value")]
)


def update_company_info(n_clicks, stock_code):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    
    end_date = dt.now()
    start_date = end_date - timedelta(days=14)
    df = get_stock_data(stock_code, start_date.strftime('%d-%m-%Y'), end_date.strftime('%d-%m-%Y'))
    
    if df.empty:
        return "No data available"
    

    columns_to_display = ['Date', 'Open Price', 'Close Price', 'Total Traded Quantity', 'Deliverable Quantity']
    table = dash_table.DataTable(
        columns=[{"name": col, "id": col} for col in columns_to_display],
        data=df[columns_to_display].to_dict('records'),
        style_table={'border': 'thin lightgrey solid'},
        style_cell={'textAlign': 'center'},
        style_header={'backgroundColor': '#cfcfd0', 'fontWeight': 'bold', 'color':'#1f2025', 'border': 'thin lightgrey solid'},
        style_data={
            'backgroundColor': '#1f2025', 'color':'#cfcfd0', 'width' : '15%', 'border': 'thin lightgrey solid'}
    )
    
    return table

@app.callback(
    Output("graphs-content", "children"),
    [Input("stock-price-button", "n_clicks")],
    [State("stock-code", "value"), State("date-picker-range", "start_date"), State("date-picker-range", "end_date")]
)
def update_stock_graph(n_clicks, stock_code, start_date, end_date):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    df = get_stock_data(stock_code, start_date.strftime('%d-%m-%Y'), end_date.strftime('%d-%m-%Y'))
    
    if df.empty:
        return "No data available"
    
    fig = get_stock_price_fig(df)
    return dcc.Graph(figure=fig)

@app.callback(
    Output("main-content", "children"),
    [Input("indicators-button", "n_clicks")],
    [State("stock-code", "value"), State("date-picker-range", "start_date"), State("date-picker-range", "end_date")]
)
def update_indicator_graph(n_clicks, stock_code, start_date, end_date):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    df = get_stock_data(stock_code, start_date.strftime('%d-%m-%Y'), end_date.strftime('%d-%m-%Y'))
    
    if df.empty:
        return "No data available"
    
    df['EWA_20'] = df['Close Price'].ewm(span=20, adjust=False).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['EWA_20'], mode='lines', name='EWA 20'))
    fig.update_layout(
        title="Exponential Moving Average vs Date", 
        xaxis_title="Date", yaxis_title="EWA 20",
        plot_bgcolor='#1f2025',
        paper_bgcolor='#1f2025',
        font=dict(color='white'))
    
    return dcc.Graph(figure=fig)

@app.callback(
    Output("forecast-content", "children"),
    [Input("forecast-button", "n_clicks")],
    [State("stock-code", "value"), State("forecast-days", "value"), State("date-picker-range", "end_date")]
)
def update_forecast(n_clicks, stock_code, days, end_date):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    
    end_date = pd.to_datetime(end_date)
    start_date = end_date - timedelta(days=180)
    df = get_stock_data(stock_code, start_date.strftime('%d-%m-%Y'), end_date.strftime('%d-%m-%Y'))
    
    if df.empty:
        return "No data available"
    
    pivot_table = df.pivot_table(index='Date', values='Close Price', aggfunc='mean').sort_index()
    slope, predicted_next_value = calculate_slope_and_predict(pivot_table['Close Price'][-5:])
    
    if slope is None or predicted_next_value is None:
        return "Insufficient data to make predictions"
    
    latest_close_price = pivot_table['Close Price'].iloc[-1]
    next_predicted_close_prices = [latest_close_price + slope * i for i in range(1, days + 1)]
    
    dates = pd.date_range(start=end_date, periods=days).tolist()
    
    fig = go.Figure([go.Scatter(x=dates, y=next_predicted_close_prices, mode='lines', name='Forecast')])
    fig = fig.update_layout(
        title="Forecasted prices", 
        xaxis_title="Date", 
        yaxis_title="Price",
        plot_bgcolor='#1f2025',
        paper_bgcolor='#1f2025',
        font=dict(color='white'))
    
    predicted_values_str = '\n'.join([f"Day {i+1}: {price:.2f}" for i, price in enumerate(next_predicted_close_prices)])
    slope_str = f"Slope: {slope:.2f}"
    
    return html.Div([
        dcc.Graph(figure=fig),
        html.Pre(predicted_values_str, className="custom-pre"),
        html.Pre(slope_str, className="custom-pre")
    ])

if __name__ == '__main__':
    app.run_server(debug=True)

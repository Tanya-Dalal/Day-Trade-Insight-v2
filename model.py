import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from nselib import capital_market

def calculate_slope_and_predict(y_values):
    if len(y_values) < 2:
        return None, None

    x = np.array(range(len(y_values))).reshape(-1, 1)
    y = np.array(y_values).reshape(-1, 1)
    model = LinearRegression()
    model.fit(x, y)

    next_x = np.array([[len(y_values)]])
    predicted_next_y = model.predict(next_x)

    return model.coef_[0][0], predicted_next_y[0][0]

def get_stock_data(symbol, from_date, to_date):
    try:
        data = capital_market.price_volume_and_deliverable_position_data(symbol=symbol, from_date=from_date, to_date=to_date)
        print(f"Data fetched for {symbol}:")
        print(data.head())

        if not data.empty:
            # Clean numeric columns
            numeric_cols = ['PrevClose', 'OpenPrice', 'HighPrice', 'LowPrice', 'LastPrice', 'ClosePrice', 'AveragePrice',
                            'TotalTradedQuantity', 'TurnoverInRs', 'DeliverableQty', '%DlyQttoTradedQty']
            
            # Replace invalid entries with NaN
            data[numeric_cols] = data[numeric_cols].replace({',': '', '-': np.nan}, regex=True)
            
            # Convert columns to float
            data[numeric_cols] = data[numeric_cols].astype(float)

            # Drop rows with any NaN values in numeric columns
            data.dropna(subset=numeric_cols, inplace=True)

            # Adjust column names and convert date format
            data['Date'] = pd.to_datetime(data['Date'], format='%d-%b-%Y')
            data.rename(columns={
                'PrevClose': 'Previous Close',
                'OpenPrice': 'Open Price',
                'HighPrice': 'High Price',
                'LowPrice': 'Low Price',
                'LastPrice': 'Last Price',
                'ClosePrice': 'Close Price',
                'AveragePrice': 'Average Price',
                'TotalTradedQuantity': 'Total Traded Quantity',
                'TurnoverInRs': 'Turnover (INR)',
                'No.ofTrades': 'Number of Trades',
                'DeliverableQty': 'Deliverable Quantity',
                '%DlyQttoTradedQty': 'Percentage of Deliverable Quantity'
            }, inplace=True)

            # Sort by Date descending
            data.sort_values(by='Date', ascending=False, inplace=True)

        return data

    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

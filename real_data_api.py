#!/usr/bin/env python3
"""
Real Stock Data API - No API Keys Required!
Uses direct Yahoo Finance endpoint (free)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import RobustScaler
import json
import time

app = Flask(__name__)
CORS(app)

# Cache
model_cache = {}
data_cache = {}
cache_time = {}

def get_stock_data(symbol, period='3mo'):
    """Get real stock data from Yahoo Finance (no API key needed!)"""
    try:
        # Check cache (5 minute expiry)
        cache_key = f"{symbol}_{period}"
        if cache_key in data_cache:
            if time.time() - cache_time[cache_key] < 300:  # 5 minutes
                return data_cache[cache_key]

        # Yahoo Finance public API
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

        # Period mapping
        period_map = {
            '1d': '1d',
            '5d': '5d',
            '1mo': '1mo',
            '3mo': '3mo',
            '6mo': '6mo',
            '1y': '1y',
            '2y': '2y'
        }

        params = {
            'interval': '1d',
            'range': period_map.get(period, '3mo')
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()

        # Parse response
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]

        df = pd.DataFrame({
            'timestamp': timestamps,
            'open': quote['open'],
            'high': quote['high'],
            'low': quote['low'],
            'close': quote['close'],
            'volume': quote['volume']
        })

        # Convert timestamp to datetime
        df['date'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df.dropna()

        # Cache it
        data_cache[cache_key] = df
        cache_time[cache_key] = time.time()

        return df

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def calculate_indicators(df):
    """Calculate technical indicators"""
    # Returns
    df['returns'] = df['close'].pct_change()

    # Moving Averages
    df['sma_5'] = df['close'].rolling(5).mean()
    df['sma_10'] = df['close'].rolling(10).mean()
    df['sma_20'] = df['close'].rolling(20).mean()
    df['sma_50'] = df['close'].rolling(50).mean()

    # EMA
    df['ema_12'] = df['close'].ewm(span=12).mean()
    df['ema_26'] = df['close'].ewm(span=26).mean()

    # MACD
    df['macd'] = df['ema_12'] - df['ema_26']
    df['macd_signal'] = df['macd'].ewm(span=9).mean()

    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(20).mean()
    df['bb_std'] = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
    df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)

    # Volume
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']

    # Target
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)

    return df

def train_model(symbol):
    """Train ML model"""
    print(f"Training model for {symbol}...")

    df = get_stock_data(symbol, period='2y')
    if df is None or len(df) < 100:
        return None, None

    df = calculate_indicators(df)
    df = df.dropna()

    if len(df) < 50:
        return None, None

    # Features
    features = ['returns', 'sma_5', 'sma_10', 'sma_20', 'macd', 'rsi', 'volume_ratio']
    features = [f for f in features if f in df.columns]

    X = df[features]
    y = df['target']

    # Split
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # Scale
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train
    rf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
    gb = GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)

    rf.fit(X_train_scaled, y_train)
    gb.fit(X_train_scaled, y_train)

    # Simple ensemble (average probabilities)
    model = {'rf': rf, 'gb': gb, 'scaler': scaler, 'features': features}

    accuracy = (rf.score(X_test_scaled, y_test) + gb.score(X_test_scaled, y_test)) / 2
    print(f"{symbol} accuracy: {accuracy:.2%}")

    return model, accuracy

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'Real Data API - Yahoo Finance',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        symbol = data.get('symbol', '').upper()

        if not symbol:
            return jsonify({'error': 'Symbol required'}), 400

        # Get data
        df = get_stock_data(symbol, period='3mo')
        if df is None:
            return jsonify({'error': f'Could not fetch data for {symbol}'}), 500

        # Calculate indicators
        df = calculate_indicators(df)
        df = df.dropna()

        if len(df) == 0:
            return jsonify({'error': 'Insufficient data'}), 500

        # Current price
        current_price = float(df['close'].iloc[-1])

        # Train or get model
        if symbol not in model_cache:
            model, accuracy = train_model(symbol)
            if model is None:
                return jsonify({'error': 'Model training failed'}), 500
            model_cache[symbol] = model

        model = model_cache[symbol]

        # Prepare features
        latest = df[model['features']].iloc[-1:].values
        scaled = model['scaler'].transform(latest)

        # Predict
        rf_pred = model['rf'].predict_proba(scaled)[0]
        gb_pred = model['gb'].predict_proba(scaled)[0]

        # Average predictions
        avg_prob = (rf_pred + gb_pred) / 2
        prediction = 1 if avg_prob[1] > avg_prob[0] else 0
        confidence = avg_prob[prediction]

        # Historical data for chart (last 90 days)
        historical = []
        chart_data = df.tail(90)
        for idx, row in chart_data.iterrows():
            historical.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row['volume'])
            })

        # Latest indicators
        latest_row = df.iloc[-1]

        return jsonify({
            'symbol': symbol,
            'prediction': 'BUY' if prediction == 1 else 'SELL',
            'confidence': float(confidence),
            'up_probability': float(avg_prob[1]),
            'down_probability': float(avg_prob[0]),
            'current_price': current_price,
            'historical_data': historical,
            'indicators': {
                'rsi': float(latest_row['rsi']) if not pd.isna(latest_row['rsi']) else None,
                'macd': float(latest_row['macd']) if not pd.isna(latest_row['macd']) else None,
                'sma_20': float(latest_row['sma_20']) if not pd.isna(latest_row['sma_20']) else None,
                'volume': 'High' if latest_row['volume_ratio'] > 1.2 else 'Low' if latest_row['volume_ratio'] < 0.8 else 'Normal'
            },
            'change_24h': float((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100),
            'timestamp': datetime.now().isoformat(),
            'data_source': 'Yahoo Finance (Free)'
        })

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 REAL DATA API SERVER")
    print("="*70)
    print("\n✅ Using Yahoo Finance public API (100% FREE!)")
    print("📊 Real stock prices - no API keys needed")
    print("🤖 Machine Learning predictions")
    print("📈 TradingView-style data")
    print("\n🌐 Server: http://localhost:5000")
    print("📱 Mobile: http://YOUR_IP:5000")
    print("\n" + "="*70 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)

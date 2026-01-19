#!/usr/bin/env python3
"""
Simple API Server with FREE Real Stock Data
No API keys needed - uses Yahoo Finance (yfinance)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.preprocessing import RobustScaler
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Cache for trained models
model_cache = {}
scaler_cache = {}

def create_features(df):
    """Create technical indicators"""
    # Returns
    df['returns'] = df['Close'].pct_change()

    # Moving averages
    df['sma_5'] = df['Close'].rolling(window=5).mean()
    df['sma_10'] = df['Close'].rolling(window=10).mean()
    df['sma_20'] = df['Close'].rolling(window=20).mean()
    df['sma_50'] = df['Close'].rolling(window=50).mean()

    # EMA
    df['ema_12'] = df['Close'].ewm(span=12).mean()
    df['ema_26'] = df['Close'].ewm(span=26).mean()

    # MACD
    df['macd'] = df['ema_12'] - df['ema_26']
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_histogram'] = df['macd'] - df['macd_signal']

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi_14'] = 100 - (100 / (1 + rs))

    # Bollinger Bands
    df['bb_middle'] = df['Close'].rolling(window=20).mean()
    df['bb_std'] = df['Close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
    df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
    df['bb_position'] = (df['Close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

    # Volatility
    df['volatility_10'] = df['returns'].rolling(window=10).std()
    df['volatility_20'] = df['returns'].rolling(window=20).std()

    # Volume
    df['volume_sma_20'] = df['Volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['Volume'] / df['volume_sma_20']

    # Momentum
    df['momentum_5'] = df['Close'] / df['Close'].shift(5) - 1
    df['momentum_10'] = df['Close'] / df['Close'].shift(10) - 1

    # Target
    df['target'] = (df['Close'].shift(-1) > df['Close']).astype(int)

    return df

def train_model(symbol):
    """Train ML model on historical data"""
    print(f"Training model for {symbol}...")

    # Download data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years

    stock = yf.Ticker(symbol)
    df = stock.history(start=start_date, end=end_date)

    if df.empty:
        return None, None, 0

    # Create features
    df = create_features(df)
    df_clean = df.dropna()

    if len(df_clean) < 100:
        return None, None, 0

    # Prepare data
    feature_cols = ['returns', 'sma_5', 'sma_10', 'sma_20', 'sma_50',
                   'macd', 'macd_histogram', 'rsi_14', 'bb_position',
                   'volatility_10', 'volume_ratio', 'momentum_5', 'momentum_10']

    X = df_clean[feature_cols]
    y = df_clean['target']

    # Split
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    # Scale
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train ensemble
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    gb = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)

    ensemble = VotingClassifier(
        estimators=[('rf', rf), ('gb', gb)],
        voting='soft'
    )

    ensemble.fit(X_train_scaled, y_train)

    # Accuracy
    accuracy = ensemble.score(X_test_scaled, y_test)

    print(f"{symbol} accuracy: {accuracy:.2%}")

    return ensemble, scaler, accuracy

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'message': 'Simple API with real data'})

@app.route('/api/predict', methods=['POST'])
def predict():
    """Get prediction for a symbol"""
    try:
        data = request.json
        symbol = data.get('symbol', '').upper()

        if not symbol:
            return jsonify({'error': 'Symbol required'}), 400

        # Get or train model
        if symbol not in model_cache:
            model, scaler, accuracy = train_model(symbol)
            if model is None:
                return jsonify({'error': f'Could not fetch data for {symbol}'}), 500
            model_cache[symbol] = model
            scaler_cache[symbol] = scaler

        model = model_cache[symbol]
        scaler = scaler_cache[symbol]

        # Get recent data
        stock = yf.Ticker(symbol)
        df = stock.history(period='3mo')

        if df.empty:
            return jsonify({'error': 'No data available'}), 500

        # Get current price
        current_price = float(df['Close'].iloc[-1])

        # Create features
        df = create_features(df)
        df_clean = df.dropna()

        if len(df_clean) == 0:
            return jsonify({'error': 'Insufficient data'}), 500

        # Prepare features
        feature_cols = ['returns', 'sma_5', 'sma_10', 'sma_20', 'sma_50',
                       'macd', 'macd_histogram', 'rsi_14', 'bb_position',
                       'volatility_10', 'volume_ratio', 'momentum_5', 'momentum_10']

        latest_features = df_clean[feature_cols].iloc[-1:].values
        scaled_features = scaler.transform(latest_features)

        # Predict
        prediction = model.predict(scaled_features)[0]
        probabilities = model.predict_proba(scaled_features)[0]
        confidence = probabilities[prediction]

        # Get historical prices for chart
        historical_data = []
        for idx, row in df.tail(90).iterrows():
            historical_data.append({
                'date': idx.strftime('%Y-%m-%d'),
                'price': float(row['Close'])
            })

        # Calculate indicators
        latest = df_clean.iloc[-1]

        return jsonify({
            'symbol': symbol,
            'prediction': 'BUY' if prediction == 1 else 'SELL',
            'confidence': float(confidence),
            'up_probability': float(probabilities[1]),
            'down_probability': float(probabilities[0]),
            'current_price': current_price,
            'historical_data': historical_data,
            'indicators': {
                'rsi': float(latest['rsi_14']) if not pd.isna(latest['rsi_14']) else None,
                'macd': float(latest['macd']) if not pd.isna(latest['macd']) else None,
                'bb_position': 'Upper Band' if latest['bb_position'] > 0.8 else 'Lower Band' if latest['bb_position'] < 0.2 else 'Middle',
                'volume': 'High' if latest['volume_ratio'] > 1.2 else 'Low' if latest['volume_ratio'] < 0.8 else 'Normal'
            },
            'timestamp': datetime.now().isoformat(),
            'data_source': 'Yahoo Finance (Free)',
            'model': 'Random Forest + Gradient Boosting Ensemble'
        })

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Simple API Server with REAL Stock Data")
    print("="*60)
    print("\n✅ Using Yahoo Finance (100% FREE - No API keys needed!)")
    print("📊 Real-time stock prices")
    print("🤖 ML predictions with ensemble models")
    print("\nServer running at: http://localhost:5000")
    print("\n📱 Access from mobile: Use your computer's IP")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)

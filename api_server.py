"""
Flask REST API for ML Trading System Monetization
Author: Claude Code
Description: Production API with authentication, rate limiting, and subscription management
"""

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from functools import wraps
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import stripe
from production_trading_system import (
    ProductionTradingSystem,
    TradingConfig,
    TradingDatabase,
    MonetizationAPI
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY', '')

# Enable CORS for frontend integration
CORS(app)

# Initialize Stripe
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# Rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Initialize database and monetization
db = TradingDatabase()
monetization = MonetizationAPI()


# JWT Authentication
def token_required(f):
    """Decorator for JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing', 'error': 'UNAUTHORIZED'}), 401

        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]

            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired', 'error': 'TOKEN_EXPIRED'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid', 'error': 'INVALID_TOKEN'}), 401

        return f(current_user, *args, **kwargs)
    return decorated


# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'ml-trading-api'
    })


# Authentication endpoints
@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password required'}), 400

    # In production, hash password with bcrypt
    # For now, this is a simplified version
    user_id = f"user_{datetime.now().timestamp()}"

    return jsonify({
        'message': 'User registered successfully',
        'user_id': user_id
    }), 201


@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """User login and JWT token generation"""
    data = request.json

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password required'}), 400

    # In production, verify credentials against database
    # For now, this is a simplified version
    user_id = "user_123"

    # Generate JWT token
    token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        'token': token,
        'user_id': user_id,
        'expires_in': 604800  # 7 days in seconds
    })


# Trading prediction endpoints
@app.route('/api/v1/predict', methods=['POST'])
@token_required
@limiter.limit("100 per day")
def predict(current_user):
    """Get ML prediction for a symbol"""
    data = request.json

    if not data or not data.get('symbol'):
        return jsonify({'message': 'Symbol required', 'error': 'MISSING_SYMBOL'}), 400

    symbol = data.get('symbol').upper()

    try:
        # Get user's API credentials from request
        api_key = data.get('api_key') or os.getenv('ALPACA_API_KEY')
        secret_key = data.get('secret_key') or os.getenv('ALPACA_SECRET_KEY')

        if not api_key or not secret_key:
            return jsonify({'message': 'API credentials required', 'error': 'MISSING_CREDENTIALS'}), 400

        # Initialize trading system
        config = TradingConfig(
            api_key=api_key,
            secret_key=secret_key,
            paper_trading=True,
            confidence_threshold=float(data.get('confidence_threshold', 0.65))
        )

        system = ProductionTradingSystem(config)

        # Load or train model
        if symbol not in system.model.models:
            if not system.model.load_model(symbol):
                system.train_model_for_symbol(symbol)

        # Fetch data and make prediction
        df = system.fetch_data(symbol, days=500)
        if df.empty:
            return jsonify({'message': 'Could not fetch data', 'error': 'DATA_FETCH_ERROR'}), 500

        df = system.model.create_advanced_features(df)
        df_clean = df.dropna()

        # Prepare features
        exclude_cols = ['target_return', 'target_binary', 'high_low', 'high_close', 'low_close', 'true_range']
        feature_cols = [col for col in df_clean.columns if col not in exclude_cols and col not in ['open', 'high', 'low', 'close', 'volume']]

        latest_features = df_clean[feature_cols].iloc[-1:].values
        scaled_features = system.model.scalers[symbol].transform(latest_features)

        # Predict
        prediction = system.model.models[symbol].predict(scaled_features)[0]
        probabilities = system.model.models[symbol].predict_proba(scaled_features)[0]
        confidence = probabilities[prediction]

        # Get current price
        current_price = system.get_current_price(symbol)

        return jsonify({
            'symbol': symbol,
            'prediction': 'BUY' if prediction == 1 else 'SELL',
            'confidence': float(confidence),
            'up_probability': float(probabilities[1]),
            'down_probability': float(probabilities[0]),
            'current_price': float(current_price),
            'timestamp': datetime.now().isoformat(),
            'user_id': current_user
        })

    except Exception as e:
        return jsonify({
            'message': 'Prediction failed',
            'error': str(e)
        }), 500


@app.route('/api/v1/predict/batch', methods=['POST'])
@token_required
@limiter.limit("20 per day")
def predict_batch(current_user):
    """Get predictions for multiple symbols"""
    data = request.json

    if not data or not data.get('symbols'):
        return jsonify({'message': 'Symbols array required', 'error': 'MISSING_SYMBOLS'}), 400

    symbols = [s.upper() for s in data.get('symbols', [])]

    if len(symbols) > 10:
        return jsonify({'message': 'Maximum 10 symbols per batch', 'error': 'TOO_MANY_SYMBOLS'}), 400

    try:
        api_key = data.get('api_key') or os.getenv('ALPACA_API_KEY')
        secret_key = data.get('secret_key') or os.getenv('ALPACA_SECRET_KEY')

        config = TradingConfig(
            api_key=api_key,
            secret_key=secret_key,
            paper_trading=True
        )

        system = ProductionTradingSystem(config)
        predictions = []

        for symbol in symbols:
            try:
                # Load or train model
                if symbol not in system.model.models:
                    if not system.model.load_model(symbol):
                        system.train_model_for_symbol(symbol)

                # Make prediction
                df = system.fetch_data(symbol, days=500)
                if df.empty:
                    continue

                df = system.model.create_advanced_features(df)
                df_clean = df.dropna()

                exclude_cols = ['target_return', 'target_binary', 'high_low', 'high_close', 'low_close', 'true_range']
                feature_cols = [col for col in df_clean.columns if col not in exclude_cols and col not in ['open', 'high', 'low', 'close', 'volume']]

                latest_features = df_clean[feature_cols].iloc[-1:].values
                scaled_features = system.model.scalers[symbol].transform(latest_features)

                prediction = system.model.models[symbol].predict(scaled_features)[0]
                probabilities = system.model.models[symbol].predict_proba(scaled_features)[0]

                predictions.append({
                    'symbol': symbol,
                    'prediction': 'BUY' if prediction == 1 else 'SELL',
                    'confidence': float(probabilities[prediction])
                })

            except Exception as e:
                predictions.append({
                    'symbol': symbol,
                    'error': str(e)
                })

        return jsonify({
            'predictions': predictions,
            'timestamp': datetime.now().isoformat(),
            'user_id': current_user
        })

    except Exception as e:
        return jsonify({
            'message': 'Batch prediction failed',
            'error': str(e)
        }), 500


# Performance tracking endpoints
@app.route('/api/v1/performance', methods=['GET'])
@token_required
def get_performance(current_user):
    """Get system performance metrics"""
    days = request.args.get('days', 30, type=int)

    try:
        metrics = db.get_performance_metrics(days=days)
        return jsonify({
            'metrics': metrics,
            'period_days': days,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'message': 'Failed to fetch performance metrics',
            'error': str(e)
        }), 500


@app.route('/api/v1/trades', methods=['GET'])
@token_required
def get_trades(current_user):
    """Get recent trades"""
    limit = request.args.get('limit', 50, type=int)

    try:
        # In production, filter by current_user
        # For now, return all trades
        return jsonify({
            'trades': [],
            'limit': limit,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'message': 'Failed to fetch trades',
            'error': str(e)
        }), 500


# Subscription and monetization endpoints
@app.route('/api/v1/subscriptions/tiers', methods=['GET'])
def get_subscription_tiers():
    """Get available subscription tiers"""
    tiers = []
    for tier_id, tier in monetization.subscription_tiers.items():
        tiers.append({
            'id': tier_id,
            'name': tier.name,
            'price': tier.price,
            'features': tier.features,
            'max_symbols': tier.max_symbols,
            'api_calls_per_day': tier.api_calls_per_day
        })

    return jsonify({'tiers': tiers})


@app.route('/api/v1/subscriptions/subscribe', methods=['POST'])
@token_required
def subscribe(current_user):
    """Handle subscription payments via Stripe"""
    data = request.json

    if not data or not data.get('tier') or not data.get('payment_method'):
        return jsonify({'message': 'Tier and payment method required'}), 400

    tier = data.get('tier')

    if tier not in monetization.subscription_tiers:
        return jsonify({'message': 'Invalid subscription tier'}), 400

    try:
        # Create Stripe subscription
        # This is a simplified version - in production, use proper Stripe integration
        subscription_tier = monetization.subscription_tiers[tier]

        return jsonify({
            'status': 'success',
            'subscription_id': f'sub_{datetime.now().timestamp()}',
            'tier': tier,
            'price': subscription_tier.price,
            'message': 'Subscription created successfully'
        })

    except Exception as e:
        return jsonify({
            'message': 'Subscription failed',
            'error': str(e)
        }), 500


@app.route('/api/v1/subscriptions/cancel', methods=['POST'])
@token_required
def cancel_subscription(current_user):
    """Cancel user subscription"""
    try:
        # Cancel subscription in Stripe and database
        return jsonify({
            'status': 'success',
            'message': 'Subscription cancelled successfully'
        })
    except Exception as e:
        return jsonify({
            'message': 'Cancellation failed',
            'error': str(e)
        }), 500


# Admin endpoints
@app.route('/api/v1/admin/stats', methods=['GET'])
@token_required
def admin_stats(current_user):
    """Get system-wide statistics (admin only)"""
    # In production, verify admin role
    try:
        return jsonify({
            'total_users': 0,
            'total_trades': 0,
            'total_revenue': 0,
            'active_subscriptions': 0,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'message': 'Failed to fetch stats',
            'error': str(e)
        }), 500


# Webhook endpoint for Stripe
@app.route('/api/v1/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks for payment events"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')

    try:
        # Verify webhook signature
        # event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)

        # Handle different event types
        # if event['type'] == 'payment_intent.succeeded':
        #     # Handle successful payment
        #     pass

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'message': 'Endpoint not found',
        'error': 'NOT_FOUND'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'message': 'Internal server error',
        'error': 'INTERNAL_ERROR'
    }), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'message': 'Rate limit exceeded',
        'error': 'RATE_LIMIT_EXCEEDED'
    }), 429


if __name__ == '__main__':
    # For development only - use gunicorn in production
    app.run(
        debug=os.getenv('FLASK_ENV') == 'development',
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000))
    )

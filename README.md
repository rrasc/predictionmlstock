# Production ML Trading System

A complete, production-ready machine learning trading system with enterprise features, REST API, and monetization capabilities.

## Features

### Core Trading System
- **Advanced ML Models**: Ensemble methods combining Random Forest, Gradient Boosting, and XGBoost
- **50+ Technical Indicators**: Comprehensive feature engineering including RSI, MACD, Bollinger Bands, ATR, and more
- **Risk Management**: Kelly Criterion-based position sizing with stop-loss and take-profit
- **Multi-Symbol Trading**: Support for trading multiple stocks simultaneously
- **Real-time Predictions**: Live market data integration via Alpaca API

### Enterprise Features
- **Production Logging**: Comprehensive logging system for trades, errors, and performance
- **Database Storage**: SQLite/PostgreSQL for storing trades, performance metrics, and user data
- **Performance Tracking**: Real-time performance metrics including win rate, total P&L, and Sharpe ratio
- **Model Persistence**: Save and load trained models for quick deployment

### REST API
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Prevent abuse with configurable rate limits
- **Multiple Endpoints**: Predictions, batch predictions, performance metrics, and more
- **CORS Support**: Frontend integration ready

### Monetization
- **Subscription Tiers**: Free, Starter, Professional, and Enterprise plans
- **Stripe Integration**: Payment processing for subscriptions
- **Usage Tracking**: API call monitoring for billing
- **Feature Gating**: Tier-based access control

## Quick Start

### Prerequisites
- Python 3.11+
- Alpaca API account (paper or live trading)
- Optional: Docker for containerized deployment

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/predictionmlstock.git
cd predictionmlstock
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Run the trading system:
```bash
python production_trading_system.py
```

6. Run the API server:
```bash
python api_server.py
```

## Docker Deployment

### Build and run with Docker Compose:
```bash
docker-compose up -d
```

This will start:
- Flask API server
- PostgreSQL database
- Redis cache
- Celery workers
- Nginx reverse proxy

### Access the API:
- API: http://localhost:5000
- Health check: http://localhost:5000/health

## API Documentation

### Authentication

**Register User**
```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Login**
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}

Response:
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user_id": "user_123",
  "expires_in": 604800
}
```

### Get Prediction

```bash
POST /api/v1/predict
Authorization: Bearer <your-token>
Content-Type: application/json

{
  "symbol": "AAPL",
  "api_key": "your-alpaca-key",
  "secret_key": "your-alpaca-secret"
}

Response:
{
  "symbol": "AAPL",
  "prediction": "BUY",
  "confidence": 0.75,
  "up_probability": 0.75,
  "down_probability": 0.25,
  "current_price": 178.50,
  "timestamp": "2026-01-18T10:30:00"
}
```

### Batch Predictions

```bash
POST /api/v1/predict/batch
Authorization: Bearer <your-token>
Content-Type: application/json

{
  "symbols": ["AAPL", "NVDA", "TSLA", "MSFT"],
  "api_key": "your-alpaca-key",
  "secret_key": "your-alpaca-secret"
}
```

### Performance Metrics

```bash
GET /api/v1/performance?days=30
Authorization: Bearer <your-token>

Response:
{
  "metrics": {
    "total_trades": 150,
    "winning_trades": 95,
    "win_rate": 0.633,
    "total_pnl": 12500.50,
    "avg_pnl": 83.34,
    "max_win": 2500.00,
    "max_loss": -500.00
  },
  "period_days": 30
}
```

### Subscription Tiers

```bash
GET /api/v1/subscriptions/tiers

Response:
{
  "tiers": [
    {
      "id": "free",
      "name": "Free",
      "price": 0,
      "features": ["1 symbol", "Basic predictions", "Daily email alerts"],
      "max_symbols": 1,
      "api_calls_per_day": 10
    },
    {
      "id": "professional",
      "name": "Professional",
      "price": 99.99,
      "features": ["20 symbols", "Ensemble models", "Real-time alerts", "API access"],
      "max_symbols": 20,
      "api_calls_per_day": 1000
    }
  ]
}
```

## Configuration

### Trading Parameters

Edit `.env` file:

```bash
# Risk Management
MAX_POSITION_SIZE=10000        # Maximum position size in $
MAX_PORTFOLIO_RISK=0.02        # 2% risk per trade
CONFIDENCE_THRESHOLD=0.65      # Minimum confidence to trade
STOP_LOSS_PCT=0.03            # 3% stop loss
TAKE_PROFIT_PCT=0.06          # 6% take profit
MAX_DAILY_TRADES=10           # Maximum trades per day
```

### Subscription Tiers

Modify tiers in `production_trading_system.py`:

```python
'professional': SubscriptionTier(
    name='Professional',
    price=99.99,
    features=['20 symbols', 'Ensemble models', 'Real-time alerts'],
    max_symbols=20,
    api_calls_per_day=1000,
    advanced_models=True,
    real_time_alerts=True
)
```

## ML Model Architecture

### Feature Engineering
- **Moving Averages**: SMA and EMA (5, 10, 20, 50, 100, 200 periods)
- **Momentum Indicators**: RSI (7, 14, 21), MACD, Stochastic Oscillator
- **Volatility**: Bollinger Bands (10, 20, 30), ATR
- **Volume**: Volume ratios, OBV
- **Price Patterns**: Channel positions, Williams %R

### Model Ensemble
1. **Random Forest**: 300 estimators, max depth 15
2. **Gradient Boosting**: 200 estimators, learning rate 0.05
3. **XGBoost**: 200 estimators, max depth 6

Voting ensemble with soft voting (XGBoost weighted 1.2x)

### Training Process
- Time series cross-validation (5 splits)
- 80/20 train/test split
- Robust scaling for feature normalization
- Model persistence with joblib

## Deployment Checklist

### Infrastructure
- ✅ Docker containerization
- ✅ Docker Compose orchestration
- ⬜ AWS/GCP/Azure deployment
- ⬜ Load balancer configuration
- ⬜ Auto-scaling setup

### Database
- ✅ SQLite for development
- ⬜ PostgreSQL for production
- ⬜ Database replication
- ⬜ Automated backups

### Monitoring
- ⬜ Datadog/New Relic integration
- ⬜ Sentry error tracking
- ⬜ Prometheus metrics
- ⬜ Grafana dashboards

### Security
- ✅ JWT authentication
- ✅ Rate limiting
- ⬜ SSL certificates
- ⬜ DDoS protection
- ⬜ API key encryption

### Monetization
- ✅ Stripe integration
- ✅ Subscription tiers
- ✅ Usage tracking
- ⬜ Revenue dashboards
- ⬜ Automated billing

## Performance Optimization

### Model Optimization
- Use pre-trained models for faster predictions
- Cache feature calculations
- Implement model retraining on schedule

### API Optimization
- Redis caching for frequent queries
- Database connection pooling
- Async request handling
- Response compression

### Scalability
- Horizontal scaling with load balancer
- Celery for background tasks
- Message queue for order processing
- CDN for static assets

## Monitoring and Alerts

### System Health
- API uptime monitoring
- Database connection checks
- Model prediction accuracy
- Trading execution success rate

### Trading Alerts
- Email notifications for trades
- Slack/Discord webhooks
- SMS alerts (Twilio)
- Real-time dashboard updates

## Testing

Run tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=. tests/
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details

## Disclaimer

This software is for educational purposes only. Trading stocks involves risk and you can lose money. Always do your own research and consult with a financial advisor before making investment decisions.

## Support

- Documentation: https://github.com/yourusername/predictionmlstock/wiki
- Issues: https://github.com/yourusername/predictionmlstock/issues
- Email: support@yourdomain.com

## Roadmap

- [ ] Mobile app (React Native)
- [ ] Advanced backtesting engine
- [ ] Options trading support
- [ ] Crypto trading integration
- [ ] Social trading features
- [ ] Paper trading dashboard
- [ ] Machine learning model marketplace
- [ ] Multi-language support

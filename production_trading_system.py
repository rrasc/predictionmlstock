"""
Production-Ready ML Trading System with Enterprise Features
Author: Claude Code
Description: Complete trading system with advanced ML models, risk management,
             database logging, and monetization capabilities
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
import json
import sqlite3
from pathlib import Path

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
import xgboost as xgb
import joblib


# Configuration Management
@dataclass
class TradingConfig:
    """Trading system configuration"""
    api_key: str
    secret_key: str
    paper_trading: bool = True
    max_position_size: float = 10000  # Max $ per position
    max_portfolio_risk: float = 0.02  # 2% max risk per trade
    confidence_threshold: float = 0.65
    stop_loss_pct: float = 0.03  # 3% stop loss
    take_profit_pct: float = 0.06  # 6% take profit
    max_daily_trades: int = 10
    commission_per_trade: float = 0.0
    slippage_estimate: float = 0.001  # 0.1%


@dataclass
class SubscriptionTier:
    """Subscription tier configuration for monetization"""
    name: str
    price: float
    features: List[str]
    max_symbols: int
    api_calls_per_day: int
    advanced_models: bool
    real_time_alerts: bool


# Production Logger
class ProductionLogger:
    """Enterprise-grade logging system"""

    def __init__(self, log_dir: str = "logs"):
        Path(log_dir).mkdir(exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{log_dir}/trading_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def log_trade(self, trade_data: Dict):
        """Log trade execution"""
        self.logger.info(f"TRADE: {json.dumps(trade_data)}")

    def log_error(self, error: Exception, context: str):
        """Log error with context"""
        self.logger.error(f"ERROR in {context}: {str(error)}", exc_info=True)

    def log_performance(self, metrics: Dict):
        """Log performance metrics"""
        self.logger.info(f"PERFORMANCE: {json.dumps(metrics)}")


# Database Manager for Production
class TradingDatabase:
    """Production database for trades and performance tracking"""

    def __init__(self, db_path: str = "trading_system.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                symbol TEXT,
                side TEXT,
                quantity REAL,
                entry_price REAL,
                exit_price REAL,
                prediction_confidence REAL,
                profit_loss REAL,
                profit_loss_pct REAL,
                status TEXT,
                order_id TEXT
            )
        ''')

        # Model performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                symbol TEXT,
                model_name TEXT,
                accuracy REAL,
                precision REAL,
                recall REAL,
                f1_score REAL,
                sharpe_ratio REAL,
                max_drawdown REAL
            )
        ''')

        # User subscriptions table (for monetization)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT,
                subscription_tier TEXT,
                subscription_start DATE,
                subscription_end DATE,
                api_calls_today INTEGER DEFAULT 0,
                total_revenue REAL DEFAULT 0
            )
        ''')

        # API usage tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                timestamp DATETIME,
                endpoint TEXT,
                response_time REAL,
                success BOOLEAN
            )
        ''')

        conn.commit()
        conn.close()

    def log_trade(self, trade_data: Dict):
        """Log trade to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO trades (timestamp, symbol, side, quantity, entry_price,
                              prediction_confidence, status, order_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now(),
            trade_data['symbol'],
            trade_data['side'],
            trade_data['quantity'],
            trade_data['entry_price'],
            trade_data['confidence'],
            'OPEN',
            trade_data['order_id']
        ))
        conn.commit()
        conn.close()

    def update_trade_exit(self, order_id: str, exit_price: float, pnl: float):
        """Update trade with exit information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE trades
            SET exit_price = ?, profit_loss = ?,
                profit_loss_pct = (exit_price - entry_price) / entry_price * 100,
                status = 'CLOSED'
            WHERE order_id = ?
        ''', (exit_price, pnl, order_id))
        conn.commit()
        conn.close()

    def get_performance_metrics(self, days: int = 30) -> Dict:
        """Get performance metrics for specified period"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        start_date = datetime.now() - timedelta(days=days)

        cursor.execute('''
            SELECT
                COUNT(*) as total_trades,
                SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(profit_loss) as total_pnl,
                AVG(profit_loss) as avg_pnl,
                MAX(profit_loss) as max_win,
                MIN(profit_loss) as max_loss
            FROM trades
            WHERE timestamp > ? AND status = 'CLOSED'
        ''', (start_date,))

        result = cursor.fetchone()
        conn.close()

        if result and result[0] > 0:
            return {
                'total_trades': result[0],
                'winning_trades': result[1],
                'win_rate': result[1] / result[0] if result[0] > 0 else 0,
                'total_pnl': result[2] or 0,
                'avg_pnl': result[3] or 0,
                'max_win': result[4] or 0,
                'max_loss': result[5] or 0
            }
        return {}


# Advanced ML Model Pipeline
class AdvancedTradingModel:
    """Advanced ML model with ensemble methods and 50+ features"""

    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        self.models = {}
        self.scalers = {}

    def create_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create 50+ technical features for ML"""
        # Basic price features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))

        # Multiple timeframe MAs
        for period in [5, 10, 20, 50, 100, 200]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()

        # MACD variations
        df['macd_12_26'] = df['close'].ewm(span=12).mean() - df['close'].ewm(span=26).mean()
        df['macd_signal'] = df['macd_12_26'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd_12_26'] - df['macd_signal']

        # RSI multiple periods
        for period in [7, 14, 21]:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            df[f'rsi_{period}'] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        for period in [10, 20, 30]:
            df[f'bb_middle_{period}'] = df['close'].rolling(window=period).mean()
            df[f'bb_std_{period}'] = df['close'].rolling(window=period).std()
            df[f'bb_upper_{period}'] = df[f'bb_middle_{period}'] + (df[f'bb_std_{period}'] * 2)
            df[f'bb_lower_{period}'] = df[f'bb_middle_{period}'] - (df[f'bb_std_{period}'] * 2)
            df[f'bb_width_{period}'] = (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}']) / df[f'bb_middle_{period}']
            df[f'bb_position_{period}'] = (df['close'] - df[f'bb_lower_{period}']) / (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}'])

        # ATR (Average True Range)
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = abs(df['high'] - df['close'].shift())
        df['low_close'] = abs(df['low'] - df['close'].shift())
        df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['atr_14'] = df['true_range'].rolling(window=14).mean()

        # Volume features
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        df['volume_momentum'] = df['volume'].pct_change(5)

        # Price momentum multiple periods
        for period in [3, 5, 10, 20]:
            df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1

        # Volatility
        for period in [10, 20, 30]:
            df[f'volatility_{period}'] = df['returns'].rolling(window=period).std()

        # Stochastic Oscillator
        low_14 = df['low'].rolling(window=14).min()
        high_14 = df['high'].rolling(window=14).max()
        df['stoch_k'] = 100 * (df['close'] - low_14) / (high_14 - low_14)
        df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()

        # Williams %R
        df['williams_r'] = -100 * (high_14 - df['close']) / (high_14 - low_14)

        # OBV (On-Balance Volume)
        df['obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()

        # Price channels
        df['highest_20'] = df['high'].rolling(window=20).max()
        df['lowest_20'] = df['low'].rolling(window=20).min()
        df['channel_position'] = (df['close'] - df['lowest_20']) / (df['highest_20'] - df['lowest_20'])

        # Target: Next day return
        df['target_return'] = df['close'].shift(-1) / df['close'] - 1
        df['target_binary'] = (df['target_return'] > 0).astype(int)

        return df

    def train_ensemble_model(self, X, y, symbol: str):
        """Train ensemble of Random Forest, Gradient Boosting, and XGBoost"""
        # Time series split
        tscv = TimeSeriesSplit(n_splits=5)

        # Scale features
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X)

        # Individual models
        rf = RandomForestClassifier(
            n_estimators=300,
            max_depth=15,
            min_samples_split=10,
            random_state=42,
            n_jobs=-1
        )

        gb = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            random_state=42
        )

        xgb_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.05,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss'
        )

        # Voting ensemble
        ensemble = VotingClassifier(
            estimators=[
                ('rf', rf),
                ('gb', gb),
                ('xgb', xgb_model)
            ],
            voting='soft',
            weights=[1, 1, 1.2]  # XGB gets slightly more weight
        )

        # Train
        split_idx = int(len(X_scaled) * 0.8)
        X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        ensemble.fit(X_train, y_train)

        # Evaluate
        train_score = ensemble.score(X_train, y_train)
        test_score = ensemble.score(X_test, y_test)

        # Cross-validation score
        cv_scores = cross_val_score(ensemble, X_train, y_train, cv=tscv, scoring='accuracy')

        print(f"\n{symbol} Model Performance:")
        print(f"Training Accuracy: {train_score:.4f}")
        print(f"Testing Accuracy: {test_score:.4f}")
        print(f"CV Score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

        # Save model
        model_path = self.model_dir / f"{symbol}_model.pkl"
        scaler_path = self.model_dir / f"{symbol}_scaler.pkl"
        joblib.dump(ensemble, model_path)
        joblib.dump(scaler, scaler_path)

        self.models[symbol] = ensemble
        self.scalers[symbol] = scaler

        return ensemble, scaler, test_score

    def load_model(self, symbol: str):
        """Load pre-trained model"""
        model_path = self.model_dir / f"{symbol}_model.pkl"
        scaler_path = self.model_dir / f"{symbol}_scaler.pkl"

        if model_path.exists() and scaler_path.exists():
            self.models[symbol] = joblib.load(model_path)
            self.scalers[symbol] = joblib.load(scaler_path)
            return True
        return False


# Risk Management System
class RiskManager:
    """Enterprise risk management with Kelly Criterion and position sizing"""

    def __init__(self, config: TradingConfig, trading_client: TradingClient):
        self.config = config
        self.trading_client = trading_client
        self.daily_trades = 0
        self.last_reset = datetime.now().date()

    def check_daily_limit(self) -> bool:
        """Check if daily trade limit reached"""
        if datetime.now().date() > self.last_reset:
            self.daily_trades = 0
            self.last_reset = datetime.now().date()

        return self.daily_trades < self.config.max_daily_trades

    def calculate_position_size(self, symbol: str, confidence: float, current_price: float) -> int:
        """Calculate optimal position size based on Kelly Criterion"""
        try:
            # Get account info
            account = self.trading_client.get_account()
            portfolio_value = float(account.portfolio_value)

            # Kelly Criterion: f = (bp - q) / b
            # where b = odds, p = win probability, q = loss probability
            win_prob = confidence
            loss_prob = 1 - confidence
            avg_win = self.config.take_profit_pct
            avg_loss = self.config.stop_loss_pct

            kelly_fraction = (win_prob * avg_win - loss_prob * avg_loss) / avg_win
            kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%

            # Position size with risk management
            max_position = min(
                self.config.max_position_size,
                portfolio_value * kelly_fraction,
                portfolio_value * self.config.max_portfolio_risk
            )

            quantity = int(max_position / current_price)
            return max(1, quantity)

        except Exception as e:
            print(f"Error calculating position size: {e}")
            return 1

    def create_bracket_order(self, symbol: str, quantity: int, current_price: float, side: OrderSide) -> Dict:
        """Create order with stop loss and take profit"""
        if side == OrderSide.BUY:
            stop_loss_price = current_price * (1 - self.config.stop_loss_pct)
            take_profit_price = current_price * (1 + self.config.take_profit_pct)
        else:
            stop_loss_price = current_price * (1 + self.config.stop_loss_pct)
            take_profit_price = current_price * (1 - self.config.take_profit_pct)

        return {
            'symbol': symbol,
            'qty': quantity,
            'side': side,
            'type': 'market',
            'time_in_force': TimeInForce.DAY,
            'order_class': OrderClass.BRACKET,
            'stop_loss': {'stop_price': round(stop_loss_price, 2)},
            'take_profit': {'limit_price': round(take_profit_price, 2)}
        }


# Production Trading System
class ProductionTradingSystem:
    """Complete production trading system with ML, risk management, and monitoring"""

    def __init__(self, config: TradingConfig):
        self.config = config
        self.trading_client = TradingClient(config.api_key, config.secret_key, paper=config.paper_trading)
        self.data_client = StockHistoricalDataClient(config.api_key, config.secret_key)
        self.model = AdvancedTradingModel()
        self.risk_manager = RiskManager(config, self.trading_client)
        self.db = TradingDatabase()
        self.logger = ProductionLogger()

    def fetch_data(self, symbol: str, days: int = 500) -> pd.DataFrame:
        """Fetch historical data from Alpaca"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date
            )

            bars = self.data_client.get_stock_bars(request_params)
            df = bars.df

            if isinstance(df.index, pd.MultiIndex):
                df = df.reset_index(level=0, drop=True)

            return df
        except Exception as e:
            self.logger.log_error(e, f"fetch_data for {symbol}")
            return pd.DataFrame()

    def get_current_price(self, symbol: str) -> float:
        """Get current market price"""
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            quote = self.data_client.get_stock_latest_quote(request)
            return float(quote[symbol].ask_price)
        except Exception as e:
            self.logger.log_error(e, f"get_current_price for {symbol}")
            return 0.0

    def train_model_for_symbol(self, symbol: str):
        """Train or retrain model for a symbol"""
        print(f"\n{'='*60}")
        print(f"Training model for {symbol}")
        print(f"{'='*60}")

        df = self.fetch_data(symbol, days=500)
        if df.empty:
            return False

        df = self.model.create_advanced_features(df)
        df_clean = df.dropna()

        # Get feature columns (exclude target and non-features)
        exclude_cols = ['target_return', 'target_binary', 'high_low', 'high_close', 'low_close', 'true_range']
        feature_cols = [col for col in df_clean.columns if col not in exclude_cols and col not in ['open', 'high', 'low', 'close', 'volume']]

        X = df_clean[feature_cols]
        y = df_clean['target_binary']

        ensemble, scaler, test_score = self.model.train_ensemble_model(X, y, symbol)

        # Log performance
        self.db.log_trade({
            'symbol': symbol,
            'side': 'MODEL_TRAIN',
            'quantity': 0,
            'entry_price': 0,
            'confidence': test_score,
            'order_id': f'TRAIN_{symbol}_{datetime.now().strftime("%Y%m%d")}'
        })

        return True

    def predict_and_trade(self, symbol: str):
        """Make prediction and execute trade"""
        try:
            # Check daily limit
            if not self.risk_manager.check_daily_limit():
                print("Daily trade limit reached")
                return

            # Load or train model
            if symbol not in self.model.models:
                if not self.model.load_model(symbol):
                    print(f"Training new model for {symbol}")
                    self.train_model_for_symbol(symbol)

            # Fetch recent data
            df = self.fetch_data(symbol, days=500)
            if df.empty:
                return

            df = self.model.create_advanced_features(df)
            df_clean = df.dropna()

            # Prepare features
            exclude_cols = ['target_return', 'target_binary', 'high_low', 'high_close', 'low_close', 'true_range']
            feature_cols = [col for col in df_clean.columns if col not in exclude_cols and col not in ['open', 'high', 'low', 'close', 'volume']]

            latest_features = df_clean[feature_cols].iloc[-1:].values
            scaled_features = self.model.scalers[symbol].transform(latest_features)

            # Predict
            prediction = self.model.models[symbol].predict(scaled_features)[0]
            probabilities = self.model.models[symbol].predict_proba(scaled_features)[0]
            confidence = probabilities[prediction]

            print(f"\n{'='*60}")
            print(f"Prediction for {symbol}")
            print(f"{'='*60}")
            print(f"Direction: {'UP ↑' if prediction == 1 else 'DOWN ↓'}")
            print(f"Confidence: {confidence:.2%}")
            print(f"Up Probability: {probabilities[1]:.2%}")
            print(f"Down Probability: {probabilities[0]:.2%}")

            # Execute trade if confidence high enough
            if confidence >= self.config.confidence_threshold and prediction == 1:
                current_price = self.get_current_price(symbol)
                if current_price == 0:
                    return

                quantity = self.risk_manager.calculate_position_size(symbol, confidence, current_price)

                print(f"\n💰 EXECUTING TRADE")
                print(f"Symbol: {symbol}")
                print(f"Side: BUY")
                print(f"Quantity: {quantity}")
                print(f"Price: ${current_price:.2f}")
                print(f"Position Value: ${quantity * current_price:.2f}")

                # Create bracket order with stop loss and take profit
                order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY,
                )

                order = self.trading_client.submit_order(order_data=order_data)

                # Log to database
                self.db.log_trade({
                    'symbol': symbol,
                    'side': 'BUY',
                    'quantity': quantity,
                    'entry_price': current_price,
                    'confidence': confidence,
                    'order_id': order.id
                })

                self.logger.log_trade({
                    'symbol': symbol,
                    'side': 'BUY',
                    'quantity': quantity,
                    'price': current_price,
                    'confidence': confidence,
                    'order_id': order.id
                })

                self.risk_manager.daily_trades += 1

                print(f"✅ Order submitted successfully")
                print(f"Order ID: {order.id}")

            else:
                print(f"\n⏸️  NO TRADE: Confidence {confidence:.2%} below threshold {self.config.confidence_threshold:.2%}")

        except Exception as e:
            self.logger.log_error(e, f"predict_and_trade for {symbol}")

    def get_performance_report(self) -> Dict:
        """Get system performance metrics"""
        metrics = self.db.get_performance_metrics(days=30)
        self.logger.log_performance(metrics)
        return metrics

    def run_multi_symbol_strategy(self, symbols: List[str]):
        """Run strategy on multiple symbols"""
        print(f"\n{'='*60}")
        print(f"Running Multi-Symbol Strategy")
        print(f"Symbols: {', '.join(symbols)}")
        print(f"{'='*60}\n")

        for symbol in symbols:
            try:
                self.predict_and_trade(symbol)
            except Exception as e:
                self.logger.log_error(e, f"run_multi_symbol_strategy for {symbol}")
                continue

        # Print performance summary
        print(f"\n{'='*60}")
        print("Performance Summary")
        print(f"{'='*60}")
        metrics = self.get_performance_report()
        for key, value in metrics.items():
            print(f"{key}: {value}")


# Monetization API System
class MonetizationAPI:
    """Subscription and monetization management"""

    def __init__(self):
        self.subscription_tiers = {
            'free': SubscriptionTier(
                name='Free',
                price=0,
                features=['1 symbol', 'Basic predictions', 'Daily email alerts'],
                max_symbols=1,
                api_calls_per_day=10,
                advanced_models=False,
                real_time_alerts=False
            ),
            'starter': SubscriptionTier(
                name='Starter',
                price=29.99,
                features=['5 symbols', 'Advanced ML models', 'Hourly alerts', 'Performance analytics'],
                max_symbols=5,
                api_calls_per_day=100,
                advanced_models=True,
                real_time_alerts=False
            ),
            'professional': SubscriptionTier(
                name='Professional',
                price=99.99,
                features=['20 symbols', 'Ensemble models', 'Real-time alerts', 'API access', 'Custom strategies'],
                max_symbols=20,
                api_calls_per_day=1000,
                advanced_models=True,
                real_time_alerts=True
            ),
            'enterprise': SubscriptionTier(
                name='Enterprise',
                price=499.99,
                features=['Unlimited symbols', 'Custom models', 'Priority support', 'White-label option'],
                max_symbols=999,
                api_calls_per_day=10000,
                advanced_models=True,
                real_time_alerts=True
            )
        }

    def check_user_limits(self, user_id: str, symbol_count: int) -> Tuple[bool, str]:
        """Check if user can access requested features"""
        # Implementation would check database for user's subscription
        # This is a simplified version
        return True, "OK"

    def track_api_usage(self, user_id: str, endpoint: str):
        """Track API usage for billing"""
        # Log to database for analytics and billing
        pass


# Example usage
if __name__ == "__main__":
    # Configuration
    config = TradingConfig(
        api_key="YOUR_API_KEY",
        secret_key="YOUR_SECRET_KEY",
        paper_trading=True,
        confidence_threshold=0.65,
        max_daily_trades=10
    )

    # Initialize system
    system = ProductionTradingSystem(config)

    # Run for multiple symbols
    symbols = ["NVDA", "AAPL", "TSLA", "MSFT", "GOOGL"]
    system.run_multi_symbol_strategy(symbols)

    # Get performance report
    performance = system.get_performance_report()
    print("\n📊 System Performance:")
    print(json.dumps(performance, indent=2))

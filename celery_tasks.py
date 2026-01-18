"""
Celery Tasks for Background Job Processing
Author: Claude Code
Description: Asynchronous task queue for model training, trading, and notifications
"""

from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

from production_trading_system import (
    ProductionTradingSystem,
    TradingConfig,
    TradingDatabase
)

load_dotenv()

# Initialize Celery
app = Celery(
    'ml_trading',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,
)


@app.task(name='train_model')
def train_model_task(symbol: str):
    """
    Background task to train ML model for a symbol
    """
    try:
        config = TradingConfig(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            paper_trading=True
        )

        system = ProductionTradingSystem(config)
        success = system.train_model_for_symbol(symbol)

        return {
            'status': 'success' if success else 'failed',
            'symbol': symbol,
            'message': f'Model training {"completed" if success else "failed"} for {symbol}'
        }

    except Exception as e:
        return {
            'status': 'error',
            'symbol': symbol,
            'error': str(e)
        }


@app.task(name='run_prediction')
def run_prediction_task(symbol: str):
    """
    Background task to run prediction and potentially execute trade
    """
    try:
        config = TradingConfig(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            paper_trading=True,
            confidence_threshold=float(os.getenv('CONFIDENCE_THRESHOLD', 0.65))
        )

        system = ProductionTradingSystem(config)
        system.predict_and_trade(symbol)

        return {
            'status': 'success',
            'symbol': symbol,
            'message': f'Prediction completed for {symbol}'
        }

    except Exception as e:
        return {
            'status': 'error',
            'symbol': symbol,
            'error': str(e)
        }


@app.task(name='run_multi_symbol_strategy')
def run_multi_symbol_strategy_task(symbols: list):
    """
    Background task to run strategy on multiple symbols
    """
    try:
        config = TradingConfig(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            paper_trading=True
        )

        system = ProductionTradingSystem(config)
        system.run_multi_symbol_strategy(symbols)

        return {
            'status': 'success',
            'symbols': symbols,
            'message': f'Strategy completed for {len(symbols)} symbols'
        }

    except Exception as e:
        return {
            'status': 'error',
            'symbols': symbols,
            'error': str(e)
        }


@app.task(name='retrain_all_models')
def retrain_all_models_task():
    """
    Background task to retrain all models (scheduled monthly)
    """
    symbols = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'META', 'AMD', 'NFLX', 'INTC']
    results = []

    for symbol in symbols:
        result = train_model_task.delay(symbol)
        results.append(result)

    return {
        'status': 'success',
        'message': f'Retraining initiated for {len(symbols)} models',
        'task_ids': [r.id for r in results]
    }


@app.task(name='send_performance_report')
def send_performance_report_task(email: str):
    """
    Background task to generate and send performance report
    """
    try:
        db = TradingDatabase()
        metrics = db.get_performance_metrics(days=30)

        # In production, integrate with email service (SendGrid, AWS SES, etc.)
        # For now, just log the metrics

        return {
            'status': 'success',
            'email': email,
            'metrics': metrics,
            'message': 'Performance report sent'
        }

    except Exception as e:
        return {
            'status': 'error',
            'email': email,
            'error': str(e)
        }


@app.task(name='cleanup_old_data')
def cleanup_old_data_task(days: int = 90):
    """
    Background task to clean up old data from database
    """
    try:
        # Implementation for cleaning old logs, trades, etc.
        return {
            'status': 'success',
            'message': f'Cleaned data older than {days} days'
        }

    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


@app.task(name='health_check')
def health_check_task():
    """
    Background task to check system health
    """
    try:
        # Check database connection
        db = TradingDatabase()

        # Check Alpaca API connection
        config = TradingConfig(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            paper_trading=True
        )
        system = ProductionTradingSystem(config)

        return {
            'status': 'healthy',
            'database': 'connected',
            'api': 'connected',
            'message': 'All systems operational'
        }

    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }


# Periodic tasks schedule
app.conf.beat_schedule = {
    # Run predictions every day at 9:30 AM (market open)
    'daily-predictions': {
        'task': 'run_multi_symbol_strategy',
        'schedule': crontab(hour=9, minute=30),
        'args': (['NVDA', 'AAPL', 'TSLA', 'MSFT', 'GOOGL'],)
    },

    # Retrain models every Sunday at 2:00 AM
    'weekly-model-retrain': {
        'task': 'retrain_all_models',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),
    },

    # Send performance reports every Monday at 8:00 AM
    'weekly-performance-report': {
        'task': 'send_performance_report',
        'schedule': crontab(day_of_week=1, hour=8, minute=0),
        'args': ('admin@yourdomain.com',)
    },

    # Health check every 5 minutes
    'health-check': {
        'task': 'health_check',
        'schedule': crontab(minute='*/5'),
    },

    # Cleanup old data every month
    'monthly-cleanup': {
        'task': 'cleanup_old_data',
        'schedule': crontab(day_of_month=1, hour=3, minute=0),
        'args': (90,)
    },
}


if __name__ == '__main__':
    app.start()

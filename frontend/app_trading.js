// Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// State
let currentStock = null;
let priceChart = null;
let volumeChart = null;
let currentPeriod = '3mo';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    updateClock();
    setInterval(updateClock, 1000);
});

function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour12: false });
    const dateStr = now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    document.getElementById('currentTime').textContent = `${dateStr} ${timeStr}`;
}

function initializeEventListeners() {
    // Stock buttons
    document.querySelectorAll('.stock-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const symbol = btn.dataset.symbol;
            analyzeStock(symbol);
        });
    });

    // Custom symbol
    document.getElementById('analyzeBtn').addEventListener('click', () => {
        const symbol = document.getElementById('customSymbol').value.toUpperCase();
        if (symbol) analyzeStock(symbol);
    });

    document.getElementById('customSymbol').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const symbol = document.getElementById('customSymbol').value.toUpperCase();
            if (symbol) analyzeStock(symbol);
        }
    });

    // Back button
    document.getElementById('backBtn').addEventListener('click', () => {
        document.getElementById('dashboard').style.display = 'none';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // Timeframe buttons
    document.querySelectorAll('.tf-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentPeriod = btn.dataset.period;
            if (currentStock) {
                analyzeStock(currentStock, currentPeriod);
            }
        });
    });
}

async function analyzeStock(symbol, period = '3mo') {
    currentStock = symbol;
    currentPeriod = period;

    // Show dashboard and loading
    document.getElementById('dashboard').style.display = 'block';
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';

    // Scroll to dashboard
    document.getElementById('dashboard').scrollIntoView({ behavior: 'smooth' });

    try {
        const response = await axios.post(`${API_BASE_URL}/predict`, {
            symbol: symbol
        });

        const data = response.data;
        displayResults(data);

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loading').innerHTML = `
            <div style="color: #ef5350; padding: 40px;">
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 20px;"></i>
                <p>Failed to fetch data for ${symbol}</p>
                <p style="font-size: 14px; margin-top: 10px;">Make sure the API server is running: python real_data_api.py</p>
                <button class="btn btn-primary" onclick="location.reload()" style="margin-top: 20px;">
                    Try Again
                </button>
            </div>
        `;
    }
}

function displayResults(data) {
    // Hide loading, show results
    document.getElementById('loading').style.display = 'none';
    document.getElementById('results').style.display = 'block';

    // Update stock header
    document.getElementById('stockSymbol').textContent = data.symbol;
    document.getElementById('stockName').textContent = data.symbol + ' Stock';
    document.getElementById('stockPrice').textContent = data.current_price.toFixed(2);

    // Price change
    const change = data.change_24h || 0;
    const changeEl = document.getElementById('priceChange');
    changeEl.innerHTML = `
        <span class="change-value">${change >= 0 ? '+' : ''}${change.toFixed(2)}</span>
        <span class="change-percent">(${change >= 0 ? '+' : ''}${change.toFixed(2)}%)</span>
    `;
    changeEl.className = 'price-change ' + (change >= 0 ? 'positive' : 'negative');

    // Prediction badge
    const predBadge = document.getElementById('predictionBadge');
    const isBuy = data.prediction === 'BUY';
    predBadge.className = 'prediction-badge ' + (isBuy ? 'buy' : 'sell');
    predBadge.innerHTML = `
        <i class="fas fa-arrow-${isBuy ? 'up' : 'down'}"></i>
        <span>${data.prediction}</span>
        <div class="confidence">${(data.confidence * 100).toFixed(0)}%</div>
    `;

    // Prediction details
    const predDir = document.getElementById('predDirection');
    predDir.className = 'pred-direction ' + (isBuy ? 'buy' : 'sell');
    predDir.innerHTML = `
        <i class="fas fa-arrow-${isBuy ? 'up' : 'down'}"></i>
        <span>${data.prediction}</span>
    `;

    document.getElementById('confValue').textContent = `${(data.confidence * 100).toFixed(0)}%`;
    document.getElementById('confFill').style.width = `${data.confidence * 100}%`;

    document.getElementById('upProb').textContent = `${(data.up_probability * 100).toFixed(1)}%`;
    document.getElementById('downProb').textContent = `${(data.down_probability * 100).toFixed(1)}%`;

    // Indicators
    document.getElementById('rsiValue').textContent = data.indicators.rsi ? data.indicators.rsi.toFixed(2) : '--';
    document.getElementById('macdValue').textContent = data.indicators.macd ? data.indicators.macd.toFixed(2) : '--';
    document.getElementById('smaValue').textContent = data.indicators.sma_20 ? '$' + data.indicators.sma_20.toFixed(2) : '--';
    document.getElementById('volumeValue').textContent = data.indicators.volume || '--';

    // Last update
    document.getElementById('lastUpdate').textContent = 'Just now';

    // Create charts
    createCharts(data.historical_data, data.symbol);
}

function createCharts(historicalData, symbol) {
    // Clear existing charts
    document.getElementById('tradingViewChart').innerHTML = '';
    document.getElementById('volumeChart').innerHTML = '';

    if (!historicalData || historicalData.length === 0) {
        console.error('No historical data available');
        return;
    }

    // Prepare data for candlestick chart
    const candleData = historicalData.map(d => ({
        time: d.date,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close
    }));

    const volumeData = historicalData.map(d => ({
        time: d.date,
        value: d.volume,
        color: d.close >= d.open ? '#26a69a80' : '#ef535080'
    }));

    // Create price chart
    priceChart = LightweightCharts.createChart(document.getElementById('tradingViewChart'), {
        width: document.getElementById('tradingViewChart').offsetWidth,
        height: 450,
        layout: {
            background: { color: '#1e222d' },
            textColor: '#d1d4dc',
        },
        grid: {
            vertLines: { color: '#2a2e39' },
            horzLines: { color: '#2a2e39' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        rightPriceScale: {
            borderColor: '#2a2e39',
        },
        timeScale: {
            borderColor: '#2a2e39',
            timeVisible: true,
        },
    });

    const candleSeries = priceChart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
    });

    candleSeries.setData(candleData);

    // Create volume chart
    volumeChart = LightweightCharts.createChart(document.getElementById('volumeChart'), {
        width: document.getElementById('volumeChart').offsetWidth,
        height: 120,
        layout: {
            background: { color: '#1e222d' },
            textColor: '#d1d4dc',
        },
        grid: {
            vertLines: { color: '#2a2e39' },
            horzLines: { color: '#2a2e39' },
        },
        rightPriceScale: {
            borderColor: '#2a2e39',
        },
        timeScale: {
            borderColor: '#2a2e39',
            timeVisible: false,
        },
    });

    const volumeSeries = volumeChart.addHistogramSeries({
        color: '#26a69a',
        priceFormat: {
            type: 'volume',
        },
        priceScaleId: '',
    });

    volumeSeries.setData(volumeData);

    // Sync time scales
    priceChart.timeScale().subscribeVisibleTimeRangeChange(() => {
        const timeRange = priceChart.timeScale().getVisibleRange();
        volumeChart.timeScale().setVisibleRange(timeRange);
    });

    volumeChart.timeScale().subscribeVisibleTimeRangeChange(() => {
        const timeRange = volumeChart.timeScale().getVisibleRange();
        priceChart.timeScale().setVisibleRange(timeRange);
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        if (priceChart) {
            priceChart.resize(document.getElementById('tradingViewChart').offsetWidth, 450);
        }
        if (volumeChart) {
            volumeChart.resize(document.getElementById('volumeChart').offsetWidth, 120);
        }
    });
}
